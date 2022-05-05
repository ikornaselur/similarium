from sqlalchemy.ext.asyncio.session import AsyncSession

from semantle_slack_bot.models import Game


async def test_create_game_requires_fields(
    session: AsyncSession
) -> None:
    game = Game()

    session.add(game)

    await session.commit()
