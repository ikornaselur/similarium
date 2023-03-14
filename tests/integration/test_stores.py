from slack_sdk.oauth.installation_store.models import Installation

from similarium.slack import installation_store, oauth_state_store


async def test_installation_store_save(db):
    installation = Installation(
        user_id="user_x",
        team_id="team_x",
        app_id="app_x",
        is_enterprise_install=False,
    )

    await installation_store.async_save(installation)

    saved_installation = await installation_store.async_find_installation(
        enterprise_id=None,
        team_id="team_x",
        is_enterprise_install=False,
    )

    assert saved_installation is not None


async def test_oauth_state_store(db):
    assert not await oauth_state_store.async_consume(state="foo")

    state = await oauth_state_store.async_issue()

    assert await oauth_state_store.async_consume(state=state)
