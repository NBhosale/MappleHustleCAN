"""
Optimized service layer with caching and performance monitoring
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.core.performance_optimization import (
    get_performance_optimizer,
    monitor_performance,
    cache_result
)
from app.models.users import User
from app.models.services import Service, Availability, Portfolio
from app.models.bookings import Booking
from app.models.orders import Order
from app.models.items import Item
from app.repositories.optimized_queries import (
    OptimizedUserQueries,
    OptimizedServiceQueries,
    OptimizedBookingQueries,
    OptimizedOrderQueries,
)


class OptimizedUserService:
    """Optimized user service with caching"""

    def __init__(self):
        self.optimizer = get_performance_optimizer()

    @monitor_performance("get_user")
    async def get_user(
        self, 
        db: Session, 
        user_id: str, 
        include_relations: bool = True
    ) -> Optional[User]:
        """Get user with caching and optimized queries"""
        return await self.optimizer.get_user_with_cache(
            db, user_id, include_relations
        )

    @monitor_performance("get_user_by_email")
    @cache_result("user:email", expire=1800)
    async def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email with caching"""
        return db.query(User).filter(User.email == email).first()

    @monitor_performance("get_user_services")
    async def get_user_services(
        self, 
        db: Session, 
        user_id: str
    ) -> List[Service]:
        """Get user's services with optimized queries"""
        user = await self.get_user(db, user_id, include_relations=True)
        return user.services if user else []

    @monitor_performance("get_user_bookings")
    async def get_user_bookings(
        self, 
        db: Session, 
        user_id: str
    ) -> List[Booking]:
        """Get user's bookings with optimized queries"""
        return OptimizedBookingQueries.get_user_bookings_with_relations(db, user_id)

    @monitor_performance("get_user_orders")
    async def get_user_orders(
        self, 
        db: Session, 
        user_id: str
    ) -> List[Order]:
        """Get user's orders with optimized queries"""
        return OptimizedOrderQueries.get_user_orders_with_items(db, user_id)

    async def invalidate_user_cache(self, user_id: str):
        """Invalidate user-related cache"""
        await self.optimizer.invalidate_user_related_cache(user_id)


