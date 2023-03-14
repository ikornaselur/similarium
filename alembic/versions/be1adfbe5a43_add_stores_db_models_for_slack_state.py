"""Add stores DB models for Slack state

Revision ID: be1adfbe5a43
Revises: f602662cc9f9
Create Date: 2023-03-13 23:24:18.922739

"""
import datetime as dt
import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op

from similarium.config import config

revision = "be1adfbe5a43"
down_revision = "f602662cc9f9"
branch_labels = None
depends_on = None

data_dir = Path() / "data"
installations_dir = data_dir / "installations"


def upgrade():
    op.create_table(
        "slack_bots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.String(length=32), nullable=False),
        sa.Column("app_id", sa.String(length=32), nullable=False),
        sa.Column("enterprise_id", sa.String(length=32), nullable=True),
        sa.Column("enterprise_name", sa.String(length=200), nullable=True),
        sa.Column("team_id", sa.String(length=32), nullable=True),
        sa.Column("team_name", sa.String(length=200), nullable=True),
        sa.Column("bot_token", sa.String(length=200), nullable=True),
        sa.Column("bot_id", sa.String(length=32), nullable=True),
        sa.Column("bot_user_id", sa.String(length=32), nullable=True),
        sa.Column("bot_scopes", sa.String(length=1000), nullable=True),
        sa.Column("bot_refresh_token", sa.String(length=200), nullable=True),
        sa.Column("bot_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_enterprise_install", sa.Boolean(), nullable=False),
        sa.Column("installed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("slack_bots", schema=None) as batch_op:
        batch_op.create_index(
            "slack_bots_idx",
            ["client_id", "enterprise_id", "team_id", "installed_at"],
            unique=False,
        )

    op.create_table(
        "slack_installations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.String(length=32), nullable=False),
        sa.Column("app_id", sa.String(length=32), nullable=False),
        sa.Column("enterprise_id", sa.String(length=32), nullable=True),
        sa.Column("enterprise_name", sa.String(length=200), nullable=True),
        sa.Column("enterprise_url", sa.String(length=200), nullable=True),
        sa.Column("team_id", sa.String(length=32), nullable=True),
        sa.Column("team_name", sa.String(length=200), nullable=True),
        sa.Column("bot_token", sa.String(length=200), nullable=True),
        sa.Column("bot_id", sa.String(length=32), nullable=True),
        sa.Column("bot_user_id", sa.String(length=32), nullable=True),
        sa.Column("bot_scopes", sa.String(length=1000), nullable=True),
        sa.Column("bot_refresh_token", sa.String(length=200), nullable=True),
        sa.Column("bot_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("user_token", sa.String(length=200), nullable=True),
        sa.Column("user_scopes", sa.String(length=1000), nullable=True),
        sa.Column("user_refresh_token", sa.String(length=200), nullable=True),
        sa.Column("user_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("incoming_webhook_url", sa.String(length=200), nullable=True),
        sa.Column("incoming_webhook_channel", sa.String(length=200), nullable=True),
        sa.Column("incoming_webhook_channel_id", sa.String(length=200), nullable=True),
        sa.Column(
            "incoming_webhook_configuration_url", sa.String(length=200), nullable=True
        ),
        sa.Column("is_enterprise_install", sa.Boolean(), nullable=False),
        sa.Column("token_type", sa.String(length=32), nullable=True),
        sa.Column("installed_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("slack_installations", schema=None) as batch_op:
        batch_op.create_index(
            "slack_installations_idx",
            ["client_id", "enterprise_id", "team_id", "user_id", "installed_at"],
            unique=False,
        )

    op.create_table(
        "slack_oauth_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("state", sa.String(length=200), nullable=False),
        sa.Column("expire_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    migrate_data()


def downgrade():
    op.drop_table("slack_oauth_states")
    with op.batch_alter_table("slack_installations", schema=None) as batch_op:
        batch_op.drop_index("slack_installations_idx")

    op.drop_table("slack_installations")
    with op.batch_alter_table("slack_bots", schema=None) as batch_op:
        batch_op.drop_index("slack_bots_idx")

    op.drop_table("slack_bots")


def migrate_data():
    bots_table = sa.table(
        "slack_bots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.String(length=32), nullable=False),
        sa.Column("app_id", sa.String(length=32), nullable=False),
        sa.Column("enterprise_id", sa.String(length=32), nullable=True),
        sa.Column("enterprise_name", sa.String(length=200), nullable=True),
        sa.Column("team_id", sa.String(length=32), nullable=True),
        sa.Column("team_name", sa.String(length=200), nullable=True),
        sa.Column("bot_token", sa.String(length=200), nullable=True),
        sa.Column("bot_id", sa.String(length=32), nullable=True),
        sa.Column("bot_user_id", sa.String(length=32), nullable=True),
        sa.Column("bot_scopes", sa.String(length=1000), nullable=True),
        sa.Column("bot_refresh_token", sa.String(length=200), nullable=True),
        sa.Column("bot_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_enterprise_install", sa.Boolean(), nullable=False),
        sa.Column("installed_at", sa.DateTime(), nullable=False),
    )

    installations_table = sa.table(
        "slack_installations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.String(length=32), nullable=False),
        sa.Column("app_id", sa.String(length=32), nullable=False),
        sa.Column("enterprise_id", sa.String(length=32), nullable=True),
        sa.Column("enterprise_name", sa.String(length=200), nullable=True),
        sa.Column("enterprise_url", sa.String(length=200), nullable=True),
        sa.Column("team_id", sa.String(length=32), nullable=True),
        sa.Column("team_name", sa.String(length=200), nullable=True),
        sa.Column("bot_token", sa.String(length=200), nullable=True),
        sa.Column("bot_id", sa.String(length=32), nullable=True),
        sa.Column("bot_user_id", sa.String(length=32), nullable=True),
        sa.Column("bot_scopes", sa.String(length=1000), nullable=True),
        sa.Column("bot_refresh_token", sa.String(length=200), nullable=True),
        sa.Column("bot_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("user_token", sa.String(length=200), nullable=True),
        sa.Column("user_scopes", sa.String(length=1000), nullable=True),
        sa.Column("user_refresh_token", sa.String(length=200), nullable=True),
        sa.Column("user_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("incoming_webhook_url", sa.String(length=200), nullable=True),
        sa.Column("incoming_webhook_channel", sa.String(length=200), nullable=True),
        sa.Column("incoming_webhook_channel_id", sa.String(length=200), nullable=True),
        sa.Column(
            "incoming_webhook_configuration_url", sa.String(length=200), nullable=True
        ),
        sa.Column("is_enterprise_install", sa.Boolean(), nullable=False),
        sa.Column("token_type", sa.String(length=32), nullable=True),
        sa.Column("installed_at", sa.DateTime(), nullable=False),
    )

    # Process installations
    for installation in installations_dir.iterdir():
        bot_latest = json.loads((installation / "bot-latest").read_text())

        # Transform fields required to match the table
        bot_latest["bot_scopes"] = json.dumps(bot_latest["bot_scopes"])
        bot_latest["installed_at"] = dt.datetime.fromtimestamp(
            bot_latest["installed_at"]
        )
        bot_latest["client_id"] = config.slack.client_id

        op.bulk_insert(bots_table, [bot_latest])

        installer_latest = json.loads((installation / "installer-latest").read_text())

        # Transform fields required to match the table
        installer_latest["bot_scopes"] = json.dumps(installer_latest["bot_scopes"])
        installer_latest["installed_at"] = dt.datetime.fromtimestamp(
            installer_latest["installed_at"]
        )
        installer_latest["client_id"] = config.slack.client_id

        op.bulk_insert(installations_table, [installer_latest])
