"""
Error tracking and monitoring for MapleHustleCAN using Sentry
"""
import logging
import os
from typing import Dict, Any, Optional
from functools import wraps
import traceback
import time

from app.core.config import settings
from app.core.logging_context import get_logger, get_request_context

logger = get_logger(__name__)

# Initialize Sentry if configured
sentry_sdk = None
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        # Configure Sentry
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            release=settings.VERSION,
            integrations=[
                FastApiIntegration(auto_enabling_instrumentations=True),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                ),
            ],
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            send_default_pii=False,  # Don't send personally identifiable information
            attach_stacktrace=True,
            before_send=before_send_filter,
            before_send_transaction=before_send_transaction_filter,
        )
        
        logger.info("Sentry error tracking initialized")
        
    except ImportError:
        logger.warning("Sentry SDK not installed, error tracking disabled")
        sentry_sdk = None
else:
    logger.info("Sentry DSN not configured, error tracking disabled")


def before_send_filter(event, hint):
    """Filter events before sending to Sentry"""
    # Filter out health check requests
    if 'request' in event and event['request'].get('url'):
        url = event['request']['url']
        if '/health/' in url or '/metrics' in url:
            return None
    
    # Filter out rate limit errors (too noisy)
    if 'exception' in event:
        exc = event['exception']
        if exc.get('type') == 'RateLimitExceeded':
            return None
    
    # Add custom context
    context = get_request_context()
    if context['request_id']:
        event['tags']['request_id'] = context['request_id']
    if context['user_id']:
        event['tags']['user_id'] = context['user_id']
    if context['correlation_id']:
        event['tags']['correlation_id'] = context['correlation_id']
    
    return event


def before_send_transaction_filter(event, hint):
    """Filter transactions before sending to Sentry"""
    # Filter out health check transactions
    if event.get('transaction') and '/health/' in event['transaction']:
        return None
    
    return event


class ErrorTracker:
    """Error tracking utilities"""
    
    @staticmethod
    def capture_exception(error: Exception, context: Dict[str, Any] = None):
        """Capture exception in Sentry"""
        if not sentry_sdk:
            return
        
        with sentry_sdk.push_scope() as scope:
            # Add context
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            
            # Add request context
            req_context = get_request_context()
            if req_context['request_id']:
                scope.set_tag('request_id', req_context['request_id'])
            if req_context['user_id']:
                scope.set_tag('user_id', req_context['user_id'])
            if req_context['correlation_id']:
                scope.set_tag('correlation_id', req_context['correlation_id'])
            
            # Capture the exception
            sentry_sdk.capture_exception(error)
    
    @staticmethod
    def capture_message(message: str, level: str = "error", context: Dict[str, Any] = None):
        """Capture message in Sentry"""
        if not sentry_sdk:
            return
        
        with sentry_sdk.push_scope() as scope:
            # Add context
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            
            # Add request context
            req_context = get_request_context()
            if req_context['request_id']:
                scope.set_tag('request_id', req_context['request_id'])
            if req_context['user_id']:
                scope.set_tag('user_id', req_context['user_id'])
            if req_context['correlation_id']:
                scope.set_tag('correlation_id', req_context['correlation_id'])
            
            # Capture the message
            sentry_sdk.capture_message(message, level=level)
    
    @staticmethod
    def set_user_context(user_id: str, email: str = None, role: str = None):
        """Set user context in Sentry"""
        if not sentry_sdk:
            return
        
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "role": role
        })
    
    @staticmethod
    def set_tag(key: str, value: str):
        """Set tag in Sentry"""
        if not sentry_sdk:
            return
        
        sentry_sdk.set_tag(key, value)
    
    @staticmethod
    def set_context(key: str, value: Dict[str, Any]):
        """Set context in Sentry"""
        if not sentry_sdk:
            return
        
        sentry_sdk.set_context(key, value)
    
    @staticmethod
    def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: Dict[str, Any] = None):
        """Add breadcrumb to Sentry"""
        if not sentry_sdk:
            return
        
        breadcrumb = {
            "message": message,
            "category": category,
            "level": level,
            "timestamp": time.time()
        }
        
        if data:
            breadcrumb["data"] = data
        
        sentry_sdk.add_breadcrumb(breadcrumb)


