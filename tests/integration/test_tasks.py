import asyncio
from unittest import mock

from similarium.exceptions import AccountInactive
from similarium.models import Channel
from similarium.tasks import action


async def test_create_games_handles_one_task_erroring(db) -> None:
    channels = [
        Channel(id="channel_1", team_id="team_x", hour=1),
        Channel(id="channel_2", team_id="team_x", hour=1),
        Channel(id="channel_3", team_id="team_x", hour=1),
    ]
    async with db.session() as s:
        s.add_all(channels)
        await s.commit()

    pings = []

    async def mock_action(channel_id: str) -> None:
        if channel_id == "channel_1":
            raise Exception("Uh oh")
        await asyncio.sleep(0.1)
        pings.append(channel_id)

    await action(channels, mock_action)

    assert len(pings) == 2
    assert "channel_2" in pings
    assert "channel_3" in pings


async def test_create_games_reports_errors_to_sentry(db) -> None:
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

    async def mock_action(channel_id: str) -> None:
        if channel_id == "channel_1":
            raise exception
        await asyncio.sleep(0.1)
        pings.append(channel_id)

    with mock.patch("similarium.tasks.sentry_sdk") as mock_sentry:
        await action(channels, mock_action)

    mock_sentry.capture_exception.assert_called_once_with(exception)


async def test_create_games_marks_channels_as_inactive_if_account_inactive(db) -> None:
    channels = [
        Channel(id="channel_1", team_id="team_x", hour=1),
        Channel(id="channel_2", team_id="team_x", hour=1),
        Channel(id="channel_3", team_id="team_x", hour=1),
    ]
    async with db.session() as s:
        s.add_all(channels)
        await s.commit()

    async def mock_action(channel_id: str) -> None:
        if channel_id == "channel_1":
            raise AccountInactive()

    with mock.patch("similarium.tasks.sentry_sdk") as mock_sentry:
        await action(channels, mock_action)

    assert not mock_sentry.capture_exception.called
    assert not channels[0].active
    assert channels[1].active
    assert channels[1].active
