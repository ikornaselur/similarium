from __future__ import annotations

from sqlalchemy.ext.asyncio.session import AsyncSession

from semantle_slack_bot.models import Game, User


async def test_game_add_guess_adds_guess(db, game_id: int, user_id: str) -> None:
    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        assert game.guesses == []

        await game.add_guess(session=session, word="berry", user_id=user_id)

        assert len(game.guesses) == 1
        assert game.guesses[0].word == "berry"


async def test_game_add_guess_handles_duplicates(
    db, game_id: int, user_id: str
) -> None:
    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        assert game.guesses == []

        await game.add_guess(session=session, word="berry", user_id=user_id)

        assert len(game.guesses) == 1

        await game.add_guess(session=session, word="berry", user_id=user_id)

        assert len(game.guesses) == 1


async def test_game_add_multiple_guesses(db, game_id: int, user_id: str) -> None:
    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        assert game.guesses == []

        await game.add_guess(session=session, word="berry", user_id=user_id)
        await session.commit()

    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        await game.add_guess(session=session, word="grape", user_id=user_id)
        await session.commit()

    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        await game.add_guess(session=session, word="peach", user_id=user_id)
        await session.commit()

    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        assert len(game.guesses) == 3


async def test_game_ends_with_winning_words(db, game_id: int, user_id: str) -> None:
    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        await game.add_guess(session=session, word="berry", user_id=user_id)
        await game.add_guess(session=session, word="grape", user_id=user_id)
        await game.add_guess(session=session, word="peach", user_id=user_id)
        await session.commit()

        assert game.active

        await game.add_guess(session=session, word=game.secret, user_id=user_id)
        await session.commit()

        assert not game.active