class OptimizedServiceService:
    """Optimized service service with caching"""

    def __init__(self):
        self.optimizer = get_performance_optimizer()

    @monitor_performance("get_service")
    async def get_service(
        self, 
        db: Session, 
        service_id: str, 
        include_relations: bool = True
    ) -> Optional[Service]:
        """Get service with caching and optimized queries"""
        return await self.optimizer.get_service_with_cache(
            db, service_id, include_relations
        )

    @monitor_performance("get_services_list")
    async def get_services_list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Service]:
        """Get services list with caching and optimized queries"""
        return await self.optimizer.get_services_list_with_cache(
            db, skip, limit, filters
        )

    @monitor_performance("search_services")
    async def search_services(
        self,
        db: Session,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Service]:
        """Search services with caching"""
        return await self.optimizer.search_services_with_cache(
            db, query, filters, skip, limit
        )

    @monitor_performance("get_services_by_provider")
    async def get_services_by_provider(
        self, 
        db: Session, 
        provider_id: str
    ) -> List[Service]:
        """Get services by provider with optimized queries"""
        return OptimizedServiceQueries.get_services_by_provider_with_stats(
            db, provider_id
        )

    @monitor_performance("get_service_bookings")
    async def get_service_bookings(
        self, 
        db: Session, 
        service_id: str
    ) -> List[Booking]:
        """Get service bookings with optimized queries"""
        service = await self.get_service(db, service_id, include_relations=True)
        return service.bookings if service else []

    async def create_service(
        self, 
        db: Session, 
        provider_id: str, 
        service_data: Dict[str, Any]
    ) -> Service:
        """Create service and invalidate cache"""
        service = Service(
            provider_id=provider_id,
            **service_data
        )
        db.add(service)
        db.commit()
        db.refresh(service)
        
        # Invalidate related cache
        await self.optimizer.invalidate_service_related_cache(str(service.id))
        await self.optimizer.invalidate_user_related_cache(provider_id)
        
        return service

    async def update_service(
        self, 
        db: Session, 
        service_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[Service]:
        """Update service and invalidate cache"""
        service = await self.get_service(db, service_id, include_relations=False)
        if not service:
            return None
        
        for key, value in update_data.items():
            setattr(service, key, value)
        
        db.commit()
        db.refresh(service)
        
        # Invalidate related cache
        await self.optimizer.invalidate_service_related_cache(service_id)
        await self.optimizer.invalidate_user_related_cache(str(service.provider_id))
        
        return service

    async def delete_service(
        self, 
        db: Session, 
        service_id: str
    ) -> bool:
        """Delete service and invalidate cache"""
        service = await self.get_service(db, service_id, include_relations=False)
        if not service:
            return False
        
        provider_id = str(service.provider_id)
        db.delete(service)
        db.commit()
        
        # Invalidate related cache
        await self.optimizer.invalidate_service_related_cache(service_id)
        await self.optimizer.invalidate_user_related_cache(provider_id)
        
        return True


class OptimizedBookingService:
    """Optimized booking service with caching"""

    def __init__(self):
        self.optimizer = get_performance_optimizer()

    @monitor_performance("get_booking")
    @cache_result("booking", expire=1800)
    async def get_booking(self, db: Session, booking_id: str) -> Optional[Booking]:
        """Get booking with caching"""
        return db.query(Booking).filter(Booking.id == booking_id).first()

    @monitor_performance("get_user_bookings")
    async def get_user_bookings(
        self, 
        db: Session, 
        user_id: str
    ) -> List[Booking]:
        """Get user bookings with optimized queries"""
        return OptimizedBookingQueries.get_user_bookings_with_relations(db, user_id)

    @monitor_performance("get_provider_bookings")
    async def get_provider_bookings(
        self, 
        db: Session, 
        provider_id: str
    ) -> List[Booking]:
        """Get provider bookings with optimized queries"""
        return OptimizedBookingQueries.get_provider_bookings_with_relations(
            db, provider_id
        )

    @monitor_performance("get_bookings_list")
    async def get_bookings_list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Booking]:
        """Get bookings list with optimized queries"""
        query = db.query(Booking)
        
        # Apply filters
        if filters:
            if "status" in filters:
                query = query.filter(Booking.status == filters["status"])
            if "user_id" in filters:
                query = query.filter(Booking.client_id == filters["user_id"])
            if "provider_id" in filters:
                query = query.filter(Booking.provider_id == filters["provider_id"])
        
        return OptimizedBookingQueries.get_bookings_with_relations(
            db, skip=skip, limit=limit
        )

    async def create_booking(
        self, 
        db: Session, 
        booking_data: Dict[str, Any]
    ) -> Booking:
        """Create booking and invalidate cache"""
        booking = Booking(**booking_data)
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        # Invalidate related cache
        await self.optimizer.invalidate_user_related_cache(str(booking.client_id))
        await self.optimizer.invalidate_user_related_cache(str(booking.provider_id))
        await self.optimizer.invalidate_service_related_cache(str(booking.service_id))
        
        return booking

    async def update_booking_status(
        self, 
        db: Session, 
        booking_id: str, 
        status: str
    ) -> Optional[Booking]:
        """Update booking status and invalidate cache"""
        booking = await self.get_booking(db, booking_id)
        if not booking:
            return None
        
        booking.status = status
        db.commit()
        db.refresh(booking)
        
        # Invalidate related cache
        await self.optimizer.invalidate_user_related_cache(str(booking.client_id))
        await self.optimizer.invalidate_user_related_cache(str(booking.provider_id))
        
        return booking


