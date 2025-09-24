"""
Performance optimization utilities for MapleHustleCAN
"""
import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from app.core.cache import (
    get_cache_manager,
    cache_key,
    cache_user,
    get_cached_user,
    cache_service,
    get_cached_service,
    cache_search_results,
    get_cached_search_results,
    invalidate_user_cache,
    invalidate_service_cache,
)
from app.core.config import settings
from app.models.users import User
from app.models.services import Service
from app.repositories.optimized_queries import (
    OptimizedUserQueries,
    OptimizedServiceQueries,
    OptimizedBookingQueries,
    OptimizedOrderQueries,
)


class PerformanceOptimizer:
    """Performance optimization utilities and caching strategies"""

    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.query_stats = {}
        self.cache_hit_rates = {}

    async def get_user_with_cache(
        self, db: Session, user_id: str, include_relations: bool = True
    ) -> Optional[User]:
        """Get user with caching and optimized queries"""
        cache_key_str = f"user:{user_id}:relations:{include_relations}"
        
        # Try cache first
        if self.cache_manager:
            cached_user = await self.cache_manager.get(cache_key_str)
            if cached_user:
                self._record_cache_hit("user")
                return cached_user

        # Use optimized query
        if include_relations:
            user = OptimizedUserQueries.get_user_with_services(db, user_id)
        else:
            user = db.query(User).filter(User.id == user_id).first()

        # Cache the result
        if user and self.cache_manager:
            await self.cache_manager.set(
                cache_key_str, 
                user, 
                expire=3600  # 1 hour
            )
            self._record_cache_miss("user")

        return user

    async def get_service_with_cache(
        self, db: Session, service_id: str, include_relations: bool = True
    ) -> Optional[Service]:
        """Get service with caching and optimized queries"""
        cache_key_str = f"service:{service_id}:relations:{include_relations}"
        
        # Try cache first
        if self.cache_manager:
            cached_service = await self.cache_manager.get(cache_key_str)
            if cached_service:
                self._record_cache_hit("service")
                return cached_service

        # Use optimized query
        if include_relations:
            service = OptimizedServiceQueries.get_service_with_bookings(db, service_id)
        else:
            service = db.query(Service).filter(Service.id == service_id).first()

        # Cache the result
        if service and self.cache_manager:
            await self.cache_manager.set(
                cache_key_str, 
                service, 
                expire=1800  # 30 minutes
            )
            self._record_cache_miss("service")

        return service

    async def get_services_list_with_cache(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Service]:
        """Get services list with caching and optimized queries"""
        # Create cache key based on parameters
        filter_str = ":".join([f"{k}:{v}" for k, v in (filters or {}).items()])
        cache_key_str = f"services:list:{skip}:{limit}:{filter_str}"
        
        # Try cache first
        if self.cache_manager:
            cached_services = await self.cache_manager.get(cache_key_str)
            if cached_services:
                self._record_cache_hit("services_list")
                return cached_services

        # Use optimized query
        services = OptimizedServiceQueries.get_services_with_provider(
            db, skip=skip, limit=limit
        )

        # Apply additional filters if provided
        if filters:
            for key, value in filters.items():
                if key == "type":
                    services = [s for s in services if s.type == value]
                elif key == "provider_id":
                    services = [s for s in services if s.provider_id == value]
                elif key == "featured":
                    services = [s for s in services if s.is_featured == value]

        # Cache the result
        if self.cache_manager:
            await self.cache_manager.set(
                cache_key_str, 
                services, 
                expire=900  # 15 minutes
            )
            self._record_cache_miss("services_list")

        return services

    async def search_services_with_cache(
        self,
        db: Session,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Service]:
        """Search services with caching"""
        # Create cache key
        filter_str = ":".join([f"{k}:{v}" for k, v in (filters or {}).items()])
        cache_key_str = f"search:services:{query}:{filter_str}:{skip}:{limit}"
        
        # Try cache first
        if self.cache_manager:
            cached_results = await self.cache_manager.get(cache_key_str)
            if cached_results:
                self._record_cache_hit("search_services")
                return cached_results

        # Perform search (simplified for now)
        services = db.query(Service).filter(
            Service.title.ilike(f"%{query}%")
        ).offset(skip).limit(limit).all()

        # Cache the result
        if self.cache_manager:
            await self.cache_manager.set(
                cache_key_str, 
                services, 
                expire=600  # 10 minutes
            )
            self._record_cache_miss("search_services")

        return services

    async def invalidate_user_related_cache(self, user_id: str):
        """Invalidate all cache entries related to a user"""
        if self.cache_manager:
            patterns = [
                f"user:{user_id}:*",
                f"services:list:*",  # User might have updated services
                f"search:*"  # Search results might include user's services
            ]
            
            for pattern in patterns:
                keys = await self.cache_manager.keys(pattern)
                for key in keys:
                    await self.cache_manager.delete(key)

    async def invalidate_service_related_cache(self, service_id: str):
        """Invalidate all cache entries related to a service"""
        if self.cache_manager:
            patterns = [
                f"service:{service_id}:*",
                f"services:list:*",  # Service list might include this service
                f"search:*"  # Search results might include this service
            ]
            
            for pattern in patterns:
                keys = await self.cache_manager.keys(pattern)
                for key in keys:
                    await self.cache_manager.delete(key)

    def _record_cache_hit(self, operation: str):
        """Record cache hit for performance monitoring"""
        if operation not in self.cache_hit_rates:
            self.cache_hit_rates[operation] = {"hits": 0, "misses": 0}
        self.cache_hit_rates[operation]["hits"] += 1

    def _record_cache_miss(self, operation: str):
        """Record cache miss for performance monitoring"""
        if operation not in self.cache_hit_rates:
            self.cache_hit_rates[operation] = {"hits": 0, "misses": 0}
        self.cache_hit_rates[operation]["misses"] += 1

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        stats = {}
        for operation, rates in self.cache_hit_rates.items():
            total = rates["hits"] + rates["misses"]
            hit_rate = (rates["hits"] / total * 100) if total > 0 else 0
            stats[operation] = {
                "hits": rates["hits"],
                "misses": rates["misses"],
                "hit_rate": round(hit_rate, 2)
            }
        return stats

    def get_query_stats(self) -> Dict[str, Any]:
        """Get database query performance statistics"""
        return self.query_stats.copy()


