from __future__ import annotations

import pytest

from similarium.exceptions import UserAlreadyWon
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


async def test_game_add_guess_secret_adds_second_user_to_winner(
    db,
    game_id: int,
    user_id: str,
    user_id_2: str,
) -> None:
    async with db.session() as session:
        game = await Game.by_id(game_id, session=session)
        assert game is not None

        user = await User.by_id(user_id, session=session)
        assert user is not None

        assert user not in game.winners
        assert user_id_2 not in game.winners

        await game.add_guess(session=session, word="cherries", user_id=user_id)
        await session.commit()

        await game.add_guess(session=session, word=game.secret, user_id=user_id)
        await session.commit()

        assert len(game.winners) == 1

        await game.add_guess(session=session, word=game.secret, user_id=user_id_2)
        await session.commit()

        assert len(game.winners) == 2

        winner: GameUserWinnerAssociation = game.winners[0]

        assert winner.game_id == game_id
        assert winner.user_id == user_id

        assert winner.guess_idx == 2

        winner: GameUserWinnerAssociation = game.winners[1]

        assert winner.game_id == game_id
        assert winner.user_id == user_id_2

        assert winner.guess_idx == 3


async def test_game_get_winners_messages(db, game_id: int) -> None:
    async with db.session() as session:
        # Create 5 users to win
        users = []
        for idx in range(5):
            users.append(
                User(
                    id=f"user_{idx}",
                    profile_photo="http://profile.jpg",
                    username=f"user_{idx}",
                )
            )
            session.add(users[idx])
        await session.commit()

        game = await Game.by_id(game_id, session=session)
        assert game is not None

        await game.add_guess(session=session, word="cherries", user_id=users[0].id)
        await session.commit()

        # Let the first two win
        for user in users[:2]:
            await game.add_guess(session=session, word=game.secret, user_id=user.id)
            await session.commit()

        # Some other guesses by other users
        await game.add_guess(session=session, word="caramel", user_id=users[2].id)
        await session.commit()

        # Let them win then
        for user in users[2:]:
            await game.add_guess(session=session, word=game.secret, user_id=user.id)
            await session.commit()

        winners_messages = game.get_winners_messages()
        assert len(winners_messages) == 5

        assert winners_messages == [
            ":first_place_medal: <@user_0> got the secret on guess 2!",
            ":second_place_medal: <@user_1> got the secret on guess 2!",
            ":third_place_medal: <@user_2> got the secret on guess 3!",
            "<@user_3> got the secret on guess 3!",
            "<@user_4> got the secret on guess 3!",
        ]


async def test_game_add_guess_secret_stops_further_guesses_from_user(
    db, game_id: int, user_id: str
) -> None:
    async with db.session() as session:
        second_user = User(
            id="user_y",
            username="similarium-player",
            profile_photo="http://example.com/profile.jpg",
        )
        session.add(second_user)
        await session.commit()

        game = await Game.by_id(game_id, session=session)
        assert game is not None

        user = await User.by_id(user_id, session=session)
        assert user is not None

        assert user not in game.winners
        assert second_user not in game.winners

        await game.add_guess(session=session, word="cherries", user_id=user_id)
        await session.commit()

        await game.add_guess(session=session, word=game.secret, user_id=user_id)
        await session.commit()

        assert len(game.winners) == 1
        assert len(game.guesses) == 2

        with pytest.raises(UserAlreadyWon):
            await game.add_guess(session=session, word="blueberry", user_id=user_id)

        # Shouldn't have changed..
        assert len(game.winners) == 1
        assert len(game.guesses) == 2

        await game.add_guess(session=session, word="blueberry", user_id=second_user.id)
        await session.commit()

        assert len(game.winners) == 1
        assert len(game.guesses) == 3
