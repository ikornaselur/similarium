# flake8: noqa: E402
from typing import AsyncIterator
from unittest import mock

import pytest

# We need to mock out the available secret words for tests
SECRET_WORDS = ["apple", "excited", "future"]

mock.patch("semantle_slack_bot.target_words.target_words", SECRET_WORDS).start()


from semantle_slack_bot.config import config as _config

# Overwride the database name to be in-memory for tests, before anything else
# is imported
_config.database.name = ":memory:"
from semantle_slack_bot import db as _db
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
async def game(db, session) -> AsyncIterator[_db.Game]:
    _game = db.Game.new(
        channel_id="channel_x",
        thread_ts="thread_x",
        puzzle_number=21,
    )
    session.add(_game)
    await session.commit()
    await session.refresh(_game)
    yield _game


@pytest.fixture()
async def user(db, session) -> AsyncIterator[_db.User]:
    _user = db.User(
        id="user_x",
        username="semantle-player",
        profile_photo="http://example.com/profile.jpg",
    )
    session.add(_user)
    await session.commit()
    yield _user
