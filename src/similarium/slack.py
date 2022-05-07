import math
import os
from typing import Literal, Optional, TypedDict

from slack_bolt.app.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from similarium.config import config
from similarium.models import Game, Guess
from similarium.utils import get_custom_progress_bar, get_header_text

SPACE = " "
TOP_GUESSES_TO_SHOW = 15
LATEST_GUESSES_TO_SHOW = 3

app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])
web_client = AsyncWebClient(token=os.environ["SLACK_BOT_TOKEN"])


class TextBlock(TypedDict):
    type: Literal["plain_text"]
    text: str
    emoji: bool


class HeaderBlock(TypedDict):
    type: Literal["header"]
    text: TextBlock


class DividerBlock(TypedDict):
    type: Literal["divider"]


class ElementBlock(TypedDict):
    type: Literal["plain_text_input"]
    action_id: str


class LabelBlock(TypedDict):
    type: Literal["plain_text"]
    text: str
    emoji: bool


class InputBlock(TypedDict):
    type: Literal["input"]
    dispatch_action: bool
    block_id: str
    element: ElementBlock
    label: LabelBlock


class MarkdownTextBlock(TypedDict):
    type: Literal["mrkdwn"]
    text: str


class MarkdownSectionBlock(TypedDict):
    type: Literal["section"]
    text: MarkdownTextBlock


class ProfileBlock(TypedDict):
    type: Literal["image"]
    image_url: str
    alt_text: str


class GuessContextBlock(TypedDict):
    type: Literal["context"]
    block_id: str
    elements: tuple[ProfileBlock, MarkdownTextBlock, MarkdownTextBlock]


class SlackGame:
    """A slack game instance"""

    _game: Game
    input_action_id: str = "submit-guess"
    input_block_id: str = "guess-input"

    def __init__(self, game: Game) -> None:
        self._game = game

    @property
    def header(self) -> HeaderBlock:
        """The header of the game message

        The header will state the Similarium puzzle number it is and the date
        """
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": get_header_text(self._game.puzzle_number, self._game.date),
                "emoji": True,
            },
        }

    @property
    def divider(self) -> DividerBlock:
        return {"type": "divider"}

    @property
    def input(self) -> InputBlock:
        return {
            "type": "input",
            "dispatch_action": True,
            "block_id": self.input_block_id,
            "element": {
                "type": "plain_text_input",
                "action_id": self.input_action_id,
            },
            "label": {
                "type": "plain_text",
                "text": "Guess",
                "emoji": True,
            },
        }

    def markdown_section(self, text) -> MarkdownSectionBlock:
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        }

    async def finished(
        self, *, session: AsyncSession
    ) -> Optional[MarkdownSectionBlock]:
        top_guesses = await self._game.top_guesses(1, session=session)
        top_guess = None
        if (
            not len(top_guesses)
            or (top_guess := top_guesses[0]).word != self._game.secret
        ):
            text_lines = [
                ":cry: *No one found the word!*",
                f"The secret word of the day was: *{self._game.secret}*",
            ]
            if top_guess is not None:
                text_lines.append(
                    f"The closest guess was made by <@{top_guess.user_id}>!"
                )
            text = "\n".join(text_lines)
        else:
            text = "\n".join(
                [
                    ":tada: *The secret has been found!* :tada:",
                    f"The secret word of the day was: *{self._game.secret}*",
                    f"The winning guess was made by <@{top_guess.user_id}>!",
                ]
            )

        return self.markdown_section(text=text)

    def guess_context(self, guess: Guess, base_id: str) -> GuessContextBlock:
        closeness = _closeness(guess)

        if guess.percentile == config.rules.similarity_count:
            # It's the secret word!
            # TODO: check guess.word == guess.game.secret? Add guess.is_secret?
            guess_info = (
                f"{_idx(guess)}{_similarity(guess)}:tada: {_word(guess)} :tada:"
            )
        else:
            guess_info = f"{_idx(guess)}{_similarity(guess)}{_word(guess)}"

        return {
            "type": "context",
            "block_id": f"guess-{base_id}-{guess.word}",
            "elements": (
                {
                    "type": "image",
                    "image_url": guess.user.profile_photo,
                    "alt_text": "profile",
                },
                {"type": "mrkdwn", "text": closeness},
                {"type": "mrkdwn", "text": guess_info},
            ),
        }


def _closeness(guess: Guess) -> str:
    similarity_count = config.rules.similarity_count
    if guess.percentile:
        if guess.percentile < 10:
            percentile = f"{SPACE * 7}{guess.percentile}"
        elif guess.percentile < 100:
            percentile = f"{SPACE * 4}{guess.percentile}"
        elif guess.percentile < 1000:
            percentile = f"{SPACE * 2}{guess.percentile}"
        else:
            percentile = f"{guess.percentile}"
        progress_bar = get_custom_progress_bar(
            guess.percentile, similarity_count, width=6
        )
        return f"{progress_bar} {percentile}/{similarity_count}"
    return f"{get_custom_progress_bar(0, similarity_count, width=6)}{SPACE * 14}cold"


def _idx(guess: Guess) -> str:
    # Magic!
    # Add 6 spaces for idx < 10, 4 spaces for idx < 100, else 2 spaces
    # TODO: over 100 seems to not work
    postfix = max(2 - int(math.log10(guess.idx)), 1) * (SPACE * 2)

    return f"{guess.idx}.{postfix}"


def _similarity(guess: Guess) -> str:
    prefix = ""
    if guess.similarity >= 0:
        # Account for negative symbol
        prefix += SPACE * 2
    if abs(guess.similarity) < 10:
        # Account for small number
        prefix += SPACE * 2

    return f"_{prefix}{guess.similarity:.02f}_       "


def _word(guess: Guess) -> str:
    return f"*{guess.word}*"


async def get_thread_blocks(session: AsyncSession, game: Game) -> list:
    slack_game = SlackGame(game)
    blocks = [
        slack_game.header,
        await slack_game.finished(session=session) if not game.active else None,
        slack_game.divider,
    ]
    if game.active:
        blocks.extend(
            [
                slack_game.markdown_section("*Latest guesses*"),
                *[
                    slack_game.guess_context(guess, base_id="latest")
                    for guess in await game.latest_guesses(
                        LATEST_GUESSES_TO_SHOW, session=session
                    )
                ],
            ]
        )
    blocks.extend(
        [
            slack_game.markdown_section("*Top guesses*"),
            *[
                slack_game.guess_context(guess, base_id="top")
                for guess in await game.top_guesses(
                    TOP_GUESSES_TO_SHOW, session=session
                )
            ],
            slack_game.input if game.active else None,
        ]
    )

    return [b for b in blocks if b is not None]
