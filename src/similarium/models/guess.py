from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload

from similarium.config import config
from similarium.db import Base
from similarium.logging import logger
from similarium.utils import timestamp_ms

if TYPE_CHECKING:
    from similarium.models import Game


class Guess(Base):
    __tablename__ = "guess"

    id = sa.Column(sa.Integer, primary_key=True)
    game_id = sa.Column(sa.Integer, sa.ForeignKey("game.id"), nullable=False)
    game = relationship("Game", back_populates="guesses", lazy="joined")

    # Milliseconds since start of previous day UTC, only used for ordering
    # guesses in a game. Previous day is used to deal with time zones
    updated = sa.Column(sa.BigInteger, nullable=False)

    user_id = sa.Column(sa.Text, sa.ForeignKey("user.id"), nullable=False)
    user = relationship("User", lazy="joined", foreign_keys=[user_id])

    latest_guess_user_id = sa.Column(sa.Text, sa.ForeignKey("user.id"), nullable=False)
    latest_guess_user = relationship(
        "User", lazy="joined", foreign_keys=[latest_guess_user_id]
    )

    word = sa.Column(sa.Text, nullable=False)
    percentile = sa.Column(sa.Integer, nullable=False)
    similarity = sa.Column(sa.Float, nullable=False)
    idx = sa.Column(sa.Integer, nullable=False)

    @classmethod
    async def new(
        cls,
        *,
        game: Game,
        user_id: str,
        word: str,
        percentile: int,
        similarity: float,
        session: AsyncSession,
    ) -> Guess:
        logger.debug(
            f"Creating new Guess: {game=} {user_id=} "
            f"{word=} {percentile=} {similarity=}"
        )

        # XXX: Race condition??
        stmt = select(sa.func.count(word)).where(cls.game_id == game.id)
        result = await session.execute(stmt)
        count = result.scalars().one()

        return cls(
            game_id=game.id,
            updated=timestamp_ms(),
            user_id=user_id,
            latest_guess_user_id=user_id,
            word=word,
            percentile=percentile,
            similarity=similarity,
            idx=count + 1,
        )

    @classmethod
    async def get(
        cls, *, session: AsyncSession, word: str, game_id: int
    ) -> Optional[Guess]:
        logger.debug(f"Getting guess {word=} {game_id=}")
        stmt = (
            select(cls)
            .where(
                cls.word == word,
                cls.game_id == game_id,
            )
            .options(selectinload(cls.game))
        )

        result = await session.execute(stmt)

        return result.scalars().one_or_none()

    @property
    def is_secret(self) -> bool:
        return self.word == self.game.secret

    def __repr__(self) -> str:
        if self.percentile:
            percentile_repr = f"{self.percentile}/{config.rules.similarity_count}"
        else:
            percentile_repr = "cold"
        return f"<Guess {self.idx}. (id={self.id} {self.word}: {percentile_repr})>"
