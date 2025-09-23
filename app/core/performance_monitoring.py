"""
Performance monitoring and metrics collection for MapleHustleCAN
"""
import time
import psutil
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import wraps
import asyncio
import threading

from app.core.config import settings
from app.core.logging_context import get_logger, get_request_context
from app.core.cache import get_cache_manager

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    unit: str = "ms"


@dataclass
class SystemMetric:
    """System metric data structure"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    timestamp: datetime


class MetricsCollector:
    """Collects and stores performance metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=1000)
        self.lock = threading.Lock()
    
    def add_metric(self, metric: PerformanceMetric):
        """Add a performance metric"""
        with self.lock:
            self.metrics.append(metric)
    
    def add_system_metric(self, metric: SystemMetric):
        """Add a system metric"""
        with self.lock:
            self.system_metrics.append(metric)
    
    def get_metrics(self, name: str = None, since: datetime = None) -> List[PerformanceMetric]:
        """Get metrics filtered by name and time"""
        with self.lock:
            metrics = list(self.metrics)
        
        if name:
            metrics = [m for m in metrics if m.name == name]
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics
    
    def get_system_metrics(self, since: datetime = None) -> List[SystemMetric]:
        """Get system metrics since a specific time"""
        with self.lock:
            metrics = list(self.system_metrics)
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics
    
    def get_metric_stats(self, name: str, since: datetime = None) -> Dict[str, float]:
        """Get statistics for a specific metric"""
        metrics = self.get_metrics(name, since)
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": self._percentile(values, 50),
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99)
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]


