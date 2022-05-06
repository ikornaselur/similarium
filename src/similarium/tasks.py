import asyncio
import datetime as dt

from similarium import db
from similarium.game import end_game, start_game
from similarium.logging import logger
from similarium.models import Channel
from similarium.utils import get_seconds_left_of_hour


async def hourly_game_creator() -> None:
    """Hourly game creator

    Hourly task that will query for all active channels that should have a game
    posted and create games for each
    """
    while True:
        sleep_time = get_seconds_left_of_hour()
        logger.debug(f"Hourly task sleeping for {sleep_time:.0f} seconds")
        await asyncio.sleep(sleep_time)

        current_hour = dt.datetime.now().hour

        async with db.session() as session:
            channels = await Channel.by_hour(current_hour, session=session)

        logger.debug(f"Ending games in {len(channels)} channels")
        # End active games
        await asyncio.gather(*[end_game(channel.id) for channel in channels])

        logger.debug(f"Starting games in {len(channels)} channels")
        # Start new games
        await asyncio.gather(*[start_game(channel.id) for channel in channels])

        # TODO Timeouts?
