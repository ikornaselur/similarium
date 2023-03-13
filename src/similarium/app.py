import asyncio
import datetime as dt
import random
import re
from asyncio.exceptions import CancelledError

import pytz
import sentry_sdk
from aiohttp import web
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_server import AsyncSlackAppServer
from slack_sdk.errors import SlackApiError

from similarium import __version__, db
from similarium.command import Help, Manual, Start, Stop, parse_command
from similarium.config import config
from similarium.exceptions import (
    InvalidWord,
    NotFound,
    ParseException,
    UserAlreadyWon,
    init_exception_handler,
)
from similarium.game import end_game, start_game, update_game
from similarium.logging import configure_logger, logger, web_logger
from similarium.models import Channel, Game, User
from similarium.slack import app, get_bot_token_for_team
from similarium.spellings import americanize
from similarium.tasks import hourly_game_creator
from similarium.utils import CELEBRATE_EMOJIS, get_puzzle_number

REGEX = re.compile(r"^(?P<guess>[A-Za-z]+)$")


sentry_sdk.init(
    dsn=config.sentry.dsn,
    release=f"similarium@{__version__}",
    environment=config.sentry.env,
    integrations=[AioHttpIntegration(), SqlalchemyIntegration()],
    traces_sample_rate=1.0,
    _experiments={
        "profiles_sample_rate": 1.0,
    },
)


@app.action("submit-guess")
async def handle_submit_guess(ack, say, body, client):
    with sentry_sdk.start_transaction(op="task", name="Submit guess"):
        ack_task = asyncio.create_task(ack())
        if (
            not len(body.get("actions", []))
            or body["actions"][0].get("action_id") != "submit-guess"
        ):
            logger.error("Unable to get geuss from submission")
            await ack_task
            return
        value = body["actions"][0]["value"]

        logger.info(f"{value=}")

        message_ts = body["container"]["message_ts"]
        channel = body["container"]["channel_id"]
        team_id = body["user"]["team_id"]

        async def _ephemeral(text: str) -> None:
            await client.chat_postEphemeral(
                token=get_bot_token_for_team(team_id),
                text=text,
                channel=channel,
                user=user_id,
            )

        async with db.session() as session:
            puzzle_number = get_puzzle_number()
            game = await Game.get(
                session=session,
                channel_id=channel,
                thread_ts=message_ts,
            )
            if game is None:
                raise NotFound(
                    f"Game not found for {channel=} {message_ts=} {puzzle_number=}"
                )

            if value is not None and (match := REGEX.match(value.strip())):
                word = americanize(match.group("guess").lower())
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
                elif not await game.has_guessed(user.id, session=session):
                    logger.debug("First time this user is guessing in game")
                    # First time they guess in the current game, let's check if
                    # they've updated their profile
                    user_info = await client.users_info(user=user_id)
                    user_data = user_info.data["user"]

                    profile_photo = user_data["profile"]["image_24"]

                    if user.profile_photo != profile_photo:
                        user.profile_photo = profile_photo
                        session.add(user)
                        await session.commit()

                try:
                    guess = await game.add_guess(
                        word=word, user_id=user_id, session=session
                    )
                    await session.commit()
                    if celebration := await guess.get_celebration(session=session):
                        # It's worth celebrating this guess!
                        # This is done for the first words that breach top 1000, top 100 and top 10
                        await say(celebration)
                    if guess.is_secret:
                        # Let the user know that it was the secret
                        await _ephemeral(
                            f":tada: You found the secret! It was *{word}* :tada:"
                        )
                        # Also post on the channel to celebrate!
                        celebrate_emoji = random.choice(CELEBRATE_EMOJIS)
                        await say(
                            f"{celebrate_emoji} <@{user_id}> has just found the "
                            f"secret of the day! {celebrate_emoji}"
                        )
                except UserAlreadyWon:
                    await _ephemeral(
                        ":warning: You already got the winning word, you can't make"
                        " any further guesses :warning:"
                    )
                    await ack_task
                    return
                except InvalidWord:
                    await _ephemeral(
                        f':warning: *"{word}" is not a valid word!* :warning:'
                    )
                    await ack_task
                    return
        await update_game(game)
        await ack_task


@app.command("/similarium")
async def slash(ack, respond, say, command, client):
    ack_task = asyncio.create_task(ack())

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
            if channel is not None and channel.active:
                logger.debug(f"Game was already registered for {channel_id=}")
                await respond(
                    text=(
                        ":no_entry_sign: Game is already registered for the channel."
                        ' Please use the "stop" command before running "start" again.'
                    )
                )
                await ack_task
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

                await ack_task
                return

            logger.debug(f"User {when=} {timezone=} converted to {time=}")

            if channel is None:
                logger.debug(f"Creating new channel for {channel_id=}")
                channel = Channel(
                    id=channel_id,
                    team_id=team_id,
                    hour=time.hour,
                )
            else:
                logger.debug(f"Updating existing channel for {channel_id=}")
                channel.hour = time.hour  # pyright: ignore
                channel.active = True  # pyright: ignore
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
                await ack_task
                return
            logger.debug(f"Setting {channel} as inactive")
            async with db.session() as session:
                channel = await Channel.by_id(channel_id, session=session)
                if channel:
                    channel.active = False  # pyright: ignore
                    session.add(channel)
                    await session.commit()
            await say(f"<@{user_id}> has stopped the daily game of Similarium")
        case Help(text=text, blocks=blocks):
            await respond(text=text, blocks=blocks)
        case Manual(action="start"):
            logger.debug("Manually starting game on channel")
            try:
                await start_game(channel_id)
            except Exception as e:
                await respond(text=str(e))
        case Manual(action="end"):
            logger.debug("Manually ending game on channel")
            try:
                await end_game(channel_id)
            except Exception as e:
                await respond(text=str(e))
    await ack_task


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
