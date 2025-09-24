"""
Row-Level Security (RLS) implementation for MapleHustleCAN
Provides multi-tenant data isolation and security
"""

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RowLevelSecurity:
    """Row-Level Security manager for data isolation"""

    def __init__(self, db: Session):
        self.db = db

    def enable_rls_policies(self) -> None:
        """Enable RLS policies for all tables"""
        try:
            # Enable RLS on all tables
            tables = [
                'users', 'bookings', 'orders', 'payments', 'items',
                'services', 'messages', 'notifications', 'reviews',
                'subscriptions', 'refresh_tokens', 'user_sessions'
            ]

            for table in tables:
                # Enable RLS on table
                self.db.execute(
                    text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))

                # Create policies for each table
                self._create_user_policies(table)
                self._create_booking_policies(table)
                self._create_order_policies(table)
                self._create_payment_policies(table)
                self._create_item_policies(table)
                self._create_service_policies(table)
                self._create_message_policies(table)
                self._create_notification_policies(table)
                self._create_review_policies(table)
                self._create_subscription_policies(table)
                self._create_token_policies(table)
                self._create_session_policies(table)

            self.db.commit()
            logger.info("✅ RLS policies enabled successfully")

        except Exception as e:
            logger.error(f"❌ Failed to enable RLS policies: {e}")
            self.db.rollback()
            raise

    def _create_user_policies(self, table: str) -> None:
        """Create RLS policies for user-related data"""
        if table == 'users':
            # Users can only see their own data
            self.db.execute(text("""
                CREATE POLICY user_own_data ON users
                FOR ALL USING (id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can see all users
            self.db.execute(text("""
                CREATE POLICY admin_all_users ON users
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_booking_policies(self, table: str) -> None:
        """Create RLS policies for booking-related data"""
        if table == 'bookings':
            # Users can only see their own bookings (as client or provider)
            self.db.execute(text("""
                CREATE POLICY booking_own_data ON bookings
                FOR ALL USING (
                    client_id = current_setting('app.current_user_id')::uuid
                    OR provider_id = current_setting('app.current_user_id')::uuid
                );
            """))

            # Admins can see all bookings
            self.db.execute(text("""
                CREATE POLICY admin_all_bookings ON bookings
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_order_policies(self, table: str) -> None:
        """Create RLS policies for order-related data"""
        if table == 'orders':
            # Users can only see their own orders
            self.db.execute(text("""
                CREATE POLICY order_own_data ON orders
                FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can see all orders
            self.db.execute(text("""
                CREATE POLICY admin_all_orders ON orders
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_payment_policies(self, table: str) -> None:
        """Create RLS policies for payment-related data"""
        if table == 'payments':
            # Users can only see their own payments
            self.db.execute(text("""
                CREATE POLICY payment_own_data ON payments
                FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can see all payments
            self.db.execute(text("""
                CREATE POLICY admin_all_payments ON payments
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_item_policies(self, table: str) -> None:
        """Create RLS policies for item-related data"""
        if table == 'items':
            # Users can see all items (public catalog)
            self.db.execute(text("""
                CREATE POLICY item_public_read ON items
                FOR SELECT USING (true);
            """))

            # Only item owners can modify their items
            self.db.execute(text("""
                CREATE POLICY item_own_modify ON items
                FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can modify all items
            self.db.execute(text("""
                CREATE POLICY admin_all_items ON items
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_service_policies(self, table: str) -> None:
        """Create RLS policies for service-related data"""
        if table == 'services':
            # Users can see all services (public catalog)
            self.db.execute(text("""
                CREATE POLICY service_public_read ON services
                FOR SELECT USING (true);
            """))

            # Only service providers can modify their services
            self.db.execute(text("""
                CREATE POLICY service_own_modify ON services
                FOR ALL USING (provider_id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can modify all services
            self.db.execute(text("""
                CREATE POLICY admin_all_services ON services
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_message_policies(self, table: str) -> None:
        """Create RLS policies for message-related data"""
        if table == 'messages':
            # Users can only see messages they sent or received
            self.db.execute(text("""
                CREATE POLICY message_own_data ON messages
                FOR ALL USING (
                    sender_id = current_setting('app.current_user_id')::uuid
                    OR recipient_id = current_setting('app.current_user_id')::uuid
                );
            """))

            # Admins can see all messages
            self.db.execute(text("""
                CREATE POLICY admin_all_messages ON messages
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_notification_policies(self, table: str) -> None:
        """Create RLS policies for notification-related data"""
        if table == 'notifications':
            # Users can only see their own notifications
            self.db.execute(text("""
                CREATE POLICY notification_own_data ON notifications
                FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can see all notifications
            self.db.execute(text("""
                CREATE POLICY admin_all_notifications ON notifications
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_review_policies(self, table: str) -> None:
        """Create RLS policies for review-related data"""
        if table == 'reviews':
            # Users can see all reviews (public)
            self.db.execute(text("""
                CREATE POLICY review_public_read ON reviews
                FOR SELECT USING (true);
            """))

            # Users can only modify their own reviews
            self.db.execute(text("""
                CREATE POLICY review_own_modify ON reviews
                FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can modify all reviews
            self.db.execute(text("""
                CREATE POLICY admin_all_reviews ON reviews
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_subscription_policies(self, table: str) -> None:
        """Create RLS policies for subscription-related data"""
        if table == 'subscriptions':
            # Users can only see their own subscriptions
            self.db.execute(text("""
                CREATE POLICY subscription_own_data ON subscriptions
                FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can see all subscriptions
            self.db.execute(text("""
                CREATE POLICY admin_all_subscriptions ON subscriptions
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_token_policies(self, table: str) -> None:
        """Create RLS policies for token-related data"""
        if table == 'refresh_tokens':
            # Users can only see their own tokens
            self.db.execute(text("""
                CREATE POLICY token_own_data ON refresh_tokens
                FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can see all tokens
            self.db.execute(text("""
                CREATE POLICY admin_all_tokens ON refresh_tokens
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def _create_session_policies(self, table: str) -> None:
        """Create RLS policies for session-related data"""
        if table == 'user_sessions':
            # Users can only see their own sessions
            self.db.execute(text("""
                CREATE POLICY session_own_data ON user_sessions
                FOR ALL USING (user_id = current_setting('app.current_user_id')::uuid);
            """))

            # Admins can see all sessions
            self.db.execute(text("""
                CREATE POLICY admin_all_sessions ON user_sessions
                FOR ALL USING (
                    EXISTS (
                        SELECT 1 FROM users
                        WHERE id = current_setting('app.current_user_id')::uuid
                        AND role = 'admin'
                    )
                );
            """))

    def set_current_user(self, user_id: UUID) -> None:
        """Set current user context for RLS"""
        try:
            self.db.execute(text(f"SET app.current_user_id = '{user_id}';"))
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to set current user: {e}")
            raise

    def clear_current_user(self) -> None:
        """Clear current user context"""
        try:
            self.db.execute(text("SET app.current_user_id = NULL;"))
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to clear current user: {e}")
            raise


def create_rls_middleware():
    """Create RLS middleware for FastAPI"""
    from fastapi import Request
    from starlette.middleware.base import BaseHTTPMiddleware

    class RLSMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Skip RLS for public endpoints
            if request.url.path.startswith(
                    "/auth/login") or request.url.path.startswith("/auth/register"):
                return await call_next(request)

            # Get current user from JWT token
            try:
                # This would need to be adapted based on your auth implementation
                # For now, we'll skip RLS setup in middleware
                # In production, you'd extract user_id from JWT and set it
                pass
            except Exception:
                # If no user, continue without RLS context
                pass

            response = await call_next(request)
            return response

    return RLSMiddleware
