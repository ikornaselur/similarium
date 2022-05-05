import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

from semantle_slack_bot.models import Game


@pytest.mark.skip(reason="Just playing around")
async def test_create_game_requires_fields(
    session: AsyncSession
) -> None:
    game = Game()

    session.add(game)
