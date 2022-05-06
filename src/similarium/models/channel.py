from __future__ import annotations

from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from similarium.db import Base


class Channel(Base):
    __tablename__ = "channel"

    id = sa.Column(sa.Text, primary_key=True)
    time = sa.Column(sa.Time, nullable=False)  # Time to post the daily puzzle, on UTC+0

    @classmethod
    async def by_id(
        cls, channel_id: str, /, *, session: AsyncSession
    ) -> Optional[Channel]:
        return (
            await session.scalars(select(cls).where(cls.id == channel_id))
        ).one_or_none()

    def __repr__(self) -> str:
        return f"<Channel (id={self.id})>"
