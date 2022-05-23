import asyncio
import datetime as dt
from typing import Awaitable, Callable

import sentry_sdk

from similarium import db
from similarium.exceptions import AccountInactive
from similarium.game import end_game, start_game
from similarium.logging import logger
from similarium.models import Channel
from similarium.utils import get_seconds_left_of_hour


async def action(
    channels: list[Channel], func: Callable[[str], Awaitable[None]]
) -> None:
    with sentry_sdk.start_transaction(op="task", name=f"Hourly task: {func.__name__}"):
        results = await asyncio.gather(
            *[func(channel.id) for channel in channels if channel.active],
            return_exceptions=True,
        )
        for channel, exc in filter(lambda _: bool(_[1]), zip(channels, results)):
            if isinstance(exc, AccountInactive):
                # Account is inactive on channel, mark as such
                async with db.session() as session:
                    channel.active = False  # type: ignore
                    await session.commit()
            else:
                # Unexpected error
                sentry_sdk.capture_exception(exc)


async def hourly_game_creator() -> None:
    """Hourly game creator

    Hourly task that will query for all active channels that should have a game
    posted and create games for each
    """
    while True:
        try:
            sleep_time = get_seconds_left_of_hour()
            logger.debug(f"Hourly task sleeping for {sleep_time:.0f} seconds")
            await asyncio.sleep(sleep_time)

            current_hour = dt.datetime.now(dt.timezone.utc).hour
            async with db.session() as session:
                channels = await Channel.by_hour(current_hour, session=session)

            logger.debug(f"Ending games in {len(channels)} channels")
            await action(channels, end_game)

            logger.debug(f"Starting games in {len(channels)} channels")
            await action(channels, start_game)
        except Exception as e:
            logger.error("Got exception in hourly task runner", exc_info=e)
            sentry_sdk.capture_exception(e)
