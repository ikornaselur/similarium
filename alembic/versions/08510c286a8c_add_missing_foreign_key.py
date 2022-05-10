"""Add missing foreign key

Revision ID: 08510c286a8c
Revises: f58820236770
Create Date: 2022-05-10 21:45:56.590579

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "08510c286a8c"
down_revision = "f58820236770"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.create_foreign_key("channel_id", "channel", ["channel_id"], ["id"])


def downgrade():
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.drop_constraint("channel_id", type_="foreignkey")
