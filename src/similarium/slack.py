import math
from typing import Literal, Optional, TypedDict

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings
from sqlalchemy.ext.asyncio.session import AsyncSession

from similarium import db
from similarium.config import config
from similarium.logging import logger
from similarium.models import Game, Guess
from similarium.models.game_user_hint_association import GameUserHintAssociation
from similarium.models.stores import (
    AsyncSQLAlchemyInstallationStore,
    AsyncSQLAlchemyOAuthStateStore,
)
from similarium.utils import get_custom_progress_bar, get_header_body, get_header_text

SPACE = " "
TOP_GUESSES_TO_SHOW = 15
LATEST_GUESSES_TO_SHOW = 3

installation_store = AsyncSQLAlchemyInstallationStore(
    client_id=config.slack.client_id,
    metadata=db.Base.metadata,
    logger=logger,
)
oauth_state_store = AsyncSQLAlchemyOAuthStateStore(
    expiration_seconds=600,
    metadata=db.Base.metadata,
    logger=logger,
)
oauth_settings = AsyncOAuthSettings(
    client_id=config.slack.client_id,
    client_secret=config.slack.client_secret,
    scopes=config.slack.scopes,
    installation_store=installation_store,
    state_store=oauth_state_store,
)

if config.slack.dev_mode:
    app = AsyncApp(token=config.slack.bot_token)
else:
    app = AsyncApp(
        signing_secret=config.slack.signing_secret,
        installation_store=installation_store,
        oauth_settings=oauth_settings,
    )


async def get_bot_token_for_team(team_id: str) -> str:
    if config.slack.dev_mode:
        return config.slack.bot_token

    installation = await installation_store.async_find_installation(
        enterprise_id=None, team_id=team_id, is_enterprise_install=False
    )
    if installation is None:
        # XXX
        raise Exception("Unable to find installation")

    if installation.bot_token is None:
        raise Exception("No bot_token on installation")

    return installation.bot_token


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
    min_length: int


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


class HintSeekerContextBlock(TypedDict):
    type: Literal["context"]
    block_id: str
    elements: tuple[ProfileBlock, MarkdownTextBlock]


class HintContextBlock(TypedDict):
    type: Literal["context"]
    elements: tuple[MarkdownTextBlock]


class ButtonBlock(TypedDict):
    type: Literal["button"]
    text: TextBlock
    value: str
    action_id: str


