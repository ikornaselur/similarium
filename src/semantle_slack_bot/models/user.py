from __future__ import annotations

from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from semantle_slack_bot.db import Base


class User(Base):
    __tablename__ = "user"

    id = sa.Column(sa.Text, primary_key=True)
    profile_photo = sa.Column(sa.Text, nullable=False)
    username = sa.Column(sa.Text, nullable=False)

    @classmethod
    async def by_id(cls, user_id: str, /, *, session: AsyncSession) -> Optional[User]:
        result = await session.execute(select(cls).where(cls.id == user_id))
        return result.scalars().one_or_none()

    def __repr__(self) -> str:
        return f"<User ({self.id}: {self.username})>"
