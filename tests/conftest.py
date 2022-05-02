# flake8: noqa: E402
from typing import AsyncGenerator

import pytest

from semantle_slack_bot.config import config as _config

# Overwride the database name to be in-memory for tests
_config.database.name = ":memory:"
from semantle_slack_bot import db as _db

from tests.init_db import insert_data


@pytest.fixture()
async def db() -> AsyncGenerator:
    """Mock DB that inserts base test data for each tests that uses the db"""
    async with _db.engine.begin() as conn:
        await conn.run_sync(_db.Base.metadata.create_all)

    await insert_data()

    yield _db

    async with _db.engine.begin() as conn:
        await conn.run_sync(_db.Base.metadata.drop_all)
