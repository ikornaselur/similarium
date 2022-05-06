from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload

from semantle_slack_bot.config import config
from semantle_slack_bot.db import Base
from semantle_slack_bot.exceptions import NotFound


class Nearby(Base):
    __tablename__ = "nearby"

    word = sa.Column(sa.Text, sa.ForeignKey("word2vec.word"))
    neighbor = sa.Column(sa.Text, sa.ForeignKey("word2vec.word"))
    similarity = sa.Column(sa.Float, nullable=False)
    percentile = sa.Column(sa.Integer, nullable=False)

    word_vec = relationship("Word2Vec", foreign_keys=[word])
    neighbor_vec = relationship("Word2Vec", foreign_keys=[neighbor])

    __table_args__ = (sa.PrimaryKeyConstraint(word, neighbor),)

    @classmethod
    async def get(cls, *, session: AsyncSession, word: str, neighbor: str) -> Nearby:
        """Get Nearby by word and neighbor"""
        stmt = (
            select(cls)
            .where(cls.word == word, cls.neighbor == neighbor)
            .options(
                selectinload(cls.word_vec),
                selectinload(cls.neighbor_vec),
            )
        )
        result = await session.execute(stmt)
        nearby = result.scalars().one_or_none()

        if nearby is None:
            raise NotFound(f"Nearby not found for {neighbor=} {word=}")

        return nearby

    def __repr__(self) -> str:
        return (
            f"<Nearby ({self.word} -> {self.percentile}/"
            f"{config.rules.similarity_count} "
            f"{self.neighbor}: {self.similarity:.02f})>"
        )
