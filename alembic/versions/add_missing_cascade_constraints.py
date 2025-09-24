"""add missing CASCADE constraints to prevent orphaned records"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_missing_cascade_constraints"
down_revision = "standardize_datetime_handling"
branch_labels = None
depends_on = None


def upgrade():
    """Add missing CASCADE constraints to foreign keys"""
    
    # Drop existing foreign keys that don't have CASCADE
    op.drop_constraint("fk_bookings_user_id", "bookings", type_="foreignkey")
    op.drop_constraint("fk_bookings_provider_id", "bookings", type_="foreignkey")
    op.drop_constraint("fk_orders_user_id", "orders", type_="foreignkey")
    op.drop_constraint("fk_payments_order_id", "payments", type_="foreignkey")
    op.drop_constraint("fk_services_provider_id", "services", type_="foreignkey")
    op.drop_constraint("fk_availability_provider_id", "availability", type_="foreignkey")
    op.drop_constraint("fk_messages_sender_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_messages_recipient_id", "messages", type_="foreignkey")
    op.drop_constraint("fk_notifications_user_id", "notifications", type_="foreignkey")
    
    # Recreate foreign keys with CASCADE
    op.create_foreign_key(
        "fk_bookings_user_id_cascade", "bookings", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_bookings_provider_id_cascade", "bookings", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_orders_user_id_cascade", "orders", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_payments_order_id_cascade", "payments", "orders", 
        ["order_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_services_provider_id_cascade", "services", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_availability_provider_id_cascade", "availability", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_messages_sender_id_cascade", "messages", "users", 
        ["sender_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_messages_recipient_id_cascade", "messages", "users", 
        ["recipient_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_notifications_user_id_cascade", "notifications", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    
    # Add missing foreign key constraints
    op.create_foreign_key(
        "fk_items_provider_id_cascade", "items", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_portfolio_provider_id_cascade", "portfolio", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_service_tags_service_id_cascade", "service_tags", "services", 
        ["service_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_reviews_user_id_cascade", "reviews", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_reviews_service_id_cascade", "reviews", "services", 
        ["service_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_subscriptions_user_id_cascade", "subscriptions", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_tokens_user_id_cascade", "tokens", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_sessions_user_id_cascade", "sessions", "users", 
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_provider_metrics_provider_id_cascade", "provider_metrics", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_provider_certifications_provider_id_cascade", "provider_certifications", "users", 
        ["provider_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_message_attachments_message_id_cascade", "message_attachments", "messages", 
        ["message_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_order_items_order_id_cascade", "order_items", "orders", 
        ["order_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_order_items_item_id_cascade", "order_items", "items", 
        ["item_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_order_shipments_order_id_cascade", "order_shipments", "orders", 
        ["order_id"], ["id"], ondelete="CASCADE"
    )


def downgrade():
    """Remove CASCADE constraints"""
    # Drop CASCADE foreign keys
    cascade_constraints = [
        "fk_bookings_user_id_cascade", "fk_bookings_provider_id_cascade",
        "fk_orders_user_id_cascade", "fk_payments_order_id_cascade",
        "fk_services_provider_id_cascade", "fk_availability_provider_id_cascade",
        "fk_messages_sender_id_cascade", "fk_messages_recipient_id_cascade",
        "fk_notifications_user_id_cascade", "fk_items_provider_id_cascade",
        "fk_portfolio_provider_id_cascade", "fk_service_tags_service_id_cascade",
        "fk_reviews_user_id_cascade", "fk_reviews_service_id_cascade",
        "fk_subscriptions_user_id_cascade", "fk_tokens_user_id_cascade",
        "fk_sessions_user_id_cascade", "fk_provider_metrics_provider_id_cascade",
        "fk_provider_certifications_provider_id_cascade",
        "fk_message_attachments_message_id_cascade",
        "fk_order_items_order_id_cascade", "fk_order_items_item_id_cascade",
        "fk_order_shipments_order_id_cascade"
    ]
    
    for constraint in cascade_constraints:
        try:
            op.drop_constraint(constraint, "bookings", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "orders", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "payments", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "services", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "availability", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "messages", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "notifications", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "items", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "portfolio", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "service_tags", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "reviews", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "subscriptions", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "tokens", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "sessions", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "provider_metrics", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "provider_certifications", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "message_attachments", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "order_items", type_="foreignkey")
        except:
            pass
        try:
            op.drop_constraint(constraint, "order_shipments", type_="foreignkey")
        except:
            pass
