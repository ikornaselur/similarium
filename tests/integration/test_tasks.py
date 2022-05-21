import asyncio
from unittest import mock

import pytest

from similarium.models import Channel
from similarium.tasks import create_games


async def test_create_games_handles_one_task_erroring(
    db,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    channels = [
        Channel(id="channel_1", team_id="team_x", hour=1),
        Channel(id="channel_2", team_id="team_x", hour=1),
        Channel(id="channel_3", team_id="team_x", hour=1),
    ]
    async with db.session() as s:
        s.add_all(channels)
        await s.commit()

    pings = []

    async def mock_end_game(channel_id: str) -> None:
        if channel_id == "channel_1":
            raise Exception("Uh oh")
        await asyncio.sleep(0.1)
        pings.append(channel_id)

    monkeypatch.setattr("similarium.tasks.end_game", mock_end_game)
    monkeypatch.setattr(
        "similarium.tasks.start_game", mock.AsyncMock(return_value=None)
    )

    await create_games(1)

    assert len(pings) == 2
    assert "channel_2" in pings
    assert "channel_3" in pings


async def test_create_games_reports_errors_to_sentry(
    db,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    channels = [
        Channel(id="channel_1", team_id="team_x", hour=1),
        Channel(id="channel_2", team_id="team_x", hour=1),
        Channel(id="channel_3", team_id="team_x", hour=1),
    ]
    async with db.session() as s:
        s.add_all(channels)
        await s.commit()

    pings = []
    exception = Exception("Uh oh")

    async def mock_end_game(channel_id: str) -> None:
        if channel_id == "channel_1":
            raise exception
        await asyncio.sleep(0.1)
        pings.append(channel_id)

    monkeypatch.setattr("similarium.tasks.end_game", mock_end_game)
    monkeypatch.setattr(
        "similarium.tasks.start_game", mock.AsyncMock(return_value=None)
    )

    with mock.patch("similarium.tasks.sentry_sdk") as mock_sentry:
        await create_games(1)

    mock_sentry.capture_exception.assert_called_once_with(exception)
