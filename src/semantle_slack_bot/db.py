from __future__ import annotations

import datetime as dt
import struct
from functools import lru_cache
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.schema import Index

from semantle_slack_bot.logging import logger
from semantle_slack_bot.utils import get_secret, get_similarity

Base = declarative_base()

engine = create_async_engine("sqlite+aiosqlite:///word2vec.db", future=True)
session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

BASE_DATE = dt.datetime(2022, 4, 23, tzinfo=dt.timezone.utc)


class RowNotFound(Exception):
    pass


class InvalidWord(Exception):
    pass


def _expand_bfloat(vec: bytes, half_length: int = 600) -> bytes:
    """
    expand truncated float32 to float32
    """
    if len(vec) == half_length:
        vec = b"".join((b"\00\00" + bytes(pair)) for pair in zip(vec[::2], vec[1::2]))
    return vec


def _get_guess_created_time(day: int) -> int:
    """Get a "created" time for a guess, based on a day

    The created time is the time in milliseconds that have passed since the day
    before `day`.

    `day` is the number of days that have passed since the BASE_DATE, which is
    when the bot was launched.

    This created time is used just for ordering of guesses, and time elapsed
    since yesterday UTC is used so that time zones don't matter (in theory?).
    """
    date = BASE_DATE + dt.timedelta(days=day - 1)
    now = dt.datetime.now(dt.timezone.utc)
    delta = now - date

    return int(delta.total_seconds() * 1000)  # Milliseconds


class Game(Base):
    __tablename__ = "game"

    id = sa.Column(sa.Integer, primary_key=True)
    channel_id = sa.Column(sa.Text)
    thread_ts = sa.Column(sa.Text)
    day = sa.Column(sa.Integer)
    active = sa.Column(sa.Boolean)
    secret = sa.Column(sa.Text)
    guesses = relationship("Guess")

    __table_args__ = (Index("channel_thread_idx", channel_id, thread_ts),)

    @classmethod
    async def new(
        cls, *, channel_id: str, thread_ts: str, day: int, active: bool = True
    ) -> Game:
        secret = get_secret(channel_id, day)
        logger.debug(f"Creating new Game: {channel_id=} {thread_ts=} {day=} {secret=}")
        game = cls(
            channel_id=channel_id,
            thread_ts=thread_ts,
            day=day,
            active=active,
            secret=secret,
        )

        async with session() as s:
            async with s.begin():
                s.add(game)

        return game

    @classmethod
    async def get_or_create(cls, *, channel_id: str, thread_ts: str, day: int) -> Game:
        logger.debug(f"Getting or creating Game: {channel_id=} {thread_ts=} {day=}")
        async with session() as s:
            stmt = select(cls).where(
                cls.channel_id == channel_id,
                cls.thread_ts == thread_ts,
                cls.day == day,
            )

            result = await s.execute(stmt)

        game: Optional[Game] = result.scalars().one_or_none()
        if game is not None:
            return game

        return await cls.new(channel_id=channel_id, thread_ts=thread_ts, day=day)

    async def add_guess(self, *, word: str, user_id: str) -> Guess:
        """Add a guess to the game"""
        logger.debug(f"Adding guess {word=} to {self=}")

        # Check if guess exists
        guess = await Guess.get(word=word, game_id=self.id)
        if guess is not None:
            logger.debug(f"Guess has already been made {guess=}")
            return guess

        try:
            nearby = await Nearby.get(word=self.secret, neighbor=word)
        except RowNotFound:
            guess_vec = await Word2Vec.get(word)
            if guess_vec is None:
                logger.debug(f"Word not recognised: {word=}")
                raise InvalidWord(f"Word not recognised: {word}")

            logger.debug("Guess was not within 1000")
            secret_vec = await Word2Vec.get(self.secret)
            if secret_vec is None:
                raise Exception("Secret word not recognised?")

            similarity = get_similarity(secret_vec.expanded_vec, guess_vec.expanded_vec)
            percentile = 0
        else:
            similarity = get_similarity(
                nearby.word_vec.expanded_vec, nearby.neighbor_vec.expanded_vec
            )
            percentile = nearby.percentile

        # Create a new guess
        guess = await Guess.new(
            game=self,
            user_id=user_id,
            word=word,
            percentile=percentile,
            similarity=similarity,
        )

        return guess

    async def top_guesses(self, n: int) -> list[Guess]:
        async with session() as s:
            stmt = (
                select(Guess)
                .where(Guess.game_id == self.id)
                .order_by(Guess.similarity.desc())
                .limit(n)
            )
            result = await s.execute(stmt)
            return result.scalars().all()

    async def latest_guesses(self, n: int) -> list[Guess]:
        async with session() as s:
            stmt = (
                select(Guess)
                .where(Guess.game_id == self.id)
                .order_by(Guess.created.desc())
                .limit(n)
            )
            result = await s.execute(stmt)
            return result.scalars().all()

    def __repr__(self) -> str:
        return f"<Game (id: {self.id}, Day: {self.day})>"


