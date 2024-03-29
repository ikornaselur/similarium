# flake8: noqa: E402
from typing import AsyncIterator
from unittest import mock

import pytest

# We need to mock out the available secret words for tests
SECRET_WORDS = ["apple", "excited", "future"]

mock.patch("similarium.target_words.target_words", SECRET_WORDS).start()


from similarium.config import config as _config

# Overwride the database name to be in-memory for tests, before anything else
# is imported
_config.database.uri = "sqlite+aiosqlite:///:memory:"
from similarium import db as _db
from similarium.models import Game, User
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
async def game_id(db) -> AsyncIterator[int]:
    async with db.session() as session:
        _game = Game.new(
            channel_id="channel_x",
            thread_ts="thread_x",
            puzzle_number=21,
            puzzle_date="April 21st",
        )
        session.add(_game)
        await session.commit()
        await session.refresh(_game)

    yield _game.id


@pytest.fixture()
async def user_id(db) -> AsyncIterator[str]:
    async with db.session() as session:
        _user = User(
            id="user_x",
            username="similarium-player",
            profile_photo="http://example.com/profile.jpg",
        )
        session.add(_user)
        await session.commit()

    yield _user.id


@pytest.fixture()
async def user_id_2(db) -> AsyncIterator[str]:
    async with db.session() as session:
        _user = User(
            id="user_y",
            username="similarium-player-2",
            profile_photo="http://example.com/profile2.jpg",
        )
        session.add(_user)
        await session.commit()

    yield _user.id


@pytest.fixture(autouse=True)
async def slack_app() -> AsyncIterator[mock.AsyncMock]:
    """Mock slack app completely"""
    with mock.patch("similarium.slack.AsyncApp") as m:
        yield m
