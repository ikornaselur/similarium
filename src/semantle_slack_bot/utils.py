import math
import random

from semantle_slack_bot.target_words import target_words

Vector = list[float]


def dot(A: Vector, B: Vector) -> float:
    return sum(a * b for a, b in zip(A, B))


def norm(vec: Vector) -> float:
    return math.sqrt(dot(vec, vec))


def cos_sim(vec1: list[float], vec2: list[float]) -> float:
    return dot(vec1, vec2) / (norm(vec1) * norm(vec2))


def get_similarity(vec1: list[float], vec2: list[float]) -> float:
    return cos_sim(vec1, vec2) * 100


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
    """
    if width < 1:
        raise ValueError("Width needs to be at least 1")

    # Handle full and empty bars
    if amount >= total:
        return P[8] * width
    if amount <= 0:
        return P[0] * width

    # Calculate how many units each emoji will be
    # We will round down, making the last space potentially slightly longer,
    # which is fine if we handle the full amount properly
    emoji_units = total // width

    # Calculate how many full emojis we need
    full_emojis = amount // emoji_units

    output = P[8] * full_emojis

    # Calculate width of partial emoji
    partial_units = amount % emoji_units
    partial_emoji = P[math.floor((partial_units / emoji_units) * PARTIAL_EMOJIS)]

    output += partial_emoji

    # Fill in the empty emojis
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
    return channel_secrets[day]
