import heapq
import json
import logging
import os
import random
import re
from functools import lru_cache
from pathlib import Path
from typing import Awaitable, Callable, Optional

from rich.logging import RichHandler
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from semantle_slack_bot.event_types import Body
from semantle_slack_bot.model import get_model
from semantle_slack_bot.utils import get_custom_progress_bar, get_similarity

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler()],
)
app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])

REGEX = re.compile(r"^(?P<guess>[A-Za-z]+)$")

with open(Path(__file__).parent / "target_words.json", "r") as f:
    target_words = json.load(f)

Say = Callable[[str], Awaitable[dict]]
Guess = tuple[float, Optional[int], int, str, str]

TOP_GUESSES_TO_SHOW = 25
LATEST_GUESSES_TO_SHOW = 3

GUESSES: dict[str, dict[str, list[Guess]]] = {}
GAMES = {}


@lru_cache()
def get_secret(channel: str, day: int) -> str:
    """Get the secret of the day for a channel

    The target words are randomised for each channel, with the channel_id as
    the random seed. The day is then used to get the secret words from that
    channel specific list.
    """
    rng = random.Random(channel)
    rng.shuffle
    channel_secrets = rng.sample(target_words, len(target_words))
    return channel_secrets[day]


def get_progress_bar(amount: int, total: int) -> str:
    green_blocks_count = int(round(amount / total * 100, -1)) // 10
    green_blocks = f"{':large_green_square:' * green_blocks_count}"
    white_blocks = f"{':white_square:' * (10 - green_blocks_count)}"
    return f"{green_blocks}{white_blocks}"


def get_thread_body(guesses: list[Guess]) -> str:
    top_guesses = heapq.nlargest(TOP_GUESSES_TO_SHOW, guesses)
    latest_guesses = heapq.nlargest(
        LATEST_GUESSES_TO_SHOW,
        [(line[2], line) for line in guesses],
    )
    message = "** Game 13 - April 20th **\n"

    def guess_line(guess: Guess) -> str:
        similarity, percentile, idx, word, user = guess
        if percentile:
            closeness = f"{get_progress_bar(percentile, 1000)} {percentile}/1000"
        else:
            closeness = "cold"

        return f"{idx:>3}. {word:<10} {similarity:<8.02f} {closeness} <@{user}>\n"

    # Show the latest guesses
    message += "Latest guesses:\n"
    for _, guess in latest_guesses:
        message += guess_line(guess)

    message += "--------\n"

    for guess in top_guesses:
        message += guess_line(guess)

    return message


def get_thread_blocks(guesses: list[Guess]) -> list:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Semantle day 2 - April 16th",
                "emoji": True,
            },
        },
        {"type": "divider"},
    ]

    top_guesses = heapq.nlargest(TOP_GUESSES_TO_SHOW, guesses)
    latest_guesses = heapq.nlargest(
        LATEST_GUESSES_TO_SHOW,
        [(line[2], line) for line in guesses],
    )

    def guess_line(guess: Guess) -> tuple[str, str]:
        similarity, percentile, idx, word, user = guess
        if percentile:
            closeness = (
                f"{get_custom_progress_bar(percentile, 1000, width=6)} {percentile}/1000"
            )
        else:
            closeness = "cold"

        return (
            f"`{idx:>3}. {similarity:<6.02f} {word:<12} <@{user}>`\n",
            f"{closeness}\n",
        )

    latest_guesses_left_col = f"*Latest {LATEST_GUESSES_TO_SHOW} guesses*\n"
    latest_guesses_right_col = ":p0:\n"
    # Show the latest guesses
    for _, guess in latest_guesses:
        left, right = guess_line(guess)
        latest_guesses_left_col += left
        latest_guesses_right_col += right

    blocks.append(
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": latest_guesses_left_col},
                {"type": "mrkdwn", "text": latest_guesses_right_col},
            ],
        }
    )
    blocks.append({"type": "divider"})

    top_guesses_left_col = f"*Top {TOP_GUESSES_TO_SHOW} guesses*\n"
    top_guesses_right_col = ":p0:\n"

    for guess in top_guesses:
        left, right = guess_line(guess)
        top_guesses_left_col += left
        top_guesses_right_col += right

    blocks.append(
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": top_guesses_left_col},
                {"type": "mrkdwn", "text": top_guesses_right_col},
            ],
        }
    )

    return blocks


@app.event("message")
async def message(body: Body, logger: logging.Logger, say: Say, client, ack) -> None:
    async def _start_new_game() -> None:
        resp = await say("Starting a new game!")
        if resp.get("ok") is True:
            logger.info("Starting a new game")
            GAMES[resp["ts"]] = {
                "guesses": [],
            }

    await ack()

    event = body["event"]
    channel = event["channel"]
    if channel not in GUESSES:
        GUESSES[channel] = {}
    day = 4
    secret = get_secret(channel, day=day)
    secret_vec = get_model(secret, secret)["vec"]

    if event["type"] == "message":
        message = event.get("text")
        thread_ts = event.get("thread_ts")

        if message == "!start":
            await _start_new_game()
        elif (
            thread_ts
            and message
            and thread_ts in GAMES
            and (match := REGEX.match(message))
        ):
            guess = match.group("guess").lower()
            logger.info(f"Guess in a game: {guess}")

            result = get_model(secret, guess)
            if "vec" not in result:
                logger.error("Invalid word")
                return

            percentile = result.get("percentile")
            similarity = get_similarity(secret_vec, result["vec"])

            heapq.heappush(
                GAMES[thread_ts]["guesses"],
                (
                    similarity,
                    percentile,
                    len(GAMES[thread_ts]["guesses"]) + 1,
                    guess,
                    event["user"],
                ),
            )

            await client.chat_update(
                channel=event["channel"],
                ts=thread_ts,
                blocks=get_thread_blocks(GAMES[thread_ts]["guesses"]),
            )


async def main() -> None:
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
