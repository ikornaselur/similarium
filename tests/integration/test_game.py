from semantle_slack_bot.db import Game, User


async def test_game_add_guess_adds_guess(session, game: Game, user: User) -> None:
    assert game.guesses == []

    await game.add_guess(session=session, word="berry", user_id=user.id)

    assert len(game.guesses) == 1
    assert game.guesses[0].word == "berry"


async def test_game_add_guess_handles_duplicates(
    session, game: Game, user: User
) -> None:
    assert game.guesses == []

    await game.add_guess(session=session, word="berry", user_id=user.id)

    assert len(game.guesses) == 1

    await game.add_guess(session=session, word="berry", user_id=user.id)

    assert len(game.guesses) == 1
