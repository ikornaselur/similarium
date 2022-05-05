from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.sql.schema import Index

from semantle_slack_bot.config import config
from semantle_slack_bot.db import Base
from semantle_slack_bot.exceptions import InvalidWord, NotFound
from semantle_slack_bot.logging import logger
from semantle_slack_bot.utils import (
    get_puzzle_date,
    get_secret,
    get_similarity,
    timestamp_ms,
)

if TYPE_CHECKING:
    from semantle_slack_bot.models import Guess


class Game(Base):
    __tablename__ = "game"

    id = sa.Column(sa.Integer, primary_key=True)
    channel_id = sa.Column(sa.Text, nullable=False)
    thread_ts = sa.Column(sa.Text, nullable=False)
    puzzle_number = sa.Column(sa.Integer, nullable=False)
    date = sa.Column(sa.Text, nullable=False)
    active = sa.Column(sa.Boolean, nullable=False)
    secret = sa.Column(sa.Text, nullable=False)
    guesses = relationship("Guess", backref="game", lazy="joined")

    __table_args__ = (Index("channel_thread_idx", channel_id, thread_ts),)

    @classmethod
    def new(
        cls,
        *,
        channel_id: str,
        thread_ts: str,
        puzzle_number: int,
        active: bool = True,
    ) -> Game:
        secret = get_secret(channel_id, puzzle_number)
        logger.debug(
            f"Creating new Game: {channel_id=} {thread_ts=} {puzzle_number=} {secret=}"
        )
        return cls(
            channel_id=channel_id,
            thread_ts=thread_ts,
            puzzle_number=puzzle_number,
            date=get_puzzle_date(puzzle_number),
            active=active,
            secret=secret,
        )

    @classmethod
    async def get(
        cls,
        *,
        channel_id: str,
        thread_ts: str,
        puzzle_number: int,
        session: AsyncSession,
    ) -> Optional[Game]:
        logger.debug(
            f"Getting or creating Game: {channel_id=} {thread_ts=} {puzzle_number=}"
        )
        stmt = (
            select(cls)
            .where(
                cls.channel_id == channel_id,
                cls.thread_ts == thread_ts,
                cls.puzzle_number == puzzle_number,
            )
            .options(selectinload(cls.guesses))
        )

        result = await session.execute(stmt)

        return result.scalars().one_or_none()

    @classmethod
    async def by_id(cls, game_id: int, /, *, session: AsyncSession) -> Optional[Game]:
        result = await session.execute(
            select(cls).where(cls.id == game_id).options(selectinload(cls.guesses))
        )
        return result.scalars().one_or_none()

    async def add_guess(
        self, *, word: str, user_id: str, session: AsyncSession
    ) -> Guess:
        """Add a guess to the game"""
        from .guess import Guess
        from .nearby import Nearby
        from .word2vec import Word2Vec

        logger.debug(f"Adding guess {word=} to {self=}")

        if word == self.secret:
            logger.info(f"Secret word has been found: {word=}")
            self.active = False

        # Check if guess exists
        guess = await Guess.get(session=session, word=word, game_id=self.id)
        if guess is not None:
            logger.debug(f"Guess has already been made {guess=}")
            guess.updated = timestamp_ms()  # type: ignore
            return guess

        try:
            nearby = await Nearby.get(session=session, word=self.secret, neighbor=word)
        except NotFound:
            guess_vec = await Word2Vec.get(session=session, word=word)
            if guess_vec is None:
                logger.debug(f"Word not recognised: {word=}")
                raise InvalidWord(f"Word not recognised: {word}")

            logger.debug(f"Guess was not within {config.rules.similarity_count}")
            secret_vec = await Word2Vec.get(session=session, word=self.secret)
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
            session=session,
            game=self,
            user_id=user_id,
            word=word,
            percentile=percentile,
            similarity=similarity,
        )
        session.add(guess)
        await session.refresh(self)

        return guess

    async def top_guesses(self, n: int, /, *, session: AsyncSession) -> list[Guess]:
        from .guess import Guess

        stmt = (
            select(Guess)
            .where(Guess.game_id == self.id)
            .order_by(Guess.similarity.desc())
            .limit(n)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def latest_guesses(self, n: int, /, *, session: AsyncSession) -> list[Guess]:
        from .guess import Guess

        stmt = (
            select(Guess)
            .where(Guess.game_id == self.id)
            .order_by(Guess.updated.desc())
            .limit(n)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    def __repr__(self) -> str:
        return (
            f"<Game (id={self.id} puzzle_number={self.puzzle_number} "
            f"channel_id={self.channel_id} secret={self.secret})>"
        )
