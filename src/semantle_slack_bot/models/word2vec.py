from __future__ import annotations

import struct
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from semantle_slack_bot.db import Base
from semantle_slack_bot.utils import expand_bfloat


class Word2Vec(Base):
    __tablename__ = "word2vec"

    word = sa.Column(sa.Text, primary_key=True)
    vec = sa.Column(sa.LargeBinary, nullable=False)

    @property
    def expanded_vec(self) -> list[float]:
        return list(struct.unpack("300f", expand_bfloat(self.vec)))

    @classmethod
    async def get(cls, word: str, /, *, session: AsyncSession) -> Optional[Word2Vec]:
        stmt = select(cls).where(cls.word == word)
        result = await session.execute(stmt)
        return result.scalars().one_or_none()

    def __repr__(self) -> str:
        return f"<Word2Vec ({self.word})>"
