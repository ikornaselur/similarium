from slack_sdk.errors import SlackApiError

from similarium import db
from similarium.exceptions import ChannelNotFound, NotInChannel
from similarium.logging import logger
from similarium.models import Game
from similarium.slack import get_thread_blocks, web_client
from similarium.utils import get_header_text, get_puzzle_date, get_puzzle_number


async def start_game(channel_id: str):
    puzzle_number = get_puzzle_number()
    puzzle_date = get_puzzle_date(puzzle_number)
    header_text = get_header_text(puzzle_number, puzzle_date)

    try:
        resp = await web_client.chat_postMessage(
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
    except SlackApiError as e:
        response = e.response.data
        match response.get("error"):
            case "channel_not_found":
                # Likely private channel
                raise ChannelNotFound()
            case "not_in_channel":
                # Needs to be invited
                raise NotInChannel()
        logger.error("Error posting game", exc_info=e)
        return
    game = Game.new(
        channel_id=channel_id,
        thread_ts=resp["ts"],
        puzzle_number=puzzle_number,
        puzzle_date=puzzle_date,
    )
    async with db.session() as s:
        s.add(game)
        await s.commit()


async def update_game(game: Game) -> None:
    await web_client.chat_update(
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
            # TODO: Update message on slack...
            game.active = False
            await session.commit()

            await web_client.chat_update(
                channel=game.channel_id,
                ts=game.thread_ts,
                text="Update to todays game",
                blocks=await get_thread_blocks(game),
            )
