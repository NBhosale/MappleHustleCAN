"""
Redis caching layer for MapleHustleCAN
"""
import json
import asyncio
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


class CacheManager:
    """Redis cache manager with connection pooling"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection pool and client"""
        try:
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.client.ping()
            logger.info("Redis connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connections"""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        logger.info("Redis connections closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if not self.client:
                return None
            
            value = await self.client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Return as string if not JSON
                return value.decode('utf-8')
                
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache"""
        try:
            if not self.client:
                return False
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Set with expiration
            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                await self.client.setex(key, expire, serialized_value)
            else:
                await self.client.set(key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if not self.client:
                return False
            
            result = await self.client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if not self.client:
                return False
            
            result = await self.client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            if not self.client:
                return False
            
            result = await self.client.expire(key, seconds)
            return result
            
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            if not self.client:
                return -1
            
            return await self.client.ttl(key)
            
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -1
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            if not self.client:
                return []
            
            keys = await self.client.keys(pattern)
            return [key.decode('utf-8') for key in keys]
            
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern}: {e}")
            return []
    
    async def flushdb(self) -> bool:
        """Flush current database"""
        try:
            if not self.client:
                return False
            
            await self.client.flushdb()
            return True
            
        except Exception as e:
            logger.error(f"Error flushing database: {e}")
            return False
    
    async def info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        try:
            if not self.client:
                return {}
            
            info = await self.client.info()
            return info
            
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {}


# Global cache manager
_cache_manager: Optional[CacheManager] = None


async def initialize_redis():
    """Initialize Redis connection pool"""
    global _cache_manager
    
    if not settings.REDIS_URL:
        logger.warning("Redis URL not configured, caching disabled")
        return
    
    try:
        _cache_manager = CacheManager(settings.REDIS_URL)
        await _cache_manager.initialize()
        
        # Set global references
        global _redis_pool, _redis_client
        _redis_pool = _cache_manager.pool
        _redis_client = _cache_manager.client
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        _cache_manager = None


async def close_redis():
    """Close Redis connections"""
    global _cache_manager
    
    if _cache_manager:
        await _cache_manager.close()
        _cache_manager = None


def get_cache_manager() -> Optional[CacheManager]:
    """Get cache manager instance"""
    return _cache_manager


# Cache decorators and utilities
def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from prefix and arguments"""
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(str(arg.id))
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}:{value}")
    
    return ":".join(key_parts)


async def cached(
    key: str,
    expire: Optional[Union[int, timedelta]] = None,
    cache_manager: Optional[CacheManager] = None
):
    """Cache decorator for async functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = cache_manager or _cache_manager
            if not manager:
                return await func(*args, **kwargs)
            
            # Check cache first
            cached_value = await manager.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await manager.set(key, result, expire)
            return result
        
        return wrapper
    return decorator


async def invalidate_cache(pattern: str, cache_manager: Optional[CacheManager] = None):
    """Invalidate cache keys matching pattern"""
    manager = cache_manager or _cache_manager
    if not manager:
        return
    
    try:
        keys = await manager.keys(pattern)
        for key in keys:
            await manager.delete(key)
        logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")


async def cleanup_expired_keys():
    """Clean up expired keys (Redis does this automatically, but we can add custom logic)"""
    manager = _cache_manager
    if not manager:
        return
    
    try:
        # Get all keys
        keys = await manager.keys("*")
        
        # Check TTL for each key
        expired_keys = []
        for key in keys:
            ttl = await manager.ttl(key)
            if ttl == -1:  # No expiration set
                continue
            elif ttl == -2:  # Key doesn't exist (shouldn't happen)
                expired_keys.append(key)
        
        # Remove expired keys
        for key in expired_keys:
            await manager.delete(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache keys")
            
    except Exception as e:
        logger.error(f"Error cleaning up expired keys: {e}")


# Specific cache functions for common use cases
async def cache_user(user_id: str, user_data: Dict[str, Any], expire: int = 3600):
    """Cache user data"""
    key = f"user:{user_id}"
    manager = _cache_manager
    if manager:
        await manager.set(key, user_data, expire)


async def get_cached_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get cached user data"""
    key = f"user:{user_id}"
    manager = _cache_manager
    if manager:
        return await manager.get(key)
    return None


async def cache_service(service_id: str, service_data: Dict[str, Any], expire: int = 1800):
    """Cache service data"""
    key = f"service:{service_id}"
    manager = _cache_manager
    if manager:
        await manager.set(key, service_data, expire)


async def get_cached_service(service_id: str) -> Optional[Dict[str, Any]]:
    """Get cached service data"""
    key = f"service:{service_id}"
    manager = _cache_manager
    if manager:
        return await manager.get(key)
    return None


async def cache_search_results(query: str, results: List[Dict[str, Any]], expire: int = 900):
    """Cache search results"""
    key = f"search:{hash(query)}"
    manager = _cache_manager
    if manager:
        await manager.set(key, results, expire)


async def get_cached_search_results(query: str) -> Optional[List[Dict[str, Any]]]:
    """Get cached search results"""
    key = f"search:{hash(query)}"
    manager = _cache_manager
    if manager:
        return await manager.get(key)
    return None


async def invalidate_user_cache(user_id: str):
    """Invalidate user-related cache"""
    patterns = [
        f"user:{user_id}",
        f"search:*",  # Invalidate search results
        f"service:*"  # Invalidate service cache as user might have updated services
    ]
    
    for pattern in patterns:
        await invalidate_cache(pattern)


async def invalidate_service_cache(service_id: str):
    """Invalidate service-related cache"""
    patterns = [
        f"service:{service_id}",
        f"search:*"  # Invalidate search results
    ]
    
    for pattern in patterns:
        await invalidate_cache(pattern)
