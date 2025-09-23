"""add missing fields to users

Revision ID: add_missing_fields_to_users
Revises: b65c82ba4740
Create Date: 2025-09-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Revision identifiers
revision = "add_missing_fields_to_users"
down_revision = "b65c82ba4740"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("address", sa.String(), nullable=True))
    op.add_column("users", sa.Column("city", sa.String(), nullable=True))
    op.add_column("users", sa.Column("postal_code", sa.String(), nullable=True))
    op.add_column("users", sa.Column("province_code", sa.String(length=2), nullable=True))
    op.add_column("users", sa.Column("location", postgresql.GEOGRAPHY("POINT", 4326), nullable=True))
    op.add_column("users", sa.Column("profile_image_path", sa.String(), nullable=True))
    op.add_column("users", sa.Column("preferred_contact_method", sa.Enum("in_app", "email", "sms", name="contactmethod"), nullable=True))
    op.add_column("users", sa.Column("verification_token", sa.String(), nullable=True))
    op.add_column("users", sa.Column("password_reset_token", sa.String(), nullable=True))
    op.add_column("users", sa.Column("password_reset_expires", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "password_reset_expires")
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "verification_token")
    op.drop_column("users", "preferred_contact_method")
    op.drop_column("users", "profile_image_path")
    op.drop_column("users", "location")
    op.drop_column("users", "province_code")
    op.drop_column("users", "postal_code")
    op.drop_column("users", "city")
    op.drop_column("users", "address")
