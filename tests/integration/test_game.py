from __future__ import annotations

from similarium.models import Game, Guess, User
from similarium.models.game_user_winner_association import GameUserWinnerAssociation


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


async def test_game_add_question_word(db, game_id: int, user_id: str) -> None:
    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        await game.add_guess(session=session, word="cherries", user_id=user_id)
        await session.commit()

        assert len(game.guesses) == 1
        guess: Guess = game.guesses[0]

        assert guess.percentile == 0
        assert guess.similarity > game.similarity_range.rest


async def test_game_add_guess_secret_adds_user_to_winner(
    db, game_id: int, user_id: str
) -> None:
    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        user = await User.by_id(user_id, session=session)
        assert user is not None

        assert user not in game.winners

        await game.add_guess(session=session, word=game.secret, user_id=user_id)
        await session.commit()

        assert len(game.winners) == 1

        winner: GameUserWinnerAssociation = game.winners[0]

        assert winner.game_id == game_id
        assert winner.user_id == user_id
        assert winner.guess_idx == 1
