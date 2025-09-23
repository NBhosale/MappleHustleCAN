"""add missing fields to users

Revision ID: 901b4520ff92
Revises: add_missing_fields_to_users
Create Date: 2025-09-23 00:13:47.103550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '901b4520ff92'
down_revision: Union[str, Sequence[str], None] = 'add_missing_fields_to_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
