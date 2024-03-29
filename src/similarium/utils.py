from __future__ import annotations

import datetime as dt
import math
import random
from typing import TYPE_CHECKING, Optional

from similarium.target_words import target_words

if TYPE_CHECKING:
    from similarium.models import Game, SimilarityRange

Vector = list[float]

BASE_DATE = dt.datetime(2022, 5, 6, tzinfo=dt.timezone.utc)
CELEBRATE_EMOJIS = [
    ":sparkles:",
    ":medal:",
    ":trophy:",
    ":partying_face:",
    ":tada:",
    ":champagne:",
    ":confetti_ball:",
    ":dancer:",
    ":man_dancing:",
    ":star2:",
    ":star-struck:",
    ":clap:",
    ":raised_hands:",
    ":muscle:",
    ":mechanical_arm:",
]


def dot(A: Vector, B: Vector) -> float:
    return sum(a * b for a, b in zip(A, B))


def norm(vec: Vector) -> float:
    return math.sqrt(dot(vec, vec))


def cos_sim(vec1: list[float], vec2: list[float]) -> float:
    return dot(vec1, vec2) / (norm(vec1) * norm(vec2))


def get_similarity(vec1: list[float], vec2: list[float]) -> float:
    return cos_sim(vec1, vec2) * 100


def get_celeration_emoji() -> str:
    return random.choice(CELEBRATE_EMOJIS)


PARTIAL_EMOJIS = 8
P = [f":p{i}:" for i in range(0, PARTIAL_EMOJIS + 1)]


def get_custom_progress_bar(amount: int, total: int, width: int) -> str:
    """Generate a progress bar using custom emojis from :p0: to :p8:

    :p0: is a transparent emoji with :p1: up to :p8: filling in from the left
    side, 16 pixels out of 128 at each step

    :p1: is 16/128 pixels
    :p2: is 32/128 pixels
    ...
    :p7: is 112/128 pixels
    :p8: is 128/128 pixels

    The width is the number of emojis to use to represent the total amount

    The first emoji is only :p0: when amount is 0, no matter the total.
    When amount is 1, the first emoji will be at least :p1:.

    The last emoji is never :p8:, unless the amount is equal to total.
    """
    if width < 1:
        raise ValueError("Width needs to be at least 1")

    # Handle full and empty bars
    if amount >= total:
        return P[8] * width
    if amount <= 0:
        return P[0] * width

    # Calculate how many sections there are. Each "width" can have the length
    # of PARTIAL_EMOJIS, subtracting 1 to account for the final state of amount
    # == total
    section_count = (PARTIAL_EMOJIS * width) - 1

    # Calculate how large each section is, which are all values except the last
    # one, hence subtract 1 from total
    section_size = (total - 1) / section_count

    # Calculate how many "sections" are filled
    filled_sections = math.ceil(round(amount / section_size, 8))

    # Calculate how many filled emojis we need first
    full_emojis = filled_sections // PARTIAL_EMOJIS

    # Calculate how many sections are needed for the partial
    partial_units = filled_sections % PARTIAL_EMOJIS

    # Put together the bar
    output = P[8] * full_emojis
    output += P[partial_units]
    output += P[0] * (width - full_emojis - 1)

    return output


def get_secret(channel: str, day: int) -> str:
    """Get the secret of the day for a channel

    The target words are randomised for each channel, with the channel_id as
    the random seed. The day is then used to get the secret words from that
    channel specific list.
    """
    rng = random.Random(channel)
    channel_secrets = rng.sample(target_words, len(target_words))
    return channel_secrets[day % len(target_words)]


def get_puzzle_date(puzzle_number: int) -> str:
    """Get the puzzle date based on puzzle number

    Puzzle number #0 will be on the BASE_DATE

    TODO: Deal with time zones
    """
    date = BASE_DATE + dt.timedelta(days=puzzle_number)
    return date.strftime("%A %B %-d")


def get_puzzle_number(date: Optional[dt.datetime] = None) -> int:
    """Return what puzzle number is today

    Puzzle number is the number of days since BASE_DATE

    TODO: Deal with timezones
    """
    if date is None:
        date = dt.datetime.now(dt.timezone.utc)
    return (date - BASE_DATE).days


def expand_bfloat(vec: bytes, half_length: int = 600) -> bytes:
    """
    expand truncated float32 to float32
    """
    if len(vec) == half_length:
        vec = b"".join((b"\00\00" + bytes(pair)) for pair in zip(vec[::2], vec[1::2]))
    return vec


def timestamp_ms() -> int:
    """Return the elapsed milliseconds since the BASE_DATE

    This is just used to order guesses in chronological order
    """
    now = dt.datetime.now(dt.timezone.utc)
    delta = now - BASE_DATE

    return int(delta.total_seconds() * 1000)  # Milliseconds


def get_header_text(game: Game) -> str:
    """Generate header text of a game for a Slack message"""
    return f"{game.date} - Puzzle number {game.puzzle_number}"


def get_header_body(game: Game) -> str:
    """Generate header body of a game for Slack message"""

    sr: SimilarityRange = game.similarity_range

    return (
        f"The nearest word has a similarity of {sr.top*100:.02f}, "
        f"the tenth-nearest has a similarity of {sr.top10*100:.02f} and "
        f"the one thousandth nearest word has a similarity of {sr.rest*100:.02f}."
    )


def get_seconds_left_of_hour() -> float:
    """Calculate how many seconds left of the current hour"""
    now = dt.datetime.now(dt.timezone.utc)
    next_hour = (now + dt.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    return (next_hour - now).total_seconds()
