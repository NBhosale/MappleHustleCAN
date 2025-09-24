"""add Row-Level Security (RLS) policies for multi-tenant data isolation"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_rls_policies"
down_revision = "add_seed_data"
branch_labels = None
depends_on = None


def upgrade():
    # Enable RLS on all tables
    tables = [
        "users", "bookings", "orders", "payments", "services", 
        "availability", "messages", "notifications", "items",
        "portfolio", "service_tags", "reviews", "subscriptions",
        "tokens", "sessions", "system_events", "tax_rules", 
        "provider_metrics", "provider_certifications", "message_attachments"
    ]
    
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    
    # Users table policies
    op.execute("""
        CREATE POLICY users_own_data ON users
        FOR ALL USING (id = current_setting('app.current_user_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY users_admin_access ON users
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        )
    """)
    
    # Bookings table policies
    op.execute("""
        CREATE POLICY bookings_user_access ON bookings
        FOR ALL USING (
            user_id = current_setting('app.current_user_id')::uuid
            OR provider_id = current_setting('app.current_user_id')::uuid
        )
    """)
    
    # Orders table policies
    op.execute("""
        CREATE POLICY orders_user_access ON orders
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid)
    """)
    
    # Payments table policies
    op.execute("""
        CREATE POLICY payments_user_access ON payments
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM orders o 
                WHERE o.id = payments.order_id 
                AND o.user_id = current_setting('app.current_user_id')::uuid
            )
        )
    """)
    
    # Services table policies
    op.execute("""
        CREATE POLICY services_provider_access ON services
        FOR ALL USING (provider_id = current_setting('app.current_user_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY services_public_read ON services
        FOR SELECT USING (true)
    """)
    
    # Availability table policies
    op.execute("""
        CREATE POLICY availability_provider_access ON availability
        FOR ALL USING (provider_id = current_setting('app.current_user_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY availability_public_read ON availability
        FOR SELECT USING (true)
    """)
    
    # Messages table policies
    op.execute("""
        CREATE POLICY messages_participant_access ON messages
        FOR ALL USING (
            sender_id = current_setting('app.current_user_id')::uuid
            OR recipient_id = current_setting('app.current_user_id')::uuid
        )
    """)
    
    # Notifications table policies
    op.execute("""
        CREATE POLICY notifications_user_access ON notifications
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid)
    """)
    
    # Items table policies
    op.execute("""
        CREATE POLICY items_provider_access ON items
        FOR ALL USING (provider_id = current_setting('app.current_user_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY items_public_read ON items
        FOR SELECT USING (true)
    """)
    
    # Portfolio table policies
    op.execute("""
        CREATE POLICY portfolio_provider_access ON portfolio
        FOR ALL USING (provider_id = current_setting('app.current_user_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY portfolio_public_read ON portfolio
        FOR SELECT USING (true)
    """)
    
    # Reviews table policies
    op.execute("""
        CREATE POLICY reviews_user_access ON reviews
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY reviews_public_read ON reviews
        FOR SELECT USING (true)
    """)
    
    # Subscriptions table policies
    op.execute("""
        CREATE POLICY subscriptions_user_access ON subscriptions
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid)
    """)
    
    # Tokens table policies
    op.execute("""
        CREATE POLICY tokens_user_access ON tokens
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid)
    """)
    
    # Sessions table policies
    op.execute("""
        CREATE POLICY sessions_user_access ON sessions
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid)
    """)
    
    # System events - admin only
    op.execute("""
        CREATE POLICY system_events_admin_access ON system_events
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        )
    """)
    
    # Tax rules - admin only
    op.execute("""
        CREATE POLICY tax_rules_admin_access ON tax_rules
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        )
    """)
    
    # Provider metrics - provider access
    op.execute("""
        CREATE POLICY provider_metrics_access ON provider_metrics
        FOR ALL USING (provider_id = current_setting('app.current_user_id')::uuid)
    """)
    
    # Provider certifications - provider access
    op.execute("""
        CREATE POLICY provider_certifications_access ON provider_certifications
        FOR ALL USING (provider_id = current_setting('app.current_user_id')::uuid)
    """)
    
    # Message attachments - participant access
    op.execute("""
        CREATE POLICY message_attachments_access ON message_attachments
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM messages m 
                WHERE m.id = message_attachments.message_id 
                AND (m.sender_id = current_setting('app.current_user_id')::uuid
                     OR m.recipient_id = current_setting('app.current_user_id')::uuid)
            )
        )
    """)


def downgrade():
    # Drop all RLS policies
    policies = [
        "users_own_data", "users_admin_access",
        "bookings_user_access", "orders_user_access", "payments_user_access",
        "services_provider_access", "services_public_read",
        "availability_provider_access", "availability_public_read",
        "messages_participant_access", "notifications_user_access",
        "items_provider_access", "items_public_read",
        "portfolio_provider_access", "portfolio_public_read",
        "reviews_user_access", "reviews_public_read",
        "subscriptions_user_access", "tokens_user_access",
        "sessions_user_access", "system_events_admin_access",
        "tax_rules_admin_access", "provider_metrics_access",
        "provider_certifications_access", "message_attachments_access"
    ]
    
    for policy in policies:
        try:
            op.execute(f"DROP POLICY IF EXISTS {policy}")
        except:
            pass  # Policy might not exist
    
    # Disable RLS on all tables
    tables = [
        "users", "bookings", "orders", "payments", "services", 
        "availability", "messages", "notifications", "items",
        "portfolio", "service_tags", "reviews", "subscriptions",
        "tokens", "sessions", "system_events", "tax_rules", 
        "provider_metrics", "provider_certifications", "message_attachments"
    ]
    
    for table in tables:
        try:
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        except:
            pass  # Table might not exist