# Global performance optimizer instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


# Performance monitoring decorators
def monitor_performance(operation_name: str):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record performance metrics
                optimizer = get_performance_optimizer()
                if operation_name not in optimizer.query_stats:
                    optimizer.query_stats[operation_name] = {
                        "total_calls": 0,
                        "total_time": 0.0,
                        "avg_time": 0.0,
                        "min_time": float('inf'),
                        "max_time": 0.0
                    }
                
                stats = optimizer.query_stats[operation_name]
                stats["total_calls"] += 1
                stats["total_time"] += execution_time
                stats["avg_time"] = stats["total_time"] / stats["total_calls"]
                stats["min_time"] = min(stats["min_time"], execution_time)
                stats["max_time"] = max(stats["max_time"], execution_time)
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                # Log error but don't fail the function
                print(f"Error in {operation_name}: {e} (took {execution_time:.3f}s)")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record performance metrics
                optimizer = get_performance_optimizer()
                if operation_name not in optimizer.query_stats:
                    optimizer.query_stats[operation_name] = {
                        "total_calls": 0,
                        "total_time": 0.0,
                        "avg_time": 0.0,
                        "min_time": float('inf'),
                        "max_time": 0.0
                    }
                
                stats = optimizer.query_stats[operation_name]
                stats["total_calls"] += 1
                stats["total_time"] += execution_time
                stats["avg_time"] = stats["total_time"] / stats["total_calls"]
                stats["min_time"] = min(stats["min_time"], execution_time)
                stats["max_time"] = max(stats["max_time"], execution_time)
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                # Log error but don't fail the function
                print(f"Error in {operation_name}: {e} (took {execution_time:.3f}s)")
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_result(
    key_prefix: str,
    expire: int = 3600,
    key_func: Optional[Callable] = None
):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                cache_key_str = cache_key(key_prefix, *args, **kwargs)
            
            optimizer = get_performance_optimizer()
            if optimizer.cache_manager:
                # Try cache first
                cached_result = await optimizer.cache_manager.get(cache_key_str)
                if cached_result is not None:
                    optimizer._record_cache_hit(key_prefix)
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await optimizer.cache_manager.set(cache_key_str, result, expire)
                optimizer._record_cache_miss(key_prefix)
                return result
            else:
                # No cache available, just execute function
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                cache_key_str = cache_key(key_prefix, *args, **kwargs)
            
            optimizer = get_performance_optimizer()
            if optimizer.cache_manager:
                # For sync functions, we need to run in event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're already in an event loop, create a task
                    return loop.run_until_complete(async_wrapper(*args, **kwargs))
                else:
                    return loop.run_until_complete(async_wrapper(*args, **kwargs))
            else:
                # No cache available, just execute function
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Database connection pooling optimization
def optimize_database_connections():
    """Optimize database connection pool settings"""
    from app.db.session import get_engine
    
    engine = get_engine()
    
    # Optimize connection pool settings
    engine.pool._recycle = 3600  # Recycle connections every hour
    engine.pool._pre_ping = True  # Verify connections before use
    engine.pool._max_overflow = 20  # Allow 20 overflow connections
    engine.pool._pool_size = 10  # Base pool size of 10
    
    return engine


