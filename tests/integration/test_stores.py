from slack_sdk.oauth.installation_store.models import Installation

from similarium.slack import installation_store


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
