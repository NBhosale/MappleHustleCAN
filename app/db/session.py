"""
Database session management with connection pooling for MapleHustleCAN
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.engine import Engine
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: Engine = None
_SessionLocal: sessionmaker = None


def create_database_engine() -> Engine:
    """Create database engine with optimized connection pooling"""
    
    # Connection pool configuration
    pool_config = {
        "poolclass": QueuePool,
        "pool_size": 20,  # Number of connections to maintain in pool
        "max_overflow": 30,  # Additional connections that can be created
        "pool_pre_ping": True,  # Verify connections before use
        "pool_recycle": 3600,  # Recycle connections every hour
        "pool_timeout": 30,  # Timeout for getting connection from pool
        "echo": settings.DEBUG,  # Log SQL queries in debug mode
    }
    
    # For SQLite, use NullPool to avoid connection issues
    if settings.DATABASE_URL.startswith("sqlite"):
        pool_config["poolclass"] = NullPool
    
    # Create engine
    engine = create_engine(
        settings.DATABASE_URL,
        **pool_config,
        connect_args={
            "check_same_thread": False if settings.DATABASE_URL.startswith("sqlite") else True
        }
    )
    
    # Add connection event listeners
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set SQLite pragmas for better performance"""
        if settings.DATABASE_URL.startswith("sqlite"):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log connection checkout"""
        logger.debug("Connection checked out from pool")
    
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        """Log connection checkin"""
        logger.debug("Connection checked in to pool")
    
    return engine


def get_engine() -> Engine:
    """Get database engine (singleton)"""
    global _engine
    
    if _engine is None:
        _engine = create_database_engine()
        logger.info("Database engine created with connection pooling")
    
    return _engine


def get_session_factory() -> sessionmaker:
    """Get session factory (singleton)"""
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False  # Prevent lazy loading issues
        )
        logger.info("Database session factory created")
    
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[Session, None]:
    """
    Async context manager for database session
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
    except Exception as e:
        logger.error(f"Async database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self):
        self.engine = get_engine()
        self.session_factory = get_session_factory()
        self._connection_count = 0
        self._max_connections = 0
    
    def get_connection_stats(self) -> dict:
        """Get connection pool statistics"""
        pool = self.engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "total_connections": pool.size() + pool.overflow(),
            "available_connections": pool.checkedin(),
            "active_connections": pool.checkedout()
        }
    
    def health_check(self) -> dict:
        """Perform database health check"""
        start_time = time.time()
        
        try:
            with self.session_factory() as session:
                # Simple query to test connection
                result = session.execute("SELECT 1").scalar()
                response_time = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time * 1000, 2),
                    "connection_stats": self.get_connection_stats()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": None
            }
    
    def close_all_connections(self):
        """Close all database connections"""
        try:
            self.engine.dispose()
            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


# Global database manager
_db_manager: DatabaseManager = None


def get_database_manager() -> DatabaseManager:
    """Get database manager instance"""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
    
    return _db_manager


# Connection monitoring and optimization
class ConnectionMonitor:
    """Monitor database connections and optimize performance"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.query_times = []
        self.slow_query_threshold = 1.0  # 1 second
    
    def log_query_time(self, query_time: float, query: str = None):
        """Log query execution time"""
        self.query_times.append(query_time)
        
        if query_time > self.slow_query_threshold:
            logger.warning(f"Slow query detected: {query_time:.2f}s - {query}")
        
        # Keep only last 1000 query times
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]
    
    def get_performance_stats(self) -> dict:
        """Get query performance statistics"""
        if not self.query_times:
            return {"total_queries": 0}
        
        return {
            "total_queries": len(self.query_times),
            "average_time": sum(self.query_times) / len(self.query_times),
            "min_time": min(self.query_times),
            "max_time": max(self.query_times),
            "slow_queries": len([t for t in self.query_times if t > self.slow_query_threshold])
        }


# Query optimization utilities
def optimize_query(session: Session, query):
    """Apply query optimizations"""
    # Add query hints for better performance
    # This would be database-specific optimizations
    return query


def explain_query(session: Session, query) -> str:
    """Explain query execution plan"""
    try:
        # This would be database-specific
        if session.bind.dialect.name == 'postgresql':
            explain_query = f"EXPLAIN ANALYZE {query}"
            result = session.execute(explain_query)
            return "\n".join([str(row) for row in result])
        else:
            return "Query explanation not available for this database"
    except Exception as e:
        return f"Error explaining query: {e}"


# Database transaction utilities
class TransactionManager:
    """Manage database transactions"""
    
    def __init__(self, session: Session):
        self.session = session
        self._transaction_depth = 0
    
    def begin_transaction(self):
        """Begin a new transaction"""
        if self._transaction_depth == 0:
            # Start new transaction
            pass
        self._transaction_depth += 1
    
    def commit_transaction(self):
        """Commit the current transaction"""
        if self._transaction_depth == 1:
            self.session.commit()
        self._transaction_depth = max(0, self._transaction_depth - 1)
    
    def rollback_transaction(self):
        """Rollback the current transaction"""
        if self._transaction_depth == 1:
            self.session.rollback()
        self._transaction_depth = max(0, self._transaction_depth - 1)
    
    def __enter__(self):
        self.begin_transaction()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback_transaction()
        else:
            self.commit_transaction()


def get_transaction_manager(session: Session) -> TransactionManager:
    """Get transaction manager for session"""
    return TransactionManager(session)
