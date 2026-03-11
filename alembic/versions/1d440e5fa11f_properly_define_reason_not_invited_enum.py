"""properly define reason not invited enum

Revision ID: 1d440e5fa11f
Revises: be99dd684d6d
Create Date: 2026-02-26 09:59:05.936666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '1d440e5fa11f'
down_revision: Union[str, Sequence[str], None] = 'be99dd684d6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
