import asyncio
import os
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

from semantle_slack_bot import db
from semantle_slack_bot.config import config

SQLITE_SCHEMA = "sqlite+aiosqlite://"
POSTGRES_SCHEMA = "postgresql+asyncpg://"


async def create_all():
    console = Console()

    db_uri = config.database.uri
    if db_uri.startswith(SQLITE_SCHEMA):
        db_name = db_uri[len(SQLITE_SCHEMA) :]
        root = Path(__file__).parent.parent
        db_files = [
            root / name for name in (db_name, f"{db_name}-shm", f"{db_name}-wal")
        ]
        existing = [file for file in db_files if file.exists()]

        if existing:
            if Confirm.ask(f"Do you want to delete existing {db_name} database files?"):
                for file in existing:
                    os.remove(file)
            else:
                console.log("Aborting")
                return

    async with db.engine.begin() as conn:
        console.log("Dropping all tables")
        await conn.run_sync(db.Base.metadata.drop_all)

        console.log("Creating all tables")
        await conn.run_sync(db.Base.metadata.create_all)


asyncio.run(create_all())