# Query optimization utilities
def optimize_query_for_pagination(query, page: int, page_size: int):
    """Optimize query for pagination"""
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def add_query_indexes():
    """Add database indexes for common queries"""
    # This would typically be done in Alembic migrations
    # but we can provide the SQL here for reference
    
    indexes = [
        # User indexes
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
        "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);",
        
        # Service indexes
        "CREATE INDEX IF NOT EXISTS idx_services_provider_id ON services(provider_id);",
        "CREATE INDEX IF NOT EXISTS idx_services_type ON services(type);",
        "CREATE INDEX IF NOT EXISTS idx_services_status ON services(status);",
        "CREATE INDEX IF NOT EXISTS idx_services_featured ON services(is_featured);",
        "CREATE INDEX IF NOT EXISTS idx_services_title ON services USING gin(to_tsvector('english', title));",
        
        # Booking indexes
        "CREATE INDEX IF NOT EXISTS idx_bookings_client_id ON bookings(client_id);",
        "CREATE INDEX IF NOT EXISTS idx_bookings_provider_id ON bookings(provider_id);",
        "CREATE INDEX IF NOT EXISTS idx_bookings_service_id ON bookings(service_id);",
        "CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);",
        "CREATE INDEX IF NOT EXISTS idx_bookings_start_date ON bookings(start_date);",
        
        # Order indexes
        "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);",
        "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);",
        
        # Payment indexes
        "CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);",
        "CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);",
        
        # Message indexes
        "CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);",
        "CREATE INDEX IF NOT EXISTS idx_messages_recipient_id ON messages(recipient_id);",
        "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);",
        
        # Notification indexes
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);",
        "CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);",
    ]
    
    return indexes


# Performance monitoring endpoints
async def get_performance_metrics() -> Dict[str, Any]:
    """Get comprehensive performance metrics"""
    optimizer = get_performance_optimizer()
    
    return {
        "cache_stats": optimizer.get_cache_stats(),
        "query_stats": optimizer.get_query_stats(),
        "cache_enabled": optimizer.cache_manager is not None,
        "timestamp": time.time()
    }


# Background task for cache warming
async def warm_cache():
    """Warm up frequently accessed cache entries"""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    optimizer = get_performance_optimizer()
    
    try:
        # Warm up popular services
        popular_services = db.query(Service).filter(
            Service.is_featured == True,
            Service.status == "active"
        ).limit(20).all()
        
        for service in popular_services:
            await optimizer.get_service_with_cache(db, str(service.id))
        
        # Warm up active users (if we have a way to identify them)
        # This would typically be based on recent activity
        
        print("Cache warming completed")
        
    except Exception as e:
        print(f"Error during cache warming: {e}")
    finally:
        db.close()
