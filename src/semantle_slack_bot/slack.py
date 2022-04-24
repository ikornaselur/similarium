from typing import Literal, TypedDict

from semantle_slack_bot import db
from semantle_slack_bot.utils import get_custom_progress_bar


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
    elements: tuple[ProfileBlock, MarkdownTextBlock, MarkdownTextBlock]


class SlackGame:
    """A slack game instance"""

    _game: db.Game
    input_action_id: str = "submit-guess"
    input_block_id: str = "guess-input"

    def __init__(self, game: db.Game) -> None:
        self._game = game

    @property
    def header(self) -> HeaderBlock:
        """The header of the game message

        The header will state the Semantle puzzle number it is and the date
        """
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": (
                    f"Semantle puzzle #{self._game.puzzle_number}"
                    f" - {self._game.date}"
                ),
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

    def guess_context(self, guess: db.Guess) -> GuessContextBlock:
        if guess.percentile:
            closeness = (
                f"{get_custom_progress_bar(guess.percentile, 1000, width=6)} "
                f"{guess.percentile:<03}/1000"
            )
        else:
            closeness = f"{get_custom_progress_bar(0, 1000, width=6)} ~~~/1000"

        guess_info = (
            f"{guess.idx:>2}.   _{guess.similarity:<6.02f}_"
            f"       *{guess.word:<12}*"
        )
        return {
            "type": "context",
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