class ButtonsActionBlock(TypedDict):
    type: Literal["actions"]
    elements: list[ButtonBlock]


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
                "text": get_header_text(self._game),
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
                "min_length": 2,
            },
            "label": {
                "type": "plain_text",
                "text": "Guess",
                "emoji": True,
            },
        }

    @property
    def hint_text(self) -> HintContextBlock:
        return {
            "type": "context",
            "elements": (
                {
                    "type": "mrkdwn",
                    "text": (
                        f"It's been over {config.openai.hints.threshold} guesses"
                        " without finding the secret! Want a hint? ChatGPT can give"
                        " you one!\nIf you request a hint, only you will see it, but"
                        " everyone will know that you got it!"
                    ),
                },
            ),
        }

    @property
    def hint_button(self) -> ButtonsActionBlock:
        return {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Get hint",
                        "emoji": True,
                    },
                    "value": "hint",
                    "action_id": "hint",
                }
            ],
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
        winners = self._game.get_winners_messages()

        secret_found = len(winners) > 0

        if self._game.active and not secret_found:
            return None

        if self._game.active:
            # Game still active with a found secret
            return self.markdown_section(
                text="\n".join([":tada: *The secret has been found!* :tada:"] + winners)
            )

        # Game has been finished, set final state
        if secret_found:
            return self.markdown_section(
                text="\n".join(
                    [
                        ":tada: *The secret was found!* :tada:",
                        f"The secret word of the day was: *{self._game.secret}*",
                    ]
                    + winners
                )
            )

        # No one found the secret
        text_lines = [
            ":cry: *No one found the word!*",
            f"The secret word of the day was: *{self._game.secret}*",
        ]

        top_guesses = await self._game.top_guesses(1, session=session)
        if len(top_guesses) > 0:
            text_lines.append(
                f"The closest guess was made by <@{top_guesses[0].user_id}>!"
            )
        return self.markdown_section(text="\n".join(text_lines))

    def guess_context(self, guess: Guess, base_id: str) -> GuessContextBlock:
        closeness = _closeness(guess)

        if guess.is_secret:
            if guess.game.active:
                # Keep it secret still!
                guess_info = (
                    f"{_idx(guess)}{_similarity(guess)}:see_no_evil: _Secret will be"
                    " revealed at the end_ :see_no_evil:"
                )
            else:
                guess_info = (
                    f"{_idx(guess)}{_similarity(guess)}:tada: {_word(guess)} :tada:"
                )
        else:
            guess_info = f"{_idx(guess)}{_similarity(guess)}{_word(guess)}"

        if base_id == "latest":
            user = guess.latest_guess_user
        else:
            user = guess.user

        return {
            "type": "context",
            "block_id": f"guess-{base_id}-{guess.word}",
            "elements": (
                {
                    "type": "image",
                    "image_url": user.profile_photo,
                    "alt_text": user.username,
                },
                {"type": "mrkdwn", "text": closeness},
                {"type": "mrkdwn", "text": guess_info},
            ),
        }

    def hint_seeker_context(
        self, hint_seeker: GameUserHintAssociation
    ) -> HintSeekerContextBlock:
        return {
            "type": "context",
            "block_id": f"hint-seeker-{hint_seeker.user.username}",
            "elements": (
                {
                    "type": "image",
                    "image_url": hint_seeker.user.profile_photo,
                    "alt_text": hint_seeker.user.username,
                },
                {
                    "type": "mrkdwn",
                    "text": (
                        f"<@{hint_seeker.user.id}> saw the hint at guess"
                        f" {hint_seeker.guess_idx}"
                    ),
                },
            ),
        }


def _closeness(guess: Guess) -> str:
    similarity_count = config.rules.similarity_count
    # Similarity on the guess is stored as a value up to 100, while similarity
    # range is up to 1.0
    min_similarity = guess.game.similarity_range.rest * 100

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
    elif guess.similarity > min_similarity:
        # We have a ???? word
        similarity = "????"
    else:
        similarity = "cold"

    progress_bar = get_custom_progress_bar(0, similarity_count, width=6)
    return f"{progress_bar}{SPACE * 14}{similarity}"


def _idx(guess: Guess) -> str:
    # Magic!
    # Add 6 spaces for idx < 10, 4 spaces for idx < 100, else 2 spaces
    postfix = max(3 - int(math.log10(guess.idx)), 1) * (SPACE * 2)

    return f"{guess.idx}.{postfix}"


def _similarity(guess: Guess) -> str:
    prefix = ""
    if guess.similarity >= 0:
        # Account for negative symbol
        prefix += SPACE * 1
    if abs(guess.similarity) < 10:
        # Account for small number
        prefix += SPACE * 2

    return f"{prefix}_{guess.similarity:.02f}_{SPACE * 7}"


def _word(guess: Guess) -> str:
    return f"*{guess.word}*"


async def get_thread_blocks(game_id: int, channel_id: str) -> list:
    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        if game is None:
            raise Exception("???")

        slack_game = SlackGame(game)

        blocks = [
            slack_game.header,
            slack_game.markdown_section(get_header_body(game)),
            await slack_game.finished(session=session),
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

        if (
            channel_id in config.openai.channel_ids
            and len(game.guesses) >= config.openai.hints.threshold
        ):
            # Time to offer hints!
            blocks.extend(
                [
                    slack_game.markdown_section("*Hints*"),
                    slack_game.hint_text,
                    slack_game.hint_button,
                ]
            )
            if game.hint_seekers:
                blocks.extend(
                    [
                        slack_game.hint_seeker_context(hint_seeker)
                        for hint_seeker in game.hint_seekers
                    ]
                )

        return [b for b in blocks if b is not None]
