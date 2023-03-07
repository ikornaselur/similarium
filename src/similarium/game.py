from slack_sdk.errors import SlackApiError

from similarium import db
from similarium.exceptions import (
    AccountInactive,
    ChannelNotFound,
    GameNotRegistered,
    NotInChannel,
)
from similarium.logging import logger
from similarium.models import Channel, Game
from similarium.models.similarity_range import SimilarityRange
from similarium.slack import app, get_bot_token_for_team, get_thread_blocks
from similarium.utils import (
    get_header_body,
    get_header_text,
    get_puzzle_date,
    get_puzzle_number,
)


async def start_game(channel_id: str):
    puzzle_number = get_puzzle_number()
    puzzle_date = get_puzzle_date(puzzle_number)

    game = Game.new(
        channel_id=channel_id,
        thread_ts="",
        puzzle_number=puzzle_number,
        puzzle_date=puzzle_date,
    )
    async with db.session() as s:
        similarity_range = await SimilarityRange.get(game.secret, session=s)
        if similarity_range is None:
            raise Exception(f"Unable to find similarity range for {game.secret=}")
        game.similarity_range = similarity_range

    header_text = get_header_text(game)
    header_body = get_header_body(game)

    async with db.session() as session:
        channel = await Channel.by_id(channel_id, session=session)

    if channel is None:
        logger.warning("Need to subscribe to a game before manual trigger")
        raise GameNotRegistered()

    try:
        resp = await app.client.chat_postMessage(
            token=get_bot_token_for_team(channel.team_id),
            text=header_text,
            channel=channel_id,
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": header_text,
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": header_body,
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
                        "min_length": 2,
                    },
                    "label": {"type": "plain_text", "text": "Guess", "emoji": True},
                },
            ],
        )
    except SlackApiError as e:
        response = e.response.data
        logger.error("Error posting game", exc_info=e)
        match response.get("error"):
            case "channel_not_found":
                # Likely private channel
                raise ChannelNotFound()
            case "not_in_channel":
                # Needs to be invited
                raise NotInChannel()
            case "account_inactive":
                # Similarium user has been removed from the team
                raise AccountInactive()
        return

    game.thread_ts = resp["ts"]  # type: ignore

    async with db.session() as s:
        s.add(game)
        await s.commit()


async def update_game(game: Game) -> None:
    await app.client.chat_update(
        token=get_bot_token_for_team(game.channel.team_id),
        channel=game.channel_id,
        ts=game.thread_ts,
        text="Update to todays game",
        blocks=await get_thread_blocks(game.id),
    )


async def end_game(channel_id: str) -> None:
    """End game if there is one active"""
    async with db.session() as session:
        active_games = await Game.get_active_in_channel(channel_id, session=session)
        logger.debug(f"Got {len(active_games)} active games to end in {channel_id=}")

        for game in active_games:
            game.active = False  # type: ignore
            await session.commit()

            await app.client.chat_update(
                token=get_bot_token_for_team(game.channel.team_id),
                channel=game.channel_id,
                ts=game.thread_ts,
                text="Update to todays game",
                blocks=await get_thread_blocks(game.id),
            )
