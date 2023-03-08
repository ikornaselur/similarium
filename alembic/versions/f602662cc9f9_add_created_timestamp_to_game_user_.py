"""Add created timestamp to game user winner association

Revision ID: f602662cc9f9
Revises: e181643294b6
Create Date: 2023-03-08 14:37:56.203799

"""
import sqlalchemy as sa
from alembic import op

revision = "f602662cc9f9"
down_revision = "e181643294b6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("game_user_winner_association", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created", sa.BigInteger(), nullable=True))

    op.execute("UPDATE game_user_winner_association SET created = 0")

    with op.batch_alter_table("game_user_winner_association", schema=None) as batch_op:
        batch_op.alter_column("created", existing_type=sa.BIGINT(), nullable=False)


def downgrade():
    with op.batch_alter_table("game_user_winner_association", schema=None) as batch_op:
        batch_op.drop_column("created")
