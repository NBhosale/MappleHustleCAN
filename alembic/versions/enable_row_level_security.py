"""Enable Row-Level Security (RLS) for multi-tenant data isolation

Revision ID: rls_security_001
Revises: add_seed_data_migration
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rls_security_001'
down_revision = 'add_seed_data_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable Row-Level Security on all tables"""
    
    # Enable RLS on all tables
    tables = [
        'users', 'bookings', 'orders', 'payments', 'items', 
        'services', 'messages', 'notifications', 'reviews',
        'subscriptions', 'refresh_tokens', 'user_sessions'
    ]
    
    for table in tables:
        # Enable RLS on table
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
    
    # Create user policies
    op.execute("""
        CREATE POLICY user_own_data ON users
        FOR ALL USING (id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_users ON users
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create booking policies
    op.execute("""
        CREATE POLICY booking_own_data ON bookings
        FOR ALL USING (
            client_id = current_setting('app.current_user_id')::uuid
            OR provider_id = current_setting('app.current_user_id')::uuid
        );
    """)
    
    op.execute("""
        CREATE POLICY admin_all_bookings ON bookings
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create order policies
    op.execute("""
        CREATE POLICY order_own_data ON orders
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_orders ON orders
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create payment policies
    op.execute("""
        CREATE POLICY payment_own_data ON payments
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_payments ON payments
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create item policies
    op.execute("""
        CREATE POLICY item_public_read ON items
        FOR SELECT USING (true);
    """)
    
    op.execute("""
        CREATE POLICY item_own_modify ON items
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_items ON items
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create service policies
    op.execute("""
        CREATE POLICY service_public_read ON services
        FOR SELECT USING (true);
    """)
    
    op.execute("""
        CREATE POLICY service_own_modify ON services
        FOR ALL USING (provider_id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_services ON services
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create message policies
    op.execute("""
        CREATE POLICY message_own_data ON messages
        FOR ALL USING (
            sender_id = current_setting('app.current_user_id')::uuid
            OR recipient_id = current_setting('app.current_user_id')::uuid
        );
    """)
    
    op.execute("""
        CREATE POLICY admin_all_messages ON messages
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create notification policies
    op.execute("""
        CREATE POLICY notification_own_data ON notifications
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_notifications ON notifications
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create review policies
    op.execute("""
        CREATE POLICY review_public_read ON reviews
        FOR SELECT USING (true);
    """)
    
    op.execute("""
        CREATE POLICY review_own_modify ON reviews
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_reviews ON reviews
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create subscription policies
    op.execute("""
        CREATE POLICY subscription_own_data ON subscriptions
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_subscriptions ON subscriptions
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create token policies
    op.execute("""
        CREATE POLICY token_own_data ON refresh_tokens
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_tokens ON refresh_tokens
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)
    
    # Create session policies
    op.execute("""
        CREATE POLICY session_own_data ON user_sessions
        FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
    """)
    
    op.execute("""
        CREATE POLICY admin_all_sessions ON user_sessions
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE id = current_setting('app.current_user_id')::uuid 
                AND role = 'admin'
            )
        );
    """)


def downgrade() -> None:
    """Disable Row-Level Security on all tables"""
    
    # Drop all policies
    tables = [
        'users', 'bookings', 'orders', 'payments', 'items', 
        'services', 'messages', 'notifications', 'reviews',
        'subscriptions', 'refresh_tokens', 'user_sessions'
    ]
    
    for table in tables:
        # Drop all policies for the table
        op.execute(f"DROP POLICY IF EXISTS user_own_data ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_users ON {table};")
        op.execute(f"DROP POLICY IF EXISTS booking_own_data ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_bookings ON {table};")
        op.execute(f"DROP POLICY IF EXISTS order_own_data ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_orders ON {table};")
        op.execute(f"DROP POLICY IF EXISTS payment_own_data ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_payments ON {table};")
        op.execute(f"DROP POLICY IF EXISTS item_public_read ON {table};")
        op.execute(f"DROP POLICY IF EXISTS item_own_modify ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_items ON {table};")
        op.execute(f"DROP POLICY IF EXISTS service_public_read ON {table};")
        op.execute(f"DROP POLICY IF EXISTS service_own_modify ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_services ON {table};")
        op.execute(f"DROP POLICY IF EXISTS message_own_data ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_messages ON {table};")
        op.execute(f"DROP POLICY IF EXISTS notification_own_data ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_notifications ON {table};")
        op.execute(f"DROP POLICY IF EXISTS review_public_read ON {table};")
        op.execute(f"DROP POLICY IF EXISTS review_own_modify ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_reviews ON {table};")
        op.execute(f"DROP POLICY IF EXISTS subscription_own_data ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_subscriptions ON {table};")
        op.execute(f"DROP POLICY IF EXISTS token_own_data ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_tokens ON {table};")
        op.execute(f"DROP POLICY IF EXISTS session_own_data ON {table};")
        op.execute(f"DROP POLICY IF EXISTS admin_all_sessions ON {table};")
        
        # Disable RLS on table
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
