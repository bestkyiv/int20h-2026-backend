"""baseline

Revision ID: b567d301d5bc
Revises:
Create Date: 2026-01-11 01:13:27.329355

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b567d301d5bc"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create universities table
    op.create_table(
        "universities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_universities_name", "universities", ["name"], unique=False)

    # Create categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=False)

    # Create teams table
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_name", sa.String(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_name", "category_id", name="uix_team_name_category"),
    )
    op.create_index("ix_teams_team_name", "teams", ["team_name"], unique=False)
    op.create_index("ix_teams_category_id", "teams", ["category_id"], unique=False)

    # Create participants table
    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("telegram", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column(
            "study_year", sa.Integer(), nullable=False
        ),  # Will be made nullable in next migration
        sa.Column(
            "university_id", sa.Integer(), nullable=False
        ),  # Will be made nullable in next migration
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column(
            "participation_format",
            sa.Enum("ONLINE", "OFFLINE", name="participationformat"),
            nullable=False,
        ),
        sa.Column("team_leader", sa.Boolean(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("wants_job", sa.Boolean(), nullable=False),
        sa.Column("job_description", sa.String(), nullable=True),
        sa.Column("cv_url", sa.String(), nullable=True),
        sa.Column("linkedin", sa.String(), nullable=True),
        sa.Column("work_consent", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("personal_data_consent", sa.Boolean(), nullable=False),
        sa.Column("skills_text", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
        ),
        sa.ForeignKeyConstraint(
            ["university_id"],
            ["universities.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("telegram"),
    )
    op.create_index(
        "ix_participants_full_name", "participants", ["full_name"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("participants")
    op.drop_table("teams")
    op.drop_table("categories")
    op.drop_table("universities")
