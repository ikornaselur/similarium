from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

from similarium.config import config

Base = declarative_base()

engine = create_async_engine(config.database.uri, future=True, pool_pre_ping=True)
session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
