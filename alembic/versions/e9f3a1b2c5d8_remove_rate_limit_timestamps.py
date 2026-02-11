"""remove_rate_limit_timestamps

Revision ID: e9f3a1b2c5d8
Revises: caf62b643458
Create Date: 2026-02-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e9f3a1b2c5d8"
down_revision: Union[str, Sequence[str], None] = "caf62b643458"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove timestamp columns used for rate limiting (now handled in-memory)."""
    # Drop columns from participants table
    with op.batch_alter_table("participants", schema=None) as batch_op:
        batch_op.drop_column("last_bio_update")
        batch_op.drop_column("last_skills_update")
        batch_op.drop_column("last_category_change")

    # Drop column from teams table
    with op.batch_alter_table("teams", schema=None) as batch_op:
        batch_op.drop_column("last_category_change")


def downgrade() -> None:
    """Re-add timestamp columns for rate limiting."""
    # Add columns back to teams table
    with op.batch_alter_table("teams", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "last_category_change",
                postgresql.TIMESTAMP(timezone=True),
                nullable=True,
            )
        )

    # Add columns back to participants table
    with op.batch_alter_table("participants", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "last_category_change",
                postgresql.TIMESTAMP(timezone=True),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "last_skills_update", postgresql.TIMESTAMP(timezone=True), nullable=True
            )
        )
        batch_op.add_column(
            sa.Column(
                "last_bio_update", postgresql.TIMESTAMP(timezone=True), nullable=True
            )
        )
