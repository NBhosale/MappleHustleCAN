"""merge heads

Revision ID: f65bd796e9ad
Revises: rls_security_001, add_missing_fields_to_users
Create Date: 2025-09-24 00:51:00.869023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f65bd796e9ad'
down_revision: Union[str, Sequence[str], None] = ('rls_security_001', 'add_missing_fields_to_users')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
