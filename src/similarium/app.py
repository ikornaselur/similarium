import os
import re

import pytz
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.sql.expression import delete

from similarium import db
from similarium.command import Start, Stop, parse_command
from similarium.event_types import Body
from similarium.exceptions import InvalidWord, NotFound, ParseException
from similarium.logging import configure_logger, logger
from similarium.models import Channel, Game, User
from similarium.slack import SlackGame
from similarium.utils import get_header_text, get_puzzle_date, get_puzzle_number

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])

REGEX = re.compile(r"^(?P<guess>[A-Za-z]+)$")

TOP_GUESSES_TO_SHOW = 15
LATEST_GUESSES_TO_SHOW = 3


async def get_thread_blocks(session: AsyncSession, game: Game) -> list:
    slack_game = SlackGame(game)
    blocks = [
        slack_game.header,
        await slack_game.won(session=session) if not game.active else None,
        slack_game.divider,
        slack_game.markdown_section("*Latest guesses*"),
        *[
            slack_game.guess_context(guess, base_id="latest")
            for guess in await game.latest_guesses(
                LATEST_GUESSES_TO_SHOW, session=session
            )
        ],
        slack_game.markdown_section("*Top guesses*"),
        *[
            slack_game.guess_context(guess, base_id="top")
            for guess in await game.top_guesses(TOP_GUESSES_TO_SHOW, session=session)
        ],
        slack_game.input if game.active else None,
    ]

    return [b for b in blocks if b is not None]


@app.action("submit-guess")
async def handle_some_action(ack, body, client, respond):
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

            await respond(
                text="Update to todays game",
                blocks=await get_thread_blocks(session, game),
            )


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

    match parsed_command:
        case Start():
            # Check if there is already a game registered for the channel
            async with db.session() as session:
                channel = await Channel.by_id(channel_id, session=session)
            if channel is not None:
                logger.debug(f"Game was already registered for {channel_id=}")
                await respond(
                    text=(
                        ":no_entry_sign: Game is already registered for the channel. Please"
                        ' use the "stop" command before running "start" again.'
                    )
                )
                return

            # Get user timezone to normalize the game posting to UTC+0
            user_info = await client.users_info(user=command["user_id"])
            user_data = user_info.data["user"]
            timezone = pytz.timezone(user_data["tz"])
            time = parsed_command.when.replace(tzinfo=timezone)

            channel = Channel(
                id=channel_id,
                time=time,
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

    await respond(text=parsed_command.text, blocks=parsed_command.blocks)


@app.event("message")
async def message(body: Body, client, ack) -> None:
    await ack()

    event = body["event"]
    channel = event["channel"]

    if event["type"] == "message":
        message = event.get("text")

        if message == "!start":
            puzzle_number = get_puzzle_number()
            puzzle_date = get_puzzle_date(puzzle_number)
            header_text = get_header_text(puzzle_number, puzzle_date)

            resp = await client.chat_postMessage(
                text=header_text,
                channel=channel,
                blocks=[
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": header_text,
                            "emoji": True,
                        },
                    },
                    {"type": "divider"},
                    {
                        "dispatch_action": True,
                        "block_id": "guess-input",
                        "type": "input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "submit-guess",
                        },
                        "label": {"type": "plain_text", "text": "Guess", "emoji": True},
                    },
                ],
            )
            game = Game.new(
                channel_id=channel,
                thread_ts=resp["ts"],
                puzzle_number=puzzle_number,
                puzzle_date=puzzle_date,
            )
            async with db.session() as s:
                s.add(game)
                await s.commit()


async def main() -> None:
    configure_logger()

    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
