"""add indexes and constraints for performance and data integrity"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_indexes_and_constraints"
down_revision = "901b4520ff92"  # Update this to the latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Add indexes for frequently queried fields
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_created_at", "users", ["created_at"])
    op.create_index("ix_users_phone_number", "users", ["phone_number"])
    op.create_index("ix_users_postal_code", "users", ["postal_code"])
    op.create_index("ix_users_city", "users", ["city"])
    
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_provider_id", "bookings", ["provider_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_created_at", "bookings", ["created_at"])
    
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])
    
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_created_at", "payments", ["created_at"])
    
    op.create_index("ix_services_provider_id", "services", ["provider_id"])
    op.create_index("ix_services_type", "services", ["type"])
    op.create_index("ix_services_is_featured", "services", ["is_featured"])
    
    op.create_index("ix_availability_provider_id", "availability", ["provider_id"])
    op.create_index("ix_availability_date", "availability", ["date"])
    op.create_index("ix_availability_status", "availability", ["status"])
    
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"])
    op.create_index("ix_messages_recipient_id", "messages", ["recipient_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])
    
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    
    # Additional performance indexes
    op.create_index("ix_items_provider_id", "items", ["provider_id"])
    op.create_index("ix_items_category", "items", ["category"])
    op.create_index("ix_items_status", "items", ["status"])
    op.create_index("ix_items_created_at", "items", ["created_at"])
    
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])
    op.create_index("reviews_service_id", "reviews", ["service_id"])
    op.create_index("ix_reviews_rating", "reviews", ["rating"])
    op.create_index("ix_reviews_created_at", "reviews", ["created_at"])
    
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index("ix_subscriptions_created_at", "subscriptions", ["created_at"])
    
    op.create_index("ix_tokens_user_id", "tokens", ["user_id"])
    op.create_index("ix_tokens_token_type", "tokens", ["token_type"])
    op.create_index("ix_tokens_expires_at", "tokens", ["expires_at"])
    
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_expires", "sessions", ["expires"])
    
    op.create_index("ix_system_events_event_type", "system_events", ["event_type"])
    op.create_index("ix_system_events_created_at", "system_events", ["created_at"])
    
    op.create_index("ix_provider_metrics_provider_id", "provider_metrics", ["provider_id"])
    op.create_index("ix_provider_metrics_metric_type", "provider_metrics", ["metric_type"])
    op.create_index("ix_provider_metrics_created_at", "provider_metrics", ["created_at"])
    
    # Add foreign key constraints with CASCADE
    op.create_foreign_key(
        "fk_bookings_user_id", "bookings", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_bookings_provider_id", "bookings", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    
    op.create_foreign_key(
        "fk_orders_user_id", "orders", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    
    op.create_foreign_key(
        "fk_payments_order_id", "payments", "orders", 
        ["order_id"], ["id"], ondelete="CASCADE"
    )
    
    op.create_foreign_key(
        "fk_services_provider_id", "services", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    
    op.create_foreign_key(
        "fk_availability_provider_id", "availability", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    
    op.create_foreign_key(
        "fk_messages_sender_id", "messages", "users", 
        ["sender_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_messages_recipient_id", "messages", "users", 
        ["recipient_id"], ["id"], ondelete="CASCADE"
    )
    
    op.create_foreign_key(
        "fk_notifications_user_id", "notifications", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )


def downgrade():
    # Drop foreign key constraints
    op.drop_constraint("fk_notifications_user_id", "notifications", type_="foreignkey")
    op.drop_constraint("fk_messages_recipient_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_messages_sender_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_availability_provider_id", "availability", type_="foreignkey")
    op.drop_constraint("fk_services_provider_id", "services", type_="foreignkey")
    op.drop_constraint("fk_payments_order_id", "payments", type_="foreignkey")
    op.drop_constraint("fk_orders_user_id", "orders", type_="foreignkey")
    op.drop_constraint("fk_bookings_provider_id", "bookings", type_="foreignkey")
    op.drop_constraint("fk_bookings_user_id", "bookings", type_="foreignkey")
    
    # Drop indexes
    op.drop_index("ix_notifications_is_read", "notifications")
    op.drop_index("ix_notifications_type", "notifications")
    op.drop_index("ix_notifications_user_id", "notifications")
    op.drop_index("ix_messages_created_at", "messages")
    op.drop_index("ix_messages_recipient_id", "messages")
    op.drop_index("ix_messages_sender_id", "messages")
    op.drop_index("ix_availability_status", "availability")
    op.drop_index("ix_availability_date", "availability")
    op.drop_index("ix_availability_provider_id", "availability")
    op.drop_index("ix_services_is_featured", "services")
    op.drop_index("ix_services_type", "services")
    op.drop_index("ix_services_provider_id", "services")
    op.drop_index("ix_payments_created_at", "payments")
    op.drop_index("ix_payments_status", "payments")
    op.drop_index("ix_payments_order_id", "payments")
    op.drop_index("ix_orders_created_at", "orders")
    op.drop_index("ix_orders_status", "orders")
    op.drop_index("ix_orders_user_id", "orders")
    op.drop_index("ix_bookings_created_at", "bookings")
    op.drop_index("ix_bookings_status", "bookings")
    op.drop_index("ix_bookings_provider_id", "bookings")
    op.drop_index("ix_bookings_user_id", "bookings")
    op.drop_index("ix_users_created_at", "users")
    op.drop_index("ix_users_status", "users")
    op.drop_index("ix_users_role", "users")
    op.drop_index("ix_users_email", "users")
