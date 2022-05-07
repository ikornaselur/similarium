from __future__ import annotations

from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from similarium.db import Base


class SimilarityRange(Base):
    __tablename__ = "similarity_range"

    word = sa.Column(sa.Text, primary_key=True)
    top = sa.Column(sa.Float, nullable=False)
    top10 = sa.Column(sa.Float, nullable=False)
    rest = sa.Column(sa.Float, nullable=False)

    @classmethod
    async def get(
        cls, word: str, /, *, session: AsyncSession
    ) -> Optional[SimilarityRange]:
        stmt = select(cls).where(cls.word == word)
        result = await session.execute(stmt)
        return result.scalars().one_or_none()

    def __repr__(self) -> str:
        top = self.top
        top10 = self.top10
        rest = self.rest

        return f"<SimilarityRange ({self.word}: {top=:0.2f} {top10=:0.2f} {rest=:0.2})>"
