from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.sql.schema import Index

from similarium.config import config
from similarium.db import Base
from similarium.exceptions import InvalidWord, NotFound, UserAlreadyWon
from similarium.logging import logger
from similarium.models.game_user_winner_association import GameUserWinnerAssociation
from similarium.utils import get_secret, get_similarity, timestamp_ms

if TYPE_CHECKING:
    from similarium.models import Guess


class Game(Base):
    __tablename__ = "game"

    id = sa.Column(sa.Integer, primary_key=True)
    channel_id = sa.Column(sa.Text, sa.ForeignKey("channel.id"), nullable=False)
    thread_ts = sa.Column(sa.Text, nullable=False)
    puzzle_number = sa.Column(sa.Integer, nullable=False)
    date = sa.Column(sa.Text, nullable=False)
    active = sa.Column(sa.Boolean, nullable=False)
    secret = sa.Column(sa.Text, nullable=False)

    channel = relationship("Channel", backref="games", lazy="joined")
    guesses = relationship("Guess", back_populates="game", lazy="joined")
    winners = relationship(
        "GameUserWinnerAssociation", order_by="GameUserWinnerAssociation.guess_idx"
    )

    similarity_range = relationship(
        "SimilarityRange", primaryjoin="foreign(Game.secret) == SimilarityRange.word"
    )

    __table_args__ = (Index("channel_thread_idx", channel_id, thread_ts),)

    @classmethod
    def new(
        cls,
        *,
        channel_id: str,
        thread_ts: str,
        puzzle_number: int,
        puzzle_date: str,
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
            date=puzzle_date,
            active=active,
            secret=secret,
        )

    @classmethod
    async def get(
        cls,
        *,
        channel_id: str,
        thread_ts: str,
        session: AsyncSession,
    ) -> Optional[Game]:
        logger.debug(f"Getting Game: {channel_id=} {thread_ts=}")
        stmt = (
            select(cls)
            .where(
                cls.channel_id == channel_id,
                cls.thread_ts == thread_ts,
            )
            .options(selectinload(cls.guesses))
            .options(selectinload(cls.similarity_range))
            .options(selectinload(cls.winners))
        )

        result = await session.execute(stmt)

        return result.scalars().one_or_none()

    @classmethod
    async def get_active_in_channel(
        cls, channel_id: str, /, *, session: AsyncSession
    ) -> list[Game]:
        stmt = (
            select(cls)
            .where(cls.channel_id == channel_id, cls.active)
            .options(selectinload(cls.guesses))
            .options(selectinload(cls.similarity_range))
            .options(selectinload(cls.winners))
        )

        result = await session.execute(stmt)

        return result.scalars().all()

    @classmethod
    async def by_id(cls, game_id: int, /, *, session: AsyncSession) -> Optional[Game]:
        return (
            await session.scalars(
                select(cls)
                .where(cls.id == game_id)
                .options(selectinload(cls.guesses))
                .options(selectinload(cls.similarity_range))
                .options(selectinload(cls.winners))
            )
        ).one_or_none()

    async def add_guess(
        self, *, word: str, user_id: str, session: AsyncSession
    ) -> Guess:
        """Add a guess to the game"""
        from .guess import Guess
        from .nearby import Nearby
        from .word2vec import Word2Vec

        logger.debug(f"Adding guess {word=} to {self=}")

        # Check if user has already won
        stmt = select(GameUserWinnerAssociation).where(
            GameUserWinnerAssociation.game_id == self.id,
            GameUserWinnerAssociation.user_id == user_id,
        )
        existing_assoc = await session.scalar(stmt)
        if existing_assoc is not None:
            raise UserAlreadyWon("User already won")

        if word == self.secret:
            logger.debug(f"Guess was the secret, adding {user_id=} to winners")
            self.winners.append(
                GameUserWinnerAssociation(
                    game_id=self.id, user_id=user_id, guess_idx=len(self.guesses) + 1
                )
            )
            similarity = 100.0
            percentile = config.rules.similarity_count
        else:
            try:
                nearby = await Nearby.get(
                    session=session, word=self.secret, neighbor=word
                )
            except NotFound:
                guess_vec = await Word2Vec.get(word, session=session)
                if guess_vec is None:
                    logger.debug(f"Word not recognised: {word=}")
                    raise InvalidWord(f"Word not recognised: {word}")

                logger.debug(f"Guess was not within {config.rules.similarity_count}")
                secret_vec = await Word2Vec.get(self.secret, session=session)
                if secret_vec is None:
                    raise Exception("Secret word not recognised?")

                similarity = get_similarity(
                    secret_vec.expanded_vec, guess_vec.expanded_vec
                )
                percentile = 0
            else:
                similarity = get_similarity(
                    nearby.word_vec.expanded_vec, nearby.neighbor_vec.expanded_vec
                )
                percentile = nearby.percentile

        # Check if guess exists
        guess = await Guess.get(session=session, word=word, game_id=self.id)
        if guess is not None:
            logger.debug(f"Guess has already been made {guess=}")
            guess.updated = timestamp_ms()  # type: ignore
            guess.latest_guess_user_id = user_id  # type: ignore
            return guess

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
            .options(selectinload(Guess.game))
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
            .options(selectinload(Guess.game))
            .limit(n)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    def __repr__(self) -> str:
        return (
            f"<Game (id={self.id} puzzle_number={self.puzzle_number} "
            f"channel_id={self.channel_id} secret={self.secret})>"
        )