class PerformanceMonitor:
    """Main performance monitoring class"""
    
    def __init__(self):
        self.collector = MetricsCollector()
        self.start_time = time.time()
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        self.lock = threading.Lock()
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record API request metrics"""
        with self.lock:
            key = f"{method} {path}"
            self.request_counts[key] += 1
            
            if status_code >= 400:
                self.error_counts[key] += 1
            
            self.response_times[key].append(duration)
            
            # Keep only last 1000 response times per endpoint
            if len(self.response_times[key]) > 1000:
                self.response_times[key] = self.response_times[key][-1000:]
        
        # Record as metric
        metric = PerformanceMetric(
            name="api_request_duration",
            value=duration * 1000,  # Convert to milliseconds
            timestamp=datetime.utcnow(),
            tags={
                "method": method,
                "path": path,
                "status_code": str(status_code)
            },
            unit="ms"
        )
        self.collector.add_metric(metric)
    
    def record_database_query(self, query_type: str, duration: float, rows_affected: int = None):
        """Record database query metrics"""
        metric = PerformanceMetric(
            name="database_query_duration",
            value=duration * 1000,  # Convert to milliseconds
            timestamp=datetime.utcnow(),
            tags={
                "query_type": query_type,
                "rows_affected": str(rows_affected) if rows_affected else "unknown"
            },
            unit="ms"
        )
        self.collector.add_metric(metric)
    
    def record_cache_operation(self, operation: str, duration: float, hit: bool = None):
        """Record cache operation metrics"""
        metric = PerformanceMetric(
            name="cache_operation_duration",
            value=duration * 1000,  # Convert to milliseconds
            timestamp=datetime.utcnow(),
            tags={
                "operation": operation,
                "hit": str(hit) if hit is not None else "unknown"
            },
            unit="ms"
        )
        self.collector.add_metric(metric)
    
    def record_business_operation(self, operation: str, duration: float, entity_type: str = None):
        """Record business operation metrics"""
        metric = PerformanceMetric(
            name="business_operation_duration",
            value=duration * 1000,  # Convert to milliseconds
            timestamp=datetime.utcnow(),
            tags={
                "operation": operation,
                "entity_type": entity_type or "unknown"
            },
            unit="ms"
        )
        self.collector.add_metric(metric)
    
    def collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_available_mb = memory.available / 1024 / 1024
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_free_gb = disk.free / 1024 / 1024 / 1024
            
            system_metric = SystemMetric(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                timestamp=datetime.utcnow()
            )
            
            self.collector.add_system_metric(system_metric)
            
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        with self.lock:
            total_requests = sum(self.request_counts.values())
            total_errors = sum(self.error_counts.values())
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            # Calculate average response times
            avg_response_times = {}
            for endpoint, times in self.response_times.items():
                if times:
                    avg_response_times[endpoint] = sum(times) / len(times)
        
        # Get recent metrics
        since = datetime.utcnow() - timedelta(minutes=5)
        api_metrics = self.collector.get_metric_stats("api_request_duration", since)
        db_metrics = self.collector.get_metric_stats("database_query_duration", since)
        cache_metrics = self.collector.get_metric_stats("cache_operation_duration", since)
        
        # Get system metrics
        system_metrics = self.collector.get_system_metrics(since)
        latest_system = system_metrics[-1] if system_metrics else None
        
        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate_percent": round(error_rate, 2),
            "avg_response_times": avg_response_times,
            "api_metrics": api_metrics,
            "database_metrics": db_metrics,
            "cache_metrics": cache_metrics,
            "system_metrics": {
                "cpu_percent": latest_system.cpu_percent if latest_system else 0,
                "memory_percent": latest_system.memory_percent if latest_system else 0,
                "memory_used_mb": latest_system.memory_used_mb if latest_system else 0,
                "disk_percent": latest_system.disk_percent if latest_system else 0
            } if latest_system else None
        }
    
    def get_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each endpoint"""
        with self.lock:
            stats = {}
            
            for endpoint, count in self.request_counts.items():
                error_count = self.error_counts.get(endpoint, 0)
                response_times = self.response_times.get(endpoint, [])
                
                stats[endpoint] = {
                    "request_count": count,
                    "error_count": error_count,
                    "error_rate_percent": round((error_count / count * 100) if count > 0 else 0, 2),
                    "avg_response_time_ms": round(sum(response_times) / len(response_times) * 1000, 2) if response_times else 0,
                    "min_response_time_ms": round(min(response_times) * 1000, 2) if response_times else 0,
                    "max_response_time_ms": round(max(response_times) * 1000, 2) if response_times else 0
                }
            
            return stats


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(name: str, tags: Dict[str, str] = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metric
                metric = PerformanceMetric(
                    name=name,
                    value=duration * 1000,  # Convert to milliseconds
                    timestamp=datetime.utcnow(),
                    tags=tags or {},
                    unit="ms"
                )
                performance_monitor.collector.add_metric(metric)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metric
                error_tags = (tags or {}).copy()
                error_tags["error"] = "true"
                
                metric = PerformanceMetric(
                    name=f"{name}_error",
                    value=duration * 1000,
                    timestamp=datetime.utcnow(),
                    tags=error_tags,
                    unit="ms"
                )
                performance_monitor.collector.add_metric(metric)
                
                raise
        
        return wrapper
    return decorator


def monitor_async_performance(name: str, tags: Dict[str, str] = None):
    """Decorator to monitor async function performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record metric
                metric = PerformanceMetric(
                    name=name,
                    value=duration * 1000,  # Convert to milliseconds
                    timestamp=datetime.utcnow(),
                    tags=tags or {},
                    unit="ms"
                )
                performance_monitor.collector.add_metric(metric)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metric
                error_tags = (tags or {}).copy()
                error_tags["error"] = "true"
                
                metric = PerformanceMetric(
                    name=f"{name}_error",
                    value=duration * 1000,
                    timestamp=datetime.utcnow(),
                    tags=error_tags,
                    unit="ms"
                )
                performance_monitor.collector.add_metric(metric)
                
                raise
        
        return wrapper
    return decorator


class DatabasePerformanceTracker:
    """Database performance tracking"""
    
    @staticmethod
    def track_query(query_type: str, duration: float, rows_affected: int = None):
        """Track database query performance"""
        performance_monitor.record_database_query(query_type, duration, rows_affected)
    
    @staticmethod
    def track_connection_pool():
        """Track database connection pool metrics"""
        try:
            from app.db.session import get_database_manager
            db_manager = get_database_manager()
            stats = db_manager.get_connection_stats()
            
            # Record connection pool metrics
            for key, value in stats.items():
                metric = PerformanceMetric(
                    name="database_connection_pool",
                    value=float(value),
                    timestamp=datetime.utcnow(),
                    tags={"metric": key},
                    unit="count"
                )
                performance_monitor.collector.add_metric(metric)
                
        except Exception as e:
            logger.error("Failed to track database connection pool", error=str(e))


class CachePerformanceTracker:
    """Cache performance tracking"""
    
    @staticmethod
    def track_operation(operation: str, duration: float, hit: bool = None):
        """Track cache operation performance"""
        performance_monitor.record_cache_operation(operation, duration, hit)
    
    @staticmethod
    def track_cache_stats():
        """Track cache statistics"""
        try:
            cache_manager = get_cache_manager()
            if cache_manager:
                # This would be implemented in the cache manager
                pass
        except Exception as e:
            logger.error("Failed to track cache stats", error=str(e))


class BackgroundMetricsCollector:
    """Background task to collect metrics"""
    
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.running = False
        self.thread = None
    
    def start(self):
        """Start background metrics collection"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
        self.thread.start()
        logger.info("Background metrics collection started")
    
    def stop(self):
        """Stop background metrics collection"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Background metrics collection stopped")
    
    def _collect_metrics_loop(self):
        """Main metrics collection loop"""
        while self.running:
            try:
                # Collect system metrics
                performance_monitor.collect_system_metrics()
                
                # Track database connection pool
                DatabasePerformanceTracker.track_connection_pool()
                
                # Track cache stats
                CachePerformanceTracker.track_cache_stats()
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error("Error in metrics collection loop", error=str(e))
                time.sleep(5)  # Short sleep on error


# Global background metrics collector
background_collector = BackgroundMetricsCollector()


def start_performance_monitoring():
    """Start performance monitoring"""
    background_collector.start()


def stop_performance_monitoring():
    """Stop performance monitoring"""
    background_collector.stop()


def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics"""
    return performance_monitor.get_performance_summary()


def get_endpoint_performance() -> Dict[str, Dict[str, Any]]:
    """Get endpoint performance statistics"""
    return performance_monitor.get_endpoint_stats()
