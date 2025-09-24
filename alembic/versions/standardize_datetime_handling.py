"""standardize datetime handling across all models and schemas"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "standardize_datetime_handling"
down_revision = "add_rls_policies"
branch_labels = None
depends_on = None


def upgrade():
    """Standardize all datetime fields to TIMESTAMP(timezone=True)"""
    
    # Update users table
    op.alter_column('users', 'last_login_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('users', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('users', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('users', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('users', 'password_reset_expires', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.DateTime())
    
    # Update bookings table
    op.alter_column('bookings', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('bookings', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('bookings', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update orders table
    op.alter_column('orders', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('orders', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('orders', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('orders', 'shipped_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update payments table
    op.alter_column('payments', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('payments', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('payments', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update services table
    op.alter_column('services', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('services', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('services', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update portfolio table
    op.alter_column('portfolio', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('portfolio', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('portfolio', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update items table
    op.alter_column('items', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('items', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('items', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update messages table
    op.alter_column('messages', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('messages', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('messages', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update notifications table
    op.alter_column('notifications', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('notifications', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('notifications', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update reviews table
    op.alter_column('reviews', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('reviews', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('reviews', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update subscriptions table
    op.alter_column('subscriptions', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('subscriptions', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('subscriptions', 'deleted_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update tokens table
    op.alter_column('tokens', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('tokens', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('tokens', 'expires_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update sessions table
    op.alter_column('sessions', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('sessions', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('sessions', 'expires', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update system_events table
    op.alter_column('system_events', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update provider_metrics table
    op.alter_column('provider_metrics', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('provider_metrics', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update provider_certifications table
    op.alter_column('provider_certifications', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('provider_certifications', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('provider_certifications', 'expires_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    
    # Update message_attachments table
    op.alter_column('message_attachments', 'created_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))
    op.alter_column('message_attachments', 'updated_at', 
                   type_=sa.TIMESTAMP(timezone=True), 
                   existing_type=sa.TIMESTAMP(timezone=True))


def downgrade():
    """Revert datetime standardization"""
    # Note: This is a complex downgrade that would need to be carefully implemented
    # For now, we'll leave it as a placeholder since datetime standardization
    # is generally a one-way migration
    pass