class Guess(Base):
    __tablename__ = "guess"

    id = sa.Column(sa.Integer, primary_key=True)
    game_id = sa.Column(sa.Integer, sa.ForeignKey("game.id"))

    # Milliseconds since start of previous day UTC, only used for ordering
    # guesses in a game. Previous day is used to deal with time zones
    created = sa.Column(sa.Integer)

    user_id = sa.Column(sa.Text)
    word = sa.Column(sa.Text)
    percentile = sa.Column(sa.Integer)
    similarity = sa.Column(sa.Float)
    idx = sa.Column(sa.Integer)

    @classmethod
    async def new(
        cls,
        *,
        game: Game,
        user_id: str,
        word: str,
        percentile: int,
        similarity: float,
    ) -> Guess:
        logger.debug(
            f"Creating new Guess: {game=} {user_id=} "
            f"{word=} {percentile=} {similarity=}"
        )

        async with session() as s:
            async with s.begin():
                stmt = select(sa.func.count(word)).where(cls.game_id == game.id)
                result = await s.execute(stmt)
                count = result.scalars().one()

                guess = cls(
                    game_id=game.id,
                    created=_get_guess_created_time(day=game.day),
                    user_id=user_id,
                    word=word,
                    percentile=percentile,
                    similarity=similarity,
                    idx=count + 1,
                )
                s.add(guess)

        return guess

    @classmethod
    async def get(cls, *, word: str, game_id: int) -> Optional[Guess]:
        logger.debug(f"Getting guess {word=} {game_id=}")
        async with session() as s:
            stmt = select(cls).where(
                cls.word == word,
                cls.game_id == game_id,
            )

            result = await s.execute(stmt)

        return result.scalars().one_or_none()

    def __repr__(self) -> str:
        if self.percentile:
            return f"<Guess ({self.word}: {self.percentile}/1000)>"
        return f"<Guess ({self.word}: cold)>"


class Nearby(Base):
    __tablename__ = "nearby"

    word = sa.Column(sa.Text, sa.ForeignKey("word2vec.word"))
    neighbor = sa.Column(sa.Text, sa.ForeignKey("word2vec.word"))
    similarity = sa.Column(sa.Float)
    percentile = sa.Column(sa.Integer)

    word_vec = relationship("Word2Vec", foreign_keys=[word])
    neighbor_vec = relationship("Word2Vec", foreign_keys=[neighbor])

    __table_args__ = (sa.PrimaryKeyConstraint(word, neighbor),)

    @classmethod
    @lru_cache(maxsize=50_000)
    async def get(cls, word: str, neighbor: str) -> Nearby:
        """Get Nearby by word and neighbor"""
        async with session() as s:
            stmt = (
                select(cls)
                .where(cls.word == word, cls.neighbor == neighbor)
                .options(
                    selectinload(cls.word_vec),
                    selectinload(cls.neighbor_vec),
                )
            )
            result = await s.execute(stmt)
            nearby = result.scalars().one_or_none()

        if nearby is None:
            raise RowNotFound(f"Nearby not found for {neighbor=} {word=}")

        return nearby

    def __repr__(self) -> str:
        return (
            f"<Nearby ({self.word} -> {self.neighbor}: "
            f"{self.similarity:.02f} {self.percentile})>"
        )


class SimilarityRange(Base):
    __tablename__ = "similarity_range"

    word = sa.Column(sa.Text, primary_key=True)
    top = sa.Column(sa.Float)
    top10 = sa.Column(sa.Float)
    rest = sa.Column(sa.Float)

    def __repr__(self) -> str:
        return (
            f"<SimilarityRange ({self.word}: {self.top:0.2f} "
            f"{self.top10:0.2f} {self.rest:0.2})>"
        )


class Word2Vec(Base):
    __tablename__ = "word2vec"

    word = sa.Column(sa.Text, primary_key=True)
    vec = sa.Column(sa.BLOB)

    @property
    def expanded_vec(self) -> list[float]:
        return list(struct.unpack("300f", _expand_bfloat(self.vec)))

    @classmethod
    async def get(cls, word: str) -> Optional[Word2Vec]:
        async with session() as s:
            stmt = select(cls).where(cls.word == word)
            result = await s.execute(stmt)
            return result.scalars().one_or_none()

    def __repr__(self) -> str:
        return f"<Word2Vec ({self.word})>"
