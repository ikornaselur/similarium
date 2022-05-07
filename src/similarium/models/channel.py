from __future__ import annotations

from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from similarium.db import Base


class Channel(Base):
    __tablename__ = "channel"

    id = sa.Column(sa.Text, primary_key=True)
    # The hour to post the daily puzzle, on UTC+0
    hour = sa.Column(sa.Integer, nullable=False)

    @classmethod
    async def by_id(
        cls, channel_id: str, /, *, session: AsyncSession
    ) -> Optional[Channel]:
        return (
            await session.scalars(select(cls).where(cls.id == channel_id))
        ).one_or_none()

    @classmethod
    async def by_hour(cls, hour: int, /, *, session: AsyncSession) -> list[Channel]:
        return (await session.scalars(select(cls).where(cls.hour == hour))).all()

    def __repr__(self) -> str:
        return f"<Channel (id={self.id})>"
