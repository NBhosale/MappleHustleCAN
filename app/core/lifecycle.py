"""
Application lifecycle management for MapleHustleCAN
"""
import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings
from app.core.security_monitoring import get_security_monitor

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Manages application lifecycle events"""

    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.background_tasks = set()
        self.cleanup_tasks = []

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(
                f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_event.set()

        # Register signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # On Windows, also handle SIGBREAK
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)

    async def startup_tasks(self):
        """Tasks to run on application startup"""
        logger.info("Starting application lifecycle tasks...")

        # Initialize security monitoring
        if settings.SECURITY_MONITORING_ENABLED:
            from app.core.security_monitoring import (
                initialize_security_monitoring,
            )
            monitoring_config = {
                "enabled": True,
                "anomaly_detection": True,
                "alerting": settings.SECURITY_ALERTS_ENABLED,
                "email_alerts": bool(settings.ALERT_EMAIL),
                "webhook_alerts": bool(settings.ALERT_WEBHOOK_URL),
                "thresholds": {
                    "brute_force_attempts": 10,
                    "ddos_requests": 100,
                    "sql_injection_attempts": 5
                },
                "alert_cooldown": 300
            }
            initialize_security_monitoring(monitoring_config)
            logger.info("Security monitoring initialized")

        # Initialize Redis connection pool
        if settings.REDIS_URL:
            try:
                from app.core.cache import initialize_redis
                await initialize_redis()
                logger.info("Redis connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}")

        # Initialize database connection pool
        await self._initialize_database_pool()

        # Start background tasks
        await self._start_background_tasks()

        logger.info("Application startup completed")

    async def shutdown_tasks(self):
        """Tasks to run on application shutdown"""
        logger.info("Starting application shutdown tasks...")

        # Cancel all background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Run cleanup tasks
        for cleanup_task in self.cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(cleanup_task):
                    await cleanup_task()
                else:
                    cleanup_task()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

        # Close database connections
        await self._close_database_connections()

        # Close Redis connections
        if settings.REDIS_URL:
            try:
                from app.core.cache import close_redis
                await close_redis()
                logger.info("Redis connections closed")
            except Exception as e:
                logger.error(f"Error closing Redis connections: {e}")

        logger.info("Application shutdown completed")

    async def _initialize_database_pool(self):
        """Initialize database connection pool"""
        try:
            from app.db import engine

            # Configure connection pool
            if hasattr(engine, 'pool'):
                engine.pool._recycle = 3600  # Recycle connections every hour
                engine.pool._pre_ping = True  # Verify connections before use
                engine.pool._pool_timeout = 30  # Timeout for getting connection

                logger.info(
                    f"Database connection pool initialized: {
                        engine.pool.size()} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")

    async def _start_background_tasks(self):
        """Start background tasks"""
        # Start security monitoring cleanup task
        if settings.SECURITY_MONITORING_ENABLED:
            task = asyncio.create_task(self._security_cleanup_task())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

        # Start cache cleanup task
        if settings.REDIS_URL:
            task = asyncio.create_task(self._cache_cleanup_task())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

        # Start metrics collection task
        task = asyncio.create_task(self._metrics_collection_task())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def _security_cleanup_task(self):
        """Background task for security monitoring cleanup"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Clean up old security events
                monitor = get_security_monitor()
                if monitor:
                    # This would clean up old events in a real implementation
                    pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in security cleanup task: {e}")

    async def _cache_cleanup_task(self):
        """Background task for cache cleanup"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(600)  # Run every 10 minutes

                # Clean up expired cache entries
                if settings.REDIS_URL:
                    from app.core.cache import cleanup_expired_keys
                    await cleanup_expired_keys()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")

    async def _metrics_collection_task(self):
        """Background task for metrics collection"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # Run every minute

                # Collect and store metrics
                # This would collect application metrics in a real
                # implementation

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection task: {e}")

    async def _close_database_connections(self):
        """Close database connections"""
        try:
            from app.db import engine
            engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

    def add_cleanup_task(self, task):
        """Add a cleanup task to run on shutdown"""
        self.cleanup_tasks.append(task)


# Global lifecycle manager
lifecycle_manager = LifecycleManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager
    """
    # Setup signal handlers
    lifecycle_manager.setup_signal_handlers()

    # Startup
    await lifecycle_manager.startup_tasks()

    try:
        yield
    finally:
        # Shutdown
        await lifecycle_manager.shutdown_tasks()


def get_lifecycle_manager() -> LifecycleManager:
    """Get the lifecycle manager instance"""
    return lifecycle_manager
