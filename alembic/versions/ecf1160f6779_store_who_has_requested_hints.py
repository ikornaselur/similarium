"""Store who has requested hints

Revision ID: ecf1160f6779
Revises: be1adfbe5a43
Create Date: 2023-03-30 20:49:01.898386

"""
import sqlalchemy as sa
from alembic import op

revision = "ecf1160f6779"
down_revision = "be1adfbe5a43"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "game_user_hint_association",
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("created", sa.BigInteger(), nullable=False),
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
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.add_column(sa.Column("hint", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.drop_column("hint")

    op.drop_table("game_user_hint_association")
