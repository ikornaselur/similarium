"""Add many-to-many game-user winner association

Revision ID: a612cb489a61
Revises: d4438613fd7c
Create Date: 2022-05-21 16:56:48.529841

"""
import sqlalchemy as sa
from alembic import op

revision = "a612cb489a61"
down_revision = "d4438613fd7c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "game_user_winner_association",
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("guess_idx", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["game.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("game_id", "user_id"),
    )


def downgrade():
    op.drop_table("game_user_winner_association")
