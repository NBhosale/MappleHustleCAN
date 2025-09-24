"""
Optimized queries to prevent N+1 problems
"""
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from app.models.users import User
from app.models.services import Service
from app.models.bookings import Booking
from app.models.orders import Order
from app.models.payments import Payment
from app.models.items import Item
from app.models.messages import Message
from app.models.notifications import Notification
from app.models.reviews import Review
from app.models.subscriptions import Subscription


class OptimizedUserQueries:
    """Optimized user queries with proper eager loading"""
    
    @staticmethod
    def get_user_with_services(db: Session, user_id: str) -> Optional[User]:
        """Get user with all their services (eager loading)"""
        return db.query(User).options(
            selectinload(User.services)
        ).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_with_bookings(db: Session, user_id: str) -> Optional[User]:
        """Get user with all their bookings (eager loading)"""
        return db.query(User).options(
            selectinload(User.bookings).selectinload(Booking.service),
            selectinload(User.bookings).selectinload(Booking.provider)
        ).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_with_orders(db: Session, user_id: str) -> Optional[User]:
        """Get user with all their orders (eager loading)"""
        return db.query(User).options(
            selectinload(User.orders).selectinload(Order.items),
            selectinload(User.orders).selectinload(Order.payments)
        ).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_with_messages(db: Session, user_id: str) -> Optional[User]:
        """Get user with all their messages (eager loading)"""
        return db.query(User).options(
            selectinload(User.sent_messages).selectinload(Message.recipient),
            selectinload(User.received_messages).selectinload(Message.sender)
        ).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_with_notifications(db: Session, user_id: str) -> Optional[User]:
        """Get user with all their notifications (eager loading)"""
        return db.query(User).options(
            selectinload(User.notifications)
        ).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_with_reviews(db: Session, user_id: str) -> Optional[User]:
        """Get user with all their reviews (eager loading)"""
        return db.query(User).options(
            selectinload(User.reviews).selectinload(Review.service),
            selectinload(User.reviews).selectinload(Review.booking)
        ).filter(User.id == user_id).first()


class OptimizedServiceQueries:
    """Optimized service queries with proper eager loading"""
    
    @staticmethod
    def get_services_with_provider(db: Session, skip: int = 0, limit: int = 10) -> List[Service]:
        """Get services with provider information (eager loading)"""
        return db.query(Service).options(
            joinedload(Service.provider)
        ).filter(Service.status == "active").offset(skip).limit(limit).all()
    
    @staticmethod
    def get_service_with_bookings(db: Session, service_id: str) -> Optional[Service]:
        """Get service with all bookings (eager loading)"""
        return db.query(Service).options(
            selectinload(Service.bookings).selectinload(Booking.user),
            selectinload(Service.provider)
        ).filter(Service.id == service_id).first()
    
    @staticmethod
    def get_service_with_reviews(db: Session, service_id: str) -> Optional[Service]:
        """Get service with all reviews (eager loading)"""
        return db.query(Service).options(
            selectinload(Service.reviews).selectinload(Review.user),
            selectinload(Service.provider)
        ).filter(Service.id == service_id).first()
    
    @staticmethod
    def get_services_by_provider_with_stats(db: Session, provider_id: str) -> List[Service]:
        """Get services by provider with statistics (eager loading)"""
        return db.query(Service).options(
            selectinload(Service.bookings),
            selectinload(Service.reviews)
        ).filter(
            Service.provider_id == provider_id,
            Service.status == "active"
        ).all()


