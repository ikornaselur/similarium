# flake8: noqa: E402
from logging import Logger
from typing import AsyncIterator, Iterable
from unittest import mock

import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

# We need to mock out the available secret words for tests
SECRET_WORDS = ["apple", "excited", "future"]

mock.patch("semantle_slack_bot.target_words.target_words", SECRET_WORDS).start()


from semantle_slack_bot.config import config as _config

# Overwride the database name to be in-memory for tests, before anything else
# is imported
_config.database.uri = "sqlite+aiosqlite:///:memory:"
from semantle_slack_bot import db as _db
from semantle_slack_bot.models import Game, User
from tests.init_db import insert_data


@pytest.fixture()
async def db() -> AsyncIterator:
    """Mock DB that inserts base test data for each tests that uses the db"""
    async with _db.engine.begin() as conn:
        await conn.run_sync(_db.Base.metadata.create_all)

    await insert_data()

    yield _db

    async with _db.engine.begin() as conn:
        await conn.run_sync(_db.Base.metadata.drop_all)


@pytest.fixture()
async def session(db) -> AsyncIterator:
    async with db.async_session() as s:
        yield s


@pytest.fixture()
async def game(session: AsyncSession) -> AsyncIterator[Game]:
    _game = Game.new(
        channel_id="channel_x",
        thread_ts="thread_x",
        puzzle_number=21,
    )
    session.add(_game)
    await session.commit()
    await session.refresh(_game)
    yield _game


@pytest.fixture()
async def user(session: AsyncSession) -> AsyncIterator[User]:
    _user = User(
        id="user_x",
        username="semantle-player",
        profile_photo="http://example.com/profile.jpg",
    )
    session.add(_user)
    await session.commit()
    yield _user
