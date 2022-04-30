import os
import re

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from semantle_slack_bot import db
from semantle_slack_bot.event_types import Body
from semantle_slack_bot.logging import logger
from semantle_slack_bot.slack import SlackGame

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])

REGEX = re.compile(r"^(?P<guess>[A-Za-z]+)$")

TOP_GUESSES_TO_SHOW = 15
LATEST_GUESSES_TO_SHOW = 3


async def get_thread_blocks(game: db.Game) -> list:
    slack_game = SlackGame(game)
    blocks = [
        slack_game.header,
        await slack_game.won if not game.active else None,
        slack_game.divider,
        slack_game.markdown_section("*Latest guesses*"),
        *[
            slack_game.guess_context(guess, base_id="latest")
            for guess in await game.latest_guesses(LATEST_GUESSES_TO_SHOW)
        ],
        slack_game.markdown_section("*Top guesses*"),
        *[
            slack_game.guess_context(guess, base_id="top")
            for guess in await game.top_guesses(TOP_GUESSES_TO_SHOW)
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

    game = await db.Game.get_or_create(
        channel_id=channel,
        thread_ts=message_ts,
        puzzle_number=db.Game.get_today_puzzle_number(),
    )

    if value is not None and (match := REGEX.match(value.strip())):
        word = match.group("guess").lower()
        user_id = body["user"]["id"]

        try:
            await game.add_guess(word=word, user_id=user_id)
        except db.InvalidWord:
            return
        user = await db.User.by_id(user_id)
        if user is None:
            user_info = await client.users_info(user=user_id)
            user_data = user_info.data["user"]
            await db.User.new(
                user_id=user_id,
                profile_photo=user_data["profile"]["image_24"],
                username=user_data["name"],
            )

        await respond(
            text="Update to todays game",
            blocks=await get_thread_blocks(game),
        )

        """
        await client.chat_update(
            channel=channel,
            ts=message_ts,
            text="Update to todays game",
            blocks=await get_thread_blocks(game),
        )
        """


@app.event("message")
async def message(body: Body, client, ack) -> None:
    await ack()

    event = body["event"]
    channel = event["channel"]

    if event["type"] == "message":
        message = event.get("text")

        if message == "!start":
            resp = await client.chat_postMessage(
                channel=channel,
                blocks=[
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "Semantle day 4 - April 25th",
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
            await db.Game.new(
                channel_id=channel,
                thread_ts=resp["ts"],
                puzzle_number=db.Game.get_today_puzzle_number(),
            )


async def main() -> None:
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
