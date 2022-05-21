import asyncio
import datetime as dt
import re
from asyncio.exceptions import CancelledError

import pytz
import sentry_sdk
from aiohttp import web
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_server import AsyncSlackAppServer
from slack_sdk.errors import SlackApiError
from sqlalchemy.sql.expression import delete

from similarium import db
from similarium.command import Help, Manual, Start, Stop, parse_command
from similarium.config import config
from similarium.exceptions import (
    ChannelNotFound,
    GameNotRegistered,
    InvalidWord,
    NotFound,
    NotInChannel,
    ParseException,
    init_exception_handler,
)
from similarium.game import start_game, update_game
from similarium.logging import configure_logger, logger, web_logger
from similarium.models import Channel, Game, User
from similarium.slack import app
from similarium.tasks import hourly_game_creator
from similarium.utils import get_puzzle_number

REGEX = re.compile(r"^(?P<guess>[A-Za-z]+)$")

sentry_sdk.init(
    dsn=config.sentry.dsn,
    environment=config.sentry.env,
    integrations=[AioHttpIntegration()],
)


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
async def slash(ack, respond, say, command, client):
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
    user_id = command["user_id"]

    match parsed_command:
        case Start(when=when, when_human=when_human):
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
            user_info = await client.users_info(user=user_id)
            user_data = user_info.data["user"]
            # We're going to go by today to try to deal with daylight savings
            # TODO: Properly handle DST
            timezone = pytz.timezone(user_data["tz"])
            user_dt = dt.datetime.now(timezone).replace(
                hour=when.hour,
                minute=0,
                second=0,
                microsecond=0,
            )
            utc = pytz.timezone("UTC")

            datetime = utc.normalize(user_dt)
            time = datetime.time()

            # Check that we have permission to post to the channel
            try:
                await say(
                    f"<@{user_id}> has started a daily game of Similarium"
                    f" {when_human} {user_dt.tzname()}"
                )
            except SlackApiError as e:
                response = e.response.data
                await respond(
                    ":no_entry_sign: Unable to post to channel. You need to invite"
                    " @Similarium to this channel: `/invite @Similarium`"
                )
                # Report if unknown error
                error = response.get("error")
                if error not in ("channel_not_found", "not_in_channel"):
                    sentry_sdk.capture_exception(e)

                return

            logger.debug(f"User {when=} {timezone=} converted to {time=}")

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
            await say(f"<@{user_id}> has stopped the daily game of Similarium")
        case Manual(text=text, blocks=blocks):
            logger.debug("Starting manual game on channel")
            try:
                await start_game(channel_id)
            except GameNotRegistered:
                await respond(
                    text=(
                        ":no_entry_sign: You need to register a game to the channel"
                        " before manual posting"
                    )
                )
            except (ChannelNotFound, NotInChannel):
                await respond(
                    text=(
                        ":no_entry_sign: Unable to post to channel. You need to invite"
                        " @Similarium to this channel: `/invite @Similarium`"
                    )
                )
            await respond(text=text, blocks=blocks)
        case Help(text=text, blocks=blocks):
            await respond(text=text, blocks=blocks)


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


async def run_socket_mode():
    handler = AsyncSocketModeHandler(app, config.slack.app_token)

    logger.debug("Starting background task")
    background_task = asyncio.create_task(hourly_game_creator())

    await handler.start_async()

    logger.debug("Cleanup background task")
    background_task.cancel()
    try:
        await background_task
    except CancelledError:
        pass


def main() -> None:
    configure_logger()
    loop = asyncio.new_event_loop()
    init_exception_handler(loop)

    if config.slack.dev_mode:
        asyncio.run(run_socket_mode())
    else:
        server = AsyncSlackAppServer(
            port=3000,
            path="/slack/events",
            app=app,
            host="0.0.0.0",
        )
        server.web_app.on_startup.append(startup_task)
        server.web_app.on_cleanup.append(cleanup_task)

        web.run_app(
            server.web_app,
            host=server.host,
            port=server.port,
            access_log=web_logger,
            loop=loop,
        )


if __name__ == "__main__":
    main()