class OptimizedOrderService:
    """Optimized order service with caching"""

    def __init__(self):
        self.optimizer = get_performance_optimizer()

    @monitor_performance("get_order")
    @cache_result("order", expire=1800)
    async def get_order(self, db: Session, order_id: str) -> Optional[Order]:
        """Get order with caching"""
        return db.query(Order).filter(Order.id == order_id).first()

    @monitor_performance("get_user_orders")
    async def get_user_orders(
        self, 
        db: Session, 
        user_id: str
    ) -> List[Order]:
        """Get user orders with optimized queries"""
        return OptimizedOrderQueries.get_user_orders_with_items(db, user_id)

    @monitor_performance("get_orders_list")
    async def get_orders_list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Order]:
        """Get orders list with optimized queries"""
        return OptimizedOrderQueries.get_orders_with_items(
            db, skip=skip, limit=limit
        )

    async def create_order(
        self, 
        db: Session, 
        order_data: Dict[str, Any]
    ) -> Order:
        """Create order and invalidate cache"""
        order = Order(**order_data)
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Invalidate related cache
        await self.optimizer.invalidate_user_related_cache(str(order.user_id))
        
        return order

    async def update_order_status(
        self, 
        db: Session, 
        order_id: str, 
        status: str
    ) -> Optional[Order]:
        """Update order status and invalidate cache"""
        order = await self.get_order(db, order_id)
        if not order:
            return None
        
        order.status = status
        db.commit()
        db.refresh(order)
        
        # Invalidate related cache
        await self.optimizer.invalidate_user_related_cache(str(order.user_id))
        
        return order


class OptimizedItemService:
    """Optimized item service with caching"""

    def __init__(self):
        self.optimizer = get_performance_optimizer()

    @monitor_performance("get_item")
    @cache_result("item", expire=1800)
    async def get_item(self, db: Session, item_id: str) -> Optional[Item]:
        """Get item with caching"""
        return db.query(Item).filter(Item.id == item_id).first()

    @monitor_performance("get_items_list")
    async def get_items_list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Item]:
        """Get items list with optimized queries"""
        return OptimizedItemQueries.get_items_with_provider(
            db, skip=skip, limit=limit
        )

    @monitor_performance("search_items")
    @cache_result("search:items", expire=600)
    async def search_items(
        self,
        db: Session,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Item]:
        """Search items with caching"""
        # Perform search (simplified for now)
        items = db.query(Item).filter(
            Item.title.ilike(f"%{query}%")
        ).offset(skip).limit(limit).all()
        
        return items

    async def create_item(
        self, 
        db: Session, 
        item_data: Dict[str, Any]
    ) -> Item:
        """Create item and invalidate cache"""
        item = Item(**item_data)
        db.add(item)
        db.commit()
        db.refresh(item)
        
        # Invalidate related cache
        await self.optimizer.invalidate_user_related_cache(str(item.seller_id))
        
        return item

    async def update_item(
        self, 
        db: Session, 
        item_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[Item]:
        """Update item and invalidate cache"""
        item = await self.get_item(db, item_id)
        if not item:
            return None
        
        for key, value in update_data.items():
            setattr(item, key, value)
        
        db.commit()
        db.refresh(item)
        
        # Invalidate related cache
        await self.optimizer.invalidate_user_related_cache(str(item.seller_id))
        
        return item


# Global service instances
user_service = OptimizedUserService()
service_service = OptimizedServiceService()
booking_service = OptimizedBookingService()
order_service = OptimizedOrderService()
item_service = OptimizedItemService()


# Performance monitoring functions
async def get_performance_stats() -> Dict[str, Any]:
    """Get comprehensive performance statistics"""
    optimizer = get_performance_optimizer()
    
    return {
        "cache_stats": optimizer.get_cache_stats(),
        "query_stats": optimizer.get_query_stats(),
        "cache_enabled": optimizer.cache_manager is not None,
        "services": {
            "user_service": "active",
            "service_service": "active",
            "booking_service": "active",
            "order_service": "active",
            "item_service": "active"
        }
    }


async def warm_up_cache():
    """Warm up frequently accessed cache entries"""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Warm up popular services
        popular_services = db.query(Service).filter(
            Service.is_featured == True,
            Service.status == "active"
        ).limit(20).all()
        
        for service in popular_services:
            await service_service.get_service(db, str(service.id))
        
        # Warm up active users (simplified)
        active_users = db.query(User).filter(
            User.status == "active"
        ).limit(50).all()
        
        for user in active_users:
            await user_service.get_user(db, str(user.id))
        
        print("Cache warming completed successfully")
        
    except Exception as e:
        print(f"Error during cache warming: {e}")
    finally:
        db.close()
