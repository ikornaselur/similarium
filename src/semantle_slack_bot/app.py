import os
import re
from typing import Awaitable, Callable, Optional

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from semantle_slack_bot import db
from semantle_slack_bot.event_types import Body
from semantle_slack_bot.utils import get_custom_progress_bar

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])

REGEX = re.compile(r"^(?P<guess>[A-Za-z]+)$")

Say = Callable[[str], Awaitable[dict]]
Guess = tuple[float, Optional[int], int, str, str]

TOP_GUESSES_TO_SHOW = 15
LATEST_GUESSES_TO_SHOW = 3

DAY = 1
PROFILE = "https://pbs.twimg.com/profile_images/625633822235693056/lNGUneLX_400x400.jpg"

GUESSES: dict[str, dict[str, list[Guess]]] = {}
GAMES = {}


def get_progress_bar(amount: int, total: int) -> str:
    green_blocks_count = int(round(amount / total * 100, -1)) // 10
    green_blocks = f"{':large_green_square:' * green_blocks_count}"
    white_blocks = f"{':white_square:' * (10 - green_blocks_count)}"
    return f"{green_blocks}{white_blocks}"


async def get_thread_blocks(game: db.Game) -> list:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Semantle day {DAY} - April 16th",
                "emoji": True,
            },
        },
        {"type": "divider"},
    ]

    top_guesses = await game.top_guesses(TOP_GUESSES_TO_SHOW)
    latest_guesses = await game.latest_guesses(LATEST_GUESSES_TO_SHOW)

    def guess_line(guess: db.Guess) -> list[dict]:
        if guess.percentile:
            closeness = (
                f"{get_custom_progress_bar(guess.percentile, 1000, width=6)} "
                f"{guess.percentile:<03}/1000"
            )
        else:
            closeness = f"{get_custom_progress_bar(0, 1000, width=6)} ~~~/1000"

        return [
            {"type": "image", "image_url": PROFILE, "alt_text": "profile"},
            {"type": "mrkdwn", "text": closeness},
            {
                "type": "mrkdwn",
                "text": f"{guess.idx:>2}.   _{guess.similarity:<6.02f}_       *{guess.word:<12}*",
            },
        ]

    # Show the latest guesses
    blocks.append(
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Latest guesses*"}}
    )
    for guess in latest_guesses:
        blocks.append({"type": "context", "elements": guess_line(guess)})

    blocks.append({"type": "divider"})
    blocks.append(
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Top guesses*"}}
    )

    for guess in top_guesses:
        blocks.append({"type": "context", "elements": guess_line(guess)})

    blocks.append(
        {
            "dispatch_action": True,
            "block_id": "guess-input",
            "type": "input",
            "element": {
                "type": "plain_text_input",
                "action_id": "submit-guess",
            },
            "label": {"type": "plain_text", "text": "Guess", "emoji": True},
        }
    )

    return blocks


@app.action("submit-guess")
async def handle_some_action(ack, body, logger, client):
    await ack()

    value = body["actions"][0]["value"]
    message_ts = body["container"]["message_ts"]
    channel = body["container"]["channel_id"]

    game = await db.Game.get_or_create(
        channel_id=channel, thread_ts=message_ts, day=DAY
    )

    if match := REGEX.match(value):
        word = match.group("guess").lower()
        user_id = body["user"]["id"]

        await game.add_guess(word=word, user_id=user_id)

        user_info = await client.users_info(user=user_id)
        profile = user_info.data["user"]["profile"]["image_24"]

        await client.chat_update(
            channel=channel,
            ts=message_ts,
            blocks=await get_thread_blocks(game),
        )


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
                            "text": f"Semantle day {DAY} - April 16th",
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
            await db.Game.new(channel_id=channel, thread_ts=resp["ts"], day=DAY)


async def main() -> None:
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
