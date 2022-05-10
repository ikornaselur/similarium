"""Keep reference to last guesser for guesses

Revision ID: 2446cc86658c
Revises: 08510c286a8c
Create Date: 2022-05-10 22:08:50.980853

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2446cc86658c"
down_revision = "08510c286a8c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("guess", schema=None) as batch_op:
        batch_op.add_column(sa.Column("latest_guess_user_id", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "latest_guess_user_id", "user", ["latest_guess_user_id"], ["id"]
        )

    op.execute("UPDATE guess SET latest_guess_user_id = user_id")

    with op.batch_alter_table("guess", schema=None) as batch_op:
        batch_op.alter_column("latest_guess_user_id", nullable=False)


def downgrade():
    with op.batch_alter_table("guess", schema=None) as batch_op:
        batch_op.drop_constraint("latest_guess_user_id", type_="foreignkey")
        batch_op.drop_column("latest_guess_user_id")
