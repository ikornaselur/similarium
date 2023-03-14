import asyncio
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine

from similarium.config import config as similarium_config
from similarium.db import Base
from similarium.models import *  # noqa: F401
from similarium.models.stores import (
    AsyncSQLAlchemyInstallationStore,
    AsyncSQLAlchemyOAuthStateStore,
)

logger = logging.getLogger("alembic")

# Create stores to have the metadata populated
installation_store = AsyncSQLAlchemyInstallationStore(
    client_id="client_id",
    metadata=Base.metadata,
    logger=logger,
)
oauth_state_store = AsyncSQLAlchemyOAuthStateStore(
    expiration_seconds=600,
    metadata=Base.metadata,
    logger=logger,
)


config = context.config
config.set_main_option("sqlalchemy.url", similarium_config.database.uri)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


asyncio.run(run_migrations_online())
