"""add missing fields to users

Revision ID: 901b4520ff92
Revises: add_missing_fields_to_users
Create Date: 2025-09-23 00:13:47.103550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '901b4520ff92'
down_revision = 'b65c82ba4740'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing fields to users table."""
    # Add province_code field
    op.add_column('users', sa.Column('province_code', sa.String(2), nullable=True))
    
    # Add phone_number field
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))
    
    # Add foreign key constraint to canadian_provinces
    op.create_foreign_key(
        'fk_users_province_code', 'users', 'canadian_provinces',
        ['province_code'], ['code']
    )


def downgrade() -> None:
    """Remove added fields from users table."""
    # Drop foreign key constraint
    op.drop_constraint('fk_users_province_code', 'users', type_='foreignkey')
    
    # Drop columns
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'province_code')
