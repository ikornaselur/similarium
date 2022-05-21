"""Add active flag on Channel

Revision ID: d4438613fd7c
Revises: 2446cc86658c
Create Date: 2022-05-21 13:36:38.113230

"""
import sqlalchemy as sa
from alembic import op

revision = "d4438613fd7c"
down_revision = "2446cc86658c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("channel", schema=None) as batch_op:
        batch_op.add_column(sa.Column("active", sa.Boolean(), nullable=True))

    op.execute("UPDATE channel SET active = true")

    with op.batch_alter_table("channel", schema=None) as batch_op:
        batch_op.alter_column("active", nullable=False)


def downgrade():
    with op.batch_alter_table("channel", schema=None) as batch_op:
        batch_op.drop_column("active")
