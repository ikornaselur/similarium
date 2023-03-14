import time
import datetime as dt
from logging import Logger
from typing import Any, Optional
from uuid import uuid4

import sqlalchemy as sa
from slack_sdk.oauth.installation_store import Installation
from slack_sdk.oauth.installation_store.async_installation_store import (
    AsyncInstallationStore,
)
from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
from slack_sdk.oauth.state_store.async_state_store import AsyncOAuthStateStore
from slack_sdk.oauth.state_store.sqlalchemy import SQLAlchemyOAuthStateStore

from similarium import db


class AsyncSQLAlchemyInstallationStore(AsyncInstallationStore):
    client_id: str
    metadata: sa.MetaData
    installations: sa.Table
    bots: sa.Table

    def __init__(
        self,
        client_id: str,
        metadata: sa.MetaData,
        logger: Logger,
    ):
        self.client_id = client_id
        self.metadata = metadata
        self.installations = SQLAlchemyInstallationStore.build_installations_table(
            metadata=self.metadata,
            table_name=SQLAlchemyInstallationStore.default_installations_table_name,
        )
        self.bots = SQLAlchemyInstallationStore.build_bots_table(
            metadata=self.metadata,
            table_name=SQLAlchemyInstallationStore.default_bots_table_name,
        )
        self._logger = logger

    @property
    def logger(self) -> Logger:
        return self._logger

    async def async_save(self, installation: Installation):
        async with db.session() as s:
            async with s.begin_nested():
                i = installation.to_dict()
                i["client_id"] = self.client_id
                await s.execute(self.installations.insert(), i)
                b = installation.to_bot().to_dict()
                b["client_id"] = self.client_id
                await s.execute(self.bots.insert(), b)
                await s.commit()

    async def async_find_installation(
        self,
        *,
        enterprise_id: Optional[str],
        team_id: Optional[str],
        is_enterprise_install: Optional[bool],
        **kwargs: Any,
    ) -> Optional[Installation]:
        c = self.installations.c
        where_filter = [
            c.enterprise_id == enterprise_id,
            c.team_id == team_id,
            c.is_enterprise_install == is_enterprise_install,
        ]
        if "user_id" in kwargs:
            where_filter.append(c.user_id == kwargs["user_id"])
        stmt = (
            sa.select(c)
            .where(sa.and_(*where_filter))
            .order_by(sa.desc(c.installed_at))
            .limit(1)
        )
        async with db.session() as s:
            result = await s.execute(stmt)
            if inst := result.one_or_none():
                return Installation(
                    app_id=inst["app_id"],
                    enterprise_id=inst["enterprise_id"],
                    team_id=inst["team_id"],
                    user_id=inst["user_id"],
                    bot_token=inst["bot_token"],
                    bot_id=inst["bot_id"],
                    bot_user_id=inst["bot_user_id"],
                    bot_scopes=inst["bot_scopes"],
                    installed_at=inst["installed_at"],
                )
            else:
                return None


class AsyncSQLAlchemyOAuthStateStore(AsyncOAuthStateStore):
    expiration_seconds: int
    metadata: sa.MetaData
    oauth_states: sa.Table

    def __init__(
        self,
        *,
        expiration_seconds: int,
        metadata: sa.MetaData,
        logger: Logger,
    ):
        self.expiration_seconds = expiration_seconds
        self.metadata = metadata
        self.oauth_states = SQLAlchemyOAuthStateStore.build_oauth_states_table(
            metadata=self.metadata,
            table_name=SQLAlchemyOAuthStateStore.default_table_name,
        )
        self._logger = logger

    @property
    def logger(self) -> Logger:
        return self._logger

    async def async_issue(self) -> str:
        state: str = str(uuid4())
        now = dt.datetime.utcfromtimestamp(time.time() + self.expiration_seconds)
        async with db.session() as s:
            stmt = sa.insert(self.oauth_states).values(state=state, expire_at=now)
            await s.execute(stmt)
            await s.commit()
        return state

    async def async_consume(self, state: str) -> bool:
        try:
            async with db.session() as s:
                async with s.begin_nested():
                    c = self.oauth_states.c
                    stmt = self.oauth_states.select().where(
                        sa.and_(
                            c.state == state,
                            c.expire_at > dt.datetime.utcnow(),
                        )
                    )
                    result = await s.execute(stmt)
                    row = result.one()
                    self.logger.debug(f"consume's query result: {row}")
                    await s.execute(self.oauth_states.delete().where(c.id == row["id"]))
                    await s.commit()
                    return True
        except sa.exc.NoResultFound as e:  # pyright: ignore
            message = f"Failed to find any persistent data for state: {state} - {e}"
            self.logger.warning(message)
            return False
