import asyncio
import datetime as dt
import re
from asyncio.exceptions import CancelledError

import pytz
from aiohttp import web
from slack_bolt.app.async_server import AsyncSlackAppServer
from sqlalchemy.sql.expression import delete

from similarium import db
from similarium.command import Manual, Start, Stop, parse_command
from similarium.exceptions import (
    ChannelNotFound,
    InvalidWord,
    NotFound,
    NotInChannel,
    ParseException,
)
from similarium.game import start_game, update_game
from similarium.logging import configure_logger, logger, web_logger
from similarium.models import Channel, Game, User
from similarium.slack import app
from similarium.tasks import hourly_game_creator
from similarium.utils import get_puzzle_number

REGEX = re.compile(r"^(?P<guess>[A-Za-z]+)$")


@app.action("submit-guess")
async def handle_some_action(ack, body, client):
    await ack()

    value = body["state"]["values"]["guess-input"]["submit-guess"]["value"]
    logger.info(f"{value=}")

    message_ts = body["container"]["message_ts"]
    channel = body["container"]["channel_id"]

    async with db.session() as session:
        puzzle_number = get_puzzle_number()
        game = await Game.get(
            session=session,
            channel_id=channel,
            thread_ts=message_ts,
            puzzle_number=puzzle_number,
        )
        if game is None:
            raise NotFound(
                f"Game not found for {channel=} {message_ts=} {puzzle_number=}"
            )

        if value is not None and (match := REGEX.match(value.strip())):
            word = match.group("guess").lower()
            user_id = body["user"]["id"]

            user = await User.by_id(user_id, session=session)
            if user is None:
                user_info = await client.users_info(user=user_id)
                user_data = user_info.data["user"]
                user = User(
                    id=user_id,
                    profile_photo=user_data["profile"]["image_24"],
                    username=user_data["name"],
                )
                session.add(user)
                await session.commit()

            try:
                await game.add_guess(word=word, user_id=user_id, session=session)
                await session.commit()
            except InvalidWord:
                return

    await update_game(game)


@app.command("/similarium")
async def slash(ack, respond, command, client):
    await ack()

    text = command["text"].strip()
    try:
        parsed_command = parse_command(text)
    except ParseException as e:
        await respond(text=str(e))
        return
    logger.info(f"Received {parsed_command} command")
    channel_id = command["channel_id"]
    team_id = command["team_id"]

    match parsed_command:
        case Start():
            # Check if there is already a game registered for the channel
            async with db.session() as session:
                channel = await Channel.by_id(channel_id, session=session)
            if channel is not None:
                logger.debug(f"Game was already registered for {channel_id=}")
                await respond(
                    text=(
                        ":no_entry_sign: Game is already registered for the channel."
                        ' Please use the "stop" command before running "start" again.'
                    )
                )
                return

            # Get user timezone to normalize the game posting to UTC+0
            user_info = await client.users_info(user=command["user_id"])
            user_data = user_info.data["user"]
            # We're going to go by today to try to deal with daylight savings
            # TODO: Properly handle DST
            timezone = pytz.timezone(user_data["tz"])
            utc = pytz.timezone("UTC")

            datetime = utc.normalize(
                dt.datetime.now(timezone).replace(
                    hour=parsed_command.when.hour,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            )
            time = datetime.time()

            logger.debug(
                f"User {parsed_command.when=} {timezone=} converted to {time=}"
            )

            channel = Channel(
                id=channel_id,
                team_id=team_id,
                hour=time.hour,
            )
            logger.debug(f"Adding Channel {channel_id=}")
            async with db.session() as session:
                session.add(channel)
                await session.commit()
        case Stop():
            async with db.session() as session:
                channel = await Channel.by_id(channel_id, session=session)
            if channel is None:
                logger.debug(f"No game was registered {channel_id=}")
                await respond(
                    text=(
                        ":no_entry_sign: No game is registered for the channel, did you"
                        ' mean to run "start"?'
                    )
                )
                return
            logger.debug(f"Deleting {channel}")
            async with db.session() as session:
                stmt = delete(Channel).where(Channel.id == channel.id)
                await session.execute(stmt)
                await session.commit()
        case Manual():
            logger.debug("Starting manual game on channel")
            try:
                await start_game(channel_id)
            except (ChannelNotFound, NotInChannel):
                await respond(
                    text=(
                        ":no_entry_sign: Unable to post to channel. You need to invite"
                        " @Similarium to this channel: `/invite @Similarium`"
                    )
                )

    await respond(text=parsed_command.text, blocks=parsed_command.blocks)


async def startup_task(app):
    logger.debug("Starting background task")
    app["background_task"] = asyncio.create_task(hourly_game_creator())


async def cleanup_task(app):
    logger.debug("Cleanup background task")
    app["background_task"].cancel()
    try:
        await app["background_task"]
    except CancelledError:
        pass


def main() -> None:
    configure_logger()

    server = AsyncSlackAppServer(
        port=3000,
        path="/slack/events",
        app=app,
        host="0.0.0.0",
    )
    server.web_app.on_startup.append(startup_task)
    server.web_app.on_cleanup.append(cleanup_task)

    web.run_app(
        server.web_app, host=server.host, port=server.port, access_log=web_logger
    )


if __name__ == "__main__":
    main()