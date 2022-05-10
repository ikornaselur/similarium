"""Base

Revision ID: f58820236770
Revises:
Create Date: 2022-05-10 21:44:08.532075

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f58820236770"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "channel",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("team_id", sa.Text(), nullable=False),
        sa.Column("hour", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "similarity_range",
        sa.Column("word", sa.Text(), nullable=False),
        sa.Column("top", sa.Float(), nullable=False),
        sa.Column("top10", sa.Float(), nullable=False),
        sa.Column("rest", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("word"),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("profile_photo", sa.Text(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "word2vec",
        sa.Column("word", sa.Text(), nullable=False),
        sa.Column("vec", sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint("word"),
    )
    op.create_table(
        "game",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.Text(), nullable=False),
        sa.Column("thread_ts", sa.Text(), nullable=False),
        sa.Column("puzzle_number", sa.Integer(), nullable=False),
        sa.Column("date", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("secret", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.create_index(
            "channel_thread_idx", ["channel_id", "thread_ts"], unique=False
        )

    op.create_table(
        "nearby",
        sa.Column("word", sa.Text(), nullable=False),
        sa.Column("neighbor", sa.Text(), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("percentile", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["neighbor"],
            ["word2vec.word"],
        ),
        sa.ForeignKeyConstraint(
            ["word"],
            ["word2vec.word"],
        ),
        sa.PrimaryKeyConstraint("word", "neighbor"),
    )
    op.create_table(
        "guess",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("updated", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("word", sa.Text(), nullable=False),
        sa.Column("percentile", sa.Integer(), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["game.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("guess")
    op.drop_table("nearby")
    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.drop_index("channel_thread_idx")

    op.drop_table("game")
    op.drop_table("word2vec")
    op.drop_table("user")
    op.drop_table("similarity_range")
    op.drop_table("channel")