class OptimizedBookingQueries:
    """Optimized booking queries with proper eager loading"""
    
    @staticmethod
    def get_bookings_with_relations(db: Session, skip: int = 0, limit: int = 10) -> List[Booking]:
        """Get bookings with all relations (eager loading)"""
        return db.query(Booking).options(
            joinedload(Booking.user),
            joinedload(Booking.provider),
            joinedload(Booking.service)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_user_bookings_with_relations(db: Session, user_id: str) -> List[Booking]:
        """Get user bookings with all relations (eager loading)"""
        return db.query(Booking).options(
            joinedload(Booking.provider),
            joinedload(Booking.service)
        ).filter(Booking.user_id == user_id).all()
    
    @staticmethod
    def get_provider_bookings_with_relations(db: Session, provider_id: str) -> List[Booking]:
        """Get provider bookings with all relations (eager loading)"""
        return db.query(Booking).options(
            joinedload(Booking.user),
            joinedload(Booking.service)
        ).filter(Booking.provider_id == provider_id).all()


class OptimizedOrderQueries:
    """Optimized order queries with proper eager loading"""
    
    @staticmethod
    def get_orders_with_items(db: Session, skip: int = 0, limit: int = 10) -> List[Order]:
        """Get orders with items (eager loading)"""
        return db.query(Order).options(
            joinedload(Order.user),
            selectinload(Order.items),
            selectinload(Order.payments)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_user_orders_with_items(db: Session, user_id: str) -> List[Order]:
        """Get user orders with items (eager loading)"""
        return db.query(Order).options(
            selectinload(Order.items),
            selectinload(Order.payments)
        ).filter(Order.user_id == user_id).all()
    
    @staticmethod
    def get_order_with_full_details(db: Session, order_id: str) -> Optional[Order]:
        """Get order with full details (eager loading)"""
        return db.query(Order).options(
            joinedload(Order.user),
            selectinload(Order.items).joinedload(Item.provider),
            selectinload(Order.payments),
            selectinload(Order.shipments)
        ).filter(Order.id == order_id).first()


class OptimizedPaymentQueries:
    """Optimized payment queries with proper eager loading"""
    
    @staticmethod
    def get_payments_with_order(db: Session, skip: int = 0, limit: int = 10) -> List[Payment]:
        """Get payments with order (eager loading)"""
        return db.query(Payment).options(
            joinedload(Payment.order).joinedload(Order.user)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_user_payments_with_order(db: Session, user_id: str) -> List[Payment]:
        """Get user payments with order (eager loading)"""
        return db.query(Payment).options(
            joinedload(Payment.order)
        ).join(Order).filter(Order.user_id == user_id).all()


class OptimizedItemQueries:
    """Optimized item queries with proper eager loading"""
    
    @staticmethod
    def get_items_with_provider(db: Session, skip: int = 0, limit: int = 10) -> List[Item]:
        """Get items with provider (eager loading)"""
        return db.query(Item).options(
            joinedload(Item.provider)
        ).filter(Item.status == "active").offset(skip).limit(limit).all()
    
    @staticmethod
    def get_provider_items_with_stats(db: Session, provider_id: str) -> List[Item]:
        """Get provider items with statistics (eager loading)"""
        return db.query(Item).options(
            selectinload(Item.order_items)
        ).filter(
            Item.provider_id == provider_id,
            Item.status == "active"
        ).all()


class OptimizedMessageQueries:
    """Optimized message queries with proper eager loading"""
    
    @staticmethod
    def get_conversation_with_users(db: Session, user1_id: str, user2_id: str) -> List[Message]:
        """Get conversation between two users (eager loading)"""
        return db.query(Message).options(
            joinedload(Message.sender),
            joinedload(Message.recipient)
        ).filter(
            or_(
                and_(Message.sender_id == user1_id, Message.recipient_id == user2_id),
                and_(Message.sender_id == user2_id, Message.recipient_id == user1_id)
            )
        ).order_by(Message.created_at.asc()).all()
    
    @staticmethod
    def get_user_messages_with_relations(db: Session, user_id: str) -> List[Message]:
        """Get user messages with relations (eager loading)"""
        return db.query(Message).options(
            joinedload(Message.sender),
            joinedload(Message.recipient)
        ).filter(
            or_(Message.sender_id == user_id, Message.recipient_id == user_id)
        ).order_by(Message.created_at.desc()).all()


class OptimizedNotificationQueries:
    """Optimized notification queries with proper eager loading"""
    
    @staticmethod
    def get_user_notifications_with_relations(db: Session, user_id: str) -> List[Notification]:
        """Get user notifications with relations (eager loading)"""
        return db.query(Notification).options(
            joinedload(Notification.user)
        ).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def get_unread_notifications_count(db: Session, user_id: str) -> int:
        """Get unread notifications count (optimized)"""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()


class OptimizedReviewQueries:
    """Optimized review queries with proper eager loading"""
    
    @staticmethod
    def get_reviews_with_relations(db: Session, skip: int = 0, limit: int = 10) -> List[Review]:
        """Get reviews with relations (eager loading)"""
        return db.query(Review).options(
            joinedload(Review.user),
            joinedload(Review.service).joinedload(Service.provider),
            joinedload(Review.booking)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_service_reviews_with_users(db: Session, service_id: str) -> List[Review]:
        """Get service reviews with users (eager loading)"""
        return db.query(Review).options(
            joinedload(Review.user)
        ).filter(Review.service_id == service_id).order_by(Review.created_at.desc()).all()


class OptimizedSubscriptionQueries:
    """Optimized subscription queries with proper eager loading"""
    
    @staticmethod
    def get_user_subscriptions_with_relations(db: Session, user_id: str) -> List[Subscription]:
        """Get user subscriptions with relations (eager loading)"""
        return db.query(Subscription).options(
            joinedload(Subscription.user)
        ).filter(Subscription.user_id == user_id).all()
    
    @staticmethod
    def get_active_subscriptions_with_users(db: Session) -> List[Subscription]:
        """Get active subscriptions with users (eager loading)"""
        return db.query(Subscription).options(
            joinedload(Subscription.user)
        ).filter(Subscription.status == "active").all()


# Export all query classes
__all__ = [
    'OptimizedUserQueries',
    'OptimizedServiceQueries', 
    'OptimizedBookingQueries',
    'OptimizedOrderQueries',
    'OptimizedPaymentQueries',
    'OptimizedItemQueries',
    'OptimizedMessageQueries',
    'OptimizedNotificationQueries',
    'OptimizedReviewQueries',
    'OptimizedSubscriptionQueries'
]
