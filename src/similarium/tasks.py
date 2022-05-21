import asyncio
import datetime as dt

import sentry_sdk

from similarium import db
from similarium.game import end_game, start_game
from similarium.logging import logger
from similarium.models import Channel
from similarium.utils import get_seconds_left_of_hour


async def create_games(hour: int) -> None:
    """Create the games for a certain hour on all active channels"""
    async with db.session() as session:
        channels = await Channel.by_hour(hour, session=session)

    logger.debug(f"Ending games in {len(channels)} channels")
    # End active games
    results = await asyncio.gather(
        *[end_game(channel.id) for channel in channels], return_exceptions=True
    )
    for exc in filter(bool, results):
        sentry_sdk.capture_exception(exc)

    logger.debug(f"Starting games in {len(channels)} channels")
    # Start new games
    results = await asyncio.gather(
        *[start_game(channel.id) for channel in channels], return_exceptions=True
    )
    for exc in filter(bool, results):
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

            await create_games(current_hour)

            # TODO Timeouts?
        except Exception as e:
            logger.error("Got exception in hourly task runner", exc_info=e)
            sentry_sdk.capture_exception(e)
