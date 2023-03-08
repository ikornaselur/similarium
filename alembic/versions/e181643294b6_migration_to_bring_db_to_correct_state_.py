"""Migration to bring db to correct state after sqlite to psql

Revision ID: e181643294b6
Revises: a612cb489a61
Create Date: 2023-03-08 12:49:00.768283

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e181643294b6"
down_revision = "a612cb489a61"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("channel", schema=None) as batch_op:
        batch_op.alter_column("team_id", existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column("hour", existing_type=sa.BIGINT(), nullable=False)
        batch_op.alter_column("active", existing_type=sa.BOOLEAN(), nullable=False)

    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.alter_column("channel_id", existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column("thread_ts", existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column(
            "puzzle_number", existing_type=sa.BIGINT(), nullable=False
        )
        batch_op.alter_column("date", existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column("active", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column("secret", existing_type=sa.TEXT(), nullable=False)
        batch_op.drop_index("idx_16921_channel_thread_idx")
        batch_op.create_index(
            "channel_thread_idx", ["channel_id", "thread_ts"], unique=False
        )
        batch_op.create_foreign_key(None, "channel", ["channel_id"], ["id"])

    with op.batch_alter_table("game_user_winner_association", schema=None) as batch_op:
        batch_op.alter_column("guess_idx", existing_type=sa.BIGINT(), nullable=False)

    with op.batch_alter_table("guess", schema=None) as batch_op:
        batch_op.alter_column("game_id", existing_type=sa.BIGINT(), nullable=False)
        batch_op.alter_column("updated", existing_type=sa.BIGINT(), nullable=False)
        batch_op.alter_column("user_id", existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column(
            "latest_guess_user_id", existing_type=sa.TEXT(), nullable=False
        )
        batch_op.alter_column("word", existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column("percentile", existing_type=sa.BIGINT(), nullable=False)
        batch_op.alter_column(
            "similarity",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=False,
        )
        batch_op.alter_column("idx", existing_type=sa.BIGINT(), nullable=False)

    with op.batch_alter_table("nearby", schema=None) as batch_op:
        batch_op.alter_column(
            "similarity",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=False,
        )
        batch_op.alter_column("percentile", existing_type=sa.BIGINT(), nullable=False)

    with op.batch_alter_table("similarity_range", schema=None) as batch_op:
        batch_op.alter_column(
            "top",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=False,
        )
        batch_op.alter_column(
            "top10",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=False,
        )
        batch_op.alter_column(
            "rest",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=False,
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("profile_photo", existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column("username", existing_type=sa.TEXT(), nullable=False)

    with op.batch_alter_table("word2vec", schema=None) as batch_op:
        batch_op.alter_column("vec", existing_type=postgresql.BYTEA(), nullable=False)


def downgrade():
    with op.batch_alter_table("word2vec", schema=None) as batch_op:
        batch_op.alter_column("vec", existing_type=postgresql.BYTEA(), nullable=True)

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("username", existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column("profile_photo", existing_type=sa.TEXT(), nullable=True)

    with op.batch_alter_table("similarity_range", schema=None) as batch_op:
        batch_op.alter_column(
            "rest",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=True,
        )
        batch_op.alter_column(
            "top10",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=True,
        )
        batch_op.alter_column(
            "top",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=True,
        )

    with op.batch_alter_table("nearby", schema=None) as batch_op:
        batch_op.alter_column("percentile", existing_type=sa.BIGINT(), nullable=True)
        batch_op.alter_column(
            "similarity",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=True,
        )

    with op.batch_alter_table("guess", schema=None) as batch_op:
        batch_op.alter_column("idx", existing_type=sa.BIGINT(), nullable=True)
        batch_op.alter_column(
            "similarity",
            existing_type=postgresql.DOUBLE_PRECISION(precision=53),
            nullable=True,
        )
        batch_op.alter_column("percentile", existing_type=sa.BIGINT(), nullable=True)
        batch_op.alter_column("word", existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column(
            "latest_guess_user_id", existing_type=sa.TEXT(), nullable=True
        )
        batch_op.alter_column("user_id", existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column("updated", existing_type=sa.BIGINT(), nullable=True)
        batch_op.alter_column("game_id", existing_type=sa.BIGINT(), nullable=True)

    with op.batch_alter_table("game_user_winner_association", schema=None) as batch_op:
        batch_op.alter_column("guess_idx", existing_type=sa.BIGINT(), nullable=True)

    with op.batch_alter_table("game", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_index("channel_thread_idx")
        batch_op.create_index(
            "idx_16921_channel_thread_idx", ["channel_id", "thread_ts"], unique=False
        )
        batch_op.alter_column("secret", existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column("active", existing_type=sa.BOOLEAN(), nullable=True)
        batch_op.alter_column("date", existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column("puzzle_number", existing_type=sa.BIGINT(), nullable=True)
        batch_op.alter_column("thread_ts", existing_type=sa.TEXT(), nullable=True)
        batch_op.alter_column("channel_id", existing_type=sa.TEXT(), nullable=True)

    with op.batch_alter_table("channel", schema=None) as batch_op:
        batch_op.alter_column("active", existing_type=sa.BOOLEAN(), nullable=True)
        batch_op.alter_column("hour", existing_type=sa.BIGINT(), nullable=True)
        batch_op.alter_column("team_id", existing_type=sa.TEXT(), nullable=True)
