from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from semantle_slack_bot.models import Game, User


async def test_game_add_guess_adds_guess(
    session: AsyncSession, game: Game, user: User
) -> None:
    assert game.guesses == []

    await game.add_guess(session=session, word="berry", user_id=user.id)

    assert len(game.guesses) == 1
    assert game.guesses[0].word == "berry"


async def test_game_add_guess_handles_duplicates(
    session: AsyncSession, game: Game, user: User
) -> None:
    assert game.guesses == []

    await game.add_guess(session=session, word="berry", user_id=user.id)

    assert len(game.guesses) == 1

    await game.add_guess(session=session, word="berry", user_id=user.id)

    assert len(game.guesses) == 1