def track_errors(func):
    """Decorator to automatically track errors in Sentry"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Add function context
            context = {
                "function": f"{func.__module__}.{func.__name__}",
                "args": str(args)[:500],  # Limit size
                "kwargs": str(kwargs)[:500]  # Limit size
            }
            
            ErrorTracker.capture_exception(e, context)
            raise
    
    return wrapper


def track_async_errors(func):
    """Decorator to automatically track errors in async functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Add function context
            context = {
                "function": f"{func.__module__}.{func.__name__}",
                "args": str(args)[:500],  # Limit size
                "kwargs": str(kwargs)[:500]  # Limit size
            }
            
            ErrorTracker.capture_exception(e, context)
            raise
    
    return wrapper


class PerformanceTracker:
    """Performance tracking utilities"""
    
    @staticmethod
    def start_transaction(name: str, op: str = "function"):
        """Start a performance transaction"""
        if not sentry_sdk:
            return None
        
        return sentry_sdk.start_transaction(name=name, op=op)
    
    @staticmethod
    def start_span(transaction, name: str, op: str = "function", description: str = None):
        """Start a span within a transaction"""
        if not sentry_sdk or not transaction:
            return None
        
        return transaction.start_span(name=name, op=op, description=description)
    
    @staticmethod
    def finish_transaction(transaction, status: str = "ok"):
        """Finish a performance transaction"""
        if not sentry_sdk or not transaction:
            return
        
        transaction.set_status(status)
        transaction.finish()


def track_performance(name: str, op: str = "function"):
    """Decorator to track function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            transaction = PerformanceTracker.start_transaction(f"{func.__module__}.{func.__name__}", op)
            
            try:
                result = func(*args, **kwargs)
                PerformanceTracker.finish_transaction(transaction, "ok")
                return result
            except Exception as e:
                PerformanceTracker.finish_transaction(transaction, "internal_error")
                raise
        
        return wrapper
    return decorator


def track_async_performance(name: str, op: str = "function"):
    """Decorator to track async function performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            transaction = PerformanceTracker.start_transaction(f"{func.__module__}.{func.__name__}", op)
            
            try:
                result = await func(*args, **kwargs)
                PerformanceTracker.finish_transaction(transaction, "ok")
                return result
            except Exception as e:
                PerformanceTracker.finish_transaction(transaction, "internal_error")
                raise
        
        return wrapper
    return decorator


class DatabaseErrorTracker:
    """Database-specific error tracking"""
    
    @staticmethod
    def track_query_error(query: str, params: Dict[str, Any], error: Exception):
        """Track database query errors"""
        context = {
            "query": query[:1000],  # Limit query length
            "params": params,
            "error_type": "database_query"
        }
        
        ErrorTracker.capture_exception(error, context)
    
    @staticmethod
    def track_connection_error(error: Exception):
        """Track database connection errors"""
        context = {
            "error_type": "database_connection"
        }
        
        ErrorTracker.capture_exception(error, context)


class APITracker:
    """API-specific error tracking"""
    
    @staticmethod
    def track_request_error(method: str, path: str, status_code: int, error: Exception):
        """Track API request errors"""
        context = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "error_type": "api_request"
        }
        
        ErrorTracker.capture_exception(error, context)
    
    @staticmethod
    def track_validation_error(field: str, value: Any, error: Exception):
        """Track validation errors"""
        context = {
            "field": field,
            "value": str(value)[:500],  # Limit value length
            "error_type": "validation"
        }
        
        ErrorTracker.capture_exception(error, context)


class SecurityTracker:
    """Security-specific error tracking"""
    
    @staticmethod
    def track_security_event(event_type: str, details: Dict[str, Any], severity: str = "medium"):
        """Track security events"""
        context = {
            "event_type": event_type,
            "details": details,
            "severity": severity,
            "error_type": "security_event"
        }
        
        ErrorTracker.capture_message(f"Security event: {event_type}", "warning", context)
    
    @staticmethod
    def track_authentication_error(user_id: str, error: Exception):
        """Track authentication errors"""
        context = {
            "user_id": user_id,
            "error_type": "authentication"
        }
        
        ErrorTracker.capture_exception(error, context)
    
    @staticmethod
    def track_authorization_error(user_id: str, resource: str, error: Exception):
        """Track authorization errors"""
        context = {
            "user_id": user_id,
            "resource": resource,
            "error_type": "authorization"
        }
        
        ErrorTracker.capture_exception(error, context)


# Global error tracker instance
error_tracker = ErrorTracker()
performance_tracker = PerformanceTracker()
database_tracker = DatabaseErrorTracker()
api_tracker = APITracker()
security_tracker = SecurityTracker()
