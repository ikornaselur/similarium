import json
import logging
import os
import random
import re
from functools import lru_cache
from pathlib import Path
from typing import Awaitable, Callable

from rich.logging import RichHandler
from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from semantle_slack_bot.event_types import Body
from semantle_slack_bot.model import get_model
from semantle_slack_bot.utils import get_similarity

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler()],
)
app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])

REGEX = re.compile(r"^\!(?P<guess>[a-z]+)$")

with open(Path(__file__).parent / "target_words.json", "r") as f:
    target_words = json.load(f)

GUESSES = {}


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


@app.event("message")
async def message(
    body: Body, logger: logging.Logger, say: Callable[[str], Awaitable[None]]
) -> None:
    event = body["event"]
    channel = event["channel"]
    if channel not in GUESSES:
        GUESSES[channel] = {}
    day = 1
    secret = get_secret(channel, day=day)

    secret_vec = get_model(secret, secret)["vec"]

    if event["type"] == "message":
        message = event.get("text")

        if message and (match := REGEX.match(message)):
            guess = match.group("guess")
            result = get_model(secret, guess)
            if percentile := result.get("percentile"):
                closeness = f"{get_progress_bar(percentile, 1000)} {percentile}/1000"
            else:
                closeness = "cold"

            similarity = get_similarity(secret_vec, result["vec"])

            logger.info(
                f"Got {guess=} which has {similarity=} {closeness=} (to {secret=})"
            )

            await say(f"{guess:<10} {similarity:<8.02f} {closeness}")


async def main() -> None:
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    await handler.start_async()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
