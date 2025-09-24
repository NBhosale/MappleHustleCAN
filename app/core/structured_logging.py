"""
Structured logging for MapleHustleCAN
Provides consistent, structured logging across all routes
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar(
    'request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    'correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'request_id': request_id_var.get(),
            'user_id': user_id_var.get(),
            'correlation_id': correlation_id_var.get(),
        }

        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""

    def __init__(self, app, logger_name: str = "request"):
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        # Set request ID in request state
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Log request
        self.logger.info(
            "Request started",
            extra={
                'extra_fields': {
                    'event_type': 'request_start',
                    'method': request.method,
                    'url': str(
                        request.url),
                    'path': request.url.path,
                    'query_params': dict(
                        request.query_params),
                    'client_ip': request.client.host if request.client else None,
                    'user_agent': request.headers.get('user-agent'),
                    'content_type': request.headers.get('content-type'),
                    'content_length': request.headers.get('content-length'),
                }})

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log response
            self.logger.info(
                "Request completed",
                extra={
                    'extra_fields': {
                        'event_type': 'request_end',
                        'method': request.method,
                        'url': str(
                            request.url),
                        'status_code': response.status_code,
                        'process_time': round(
                            process_time,
                            4),
                        'response_size': response.headers.get('content-length'),
                    }})

            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id

            return response

        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time

            # Log error
            self.logger.error(
                "Request failed",
                extra={
                    'extra_fields': {
                        'event_type': 'request_error',
                        'method': request.method,
                        'url': str(request.url),
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'process_time': round(process_time, 4),
                    }
                },
                exc_info=True
            )

            raise


class BusinessLogicLogger:
    """Logger for business logic events"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_user_action(self, user_id: str, action: str,
                        details: Dict[str, Any] = None):
        """Log user actions"""
        self.logger.info(
            f"User action: {action}",
            extra={
                'extra_fields': {
                    'event_type': 'user_action',
                    'user_id': user_id,
                    'action': action,
                    'details': details or {},
                }
            }
        )

    def log_business_event(self,
                           event_type: str,
                           entity_type: str,
                           entity_id: str,
                           details: Dict[str,
                                         Any] = None):
        """Log business events"""
        self.logger.info(
            f"Business event: {event_type}",
            extra={
                'extra_fields': {
                    'event_type': 'business_event',
                    'business_event_type': event_type,
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    'details': details or {},
                }
            }
        )

    def log_security_event(self,
                           event_type: str,
                           severity: str,
                           details: Dict[str,
                                         Any] = None):
        """Log security events"""
        self.logger.warning(
            f"Security event: {event_type}",
            extra={
                'extra_fields': {
                    'event_type': 'security_event',
                    'security_event_type': event_type,
                    'severity': severity,
                    'details': details or {},
                }
            }
        )

    def log_performance_metric(self,
                               metric_name: str,
                               value: float,
                               unit: str = None,
                               details: Dict[str,
                                             Any] = None):
        """Log performance metrics"""
        self.logger.info(
            f"Performance metric: {metric_name}",
            extra={
                'extra_fields': {
                    'event_type': 'performance_metric',
                    'metric_name': metric_name,
                    'value': value,
                    'unit': unit,
                    'details': details or {},
                }
            }
        )

    def log_database_operation(self,
                               operation: str,
                               table: str,
                               duration: float,
                               details: Dict[str,
                                             Any] = None):
        """Log database operations"""
        self.logger.info(
            f"Database operation: {operation}",
            extra={
                'extra_fields': {
                    'event_type': 'database_operation',
                    'operation': operation,
                    'table': table,
                    'duration': duration,
                    'details': details or {},
                }
            }
        )

    def log_external_api_call(self,
                              service: str,
                              endpoint: str,
                              method: str,
                              status_code: int,
                              duration: float,
                              details: Dict[str,
                                            Any] = None):
        """Log external API calls"""
        self.logger.info(
            f"External API call: {service}",
            extra={
                'extra_fields': {
                    'event_type': 'external_api_call',
                    'service': service,
                    'endpoint': endpoint,
                    'method': method,
                    'status_code': status_code,
                    'duration': duration,
                    'details': details or {},
                }
            }
        )


class APILogger:
    """Logger for API-specific events"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_endpoint_access(
            self,
            endpoint: str,
            method: str,
            user_id: str = None,
            status_code: int = None):
        """Log endpoint access"""
        self.logger.info(
            f"Endpoint accessed: {method} {endpoint}",
            extra={
                'extra_fields': {
                    'event_type': 'endpoint_access',
                    'endpoint': endpoint,
                    'method': method,
                    'user_id': user_id,
                    'status_code': status_code,
                }
            }
        )

    def log_validation_error(
            self,
            endpoint: str,
            errors: list,
            user_id: str = None):
        """Log validation errors"""
        self.logger.warning(
            f"Validation error in {endpoint}",
            extra={
                'extra_fields': {
                    'event_type': 'validation_error',
                    'endpoint': endpoint,
                    'errors': errors,
                    'user_id': user_id,
                }
            }
        )

    def log_authentication_failure(
            self,
            endpoint: str,
            reason: str,
            client_ip: str = None):
        """Log authentication failures"""
        self.logger.warning(
            f"Authentication failure in {endpoint}",
            extra={
                'extra_fields': {
                    'event_type': 'authentication_failure',
                    'endpoint': endpoint,
                    'reason': reason,
                    'client_ip': client_ip,
                }
            }
        )

    def log_rate_limit_exceeded(
            self,
            endpoint: str,
            client_ip: str,
            limit: int):
        """Log rate limit exceeded"""
        self.logger.warning(
            f"Rate limit exceeded for {endpoint}",
            extra={
                'extra_fields': {
                    'event_type': 'rate_limit_exceeded',
                    'endpoint': endpoint,
                    'client_ip': client_ip,
                    'limit': limit,
                }
            }
        )


def setup_structured_logging():
    """Setup structured logging configuration"""

    # Create formatter
    formatter = StructuredFormatter()

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Setup specific loggers
    loggers = [
        'request',
        'business_logic',
        'api',
        'security',
        'performance',
        'database',
        'external_api'
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = True  # Use root logger configuration


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def get_business_logger() -> BusinessLogicLogger:
    """Get business logic logger"""
    return BusinessLogicLogger('business_logic')


def get_api_logger() -> APILogger:
    """Get API logger"""
    return APILogger('api')


# Context managers for logging context
class LoggingContext:
    """Context manager for logging context"""

    def __init__(
            self,
            request_id: str = None,
            user_id: str = None,
            correlation_id: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.correlation_id = correlation_id
        self.old_request_id = None
        self.old_user_id = None
        self.old_correlation_id = None

    def __enter__(self):
        if self.request_id:
            self.old_request_id = request_id_var.get()
            request_id_var.set(self.request_id)

        if self.user_id:
            self.old_user_id = user_id_var.get()
            user_id_var.set(self.user_id)

        if self.correlation_id:
            self.old_correlation_id = correlation_id_var.get()
            correlation_id_var.set(self.correlation_id)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.request_id and self.old_request_id is not None:
            request_id_var.set(self.old_request_id)

        if self.user_id and self.old_user_id is not None:
            user_id_var.set(self.old_user_id)

        if self.correlation_id and self.old_correlation_id is not None:
            correlation_id_var.set(self.old_correlation_id)


# Export main components
__all__ = [
    'StructuredFormatter',
    'RequestLoggingMiddleware',
    'BusinessLogicLogger',
    'APILogger',
    'setup_structured_logging',
    'get_logger',
    'get_business_logger',
    'get_api_logger',
    'LoggingContext',
    'request_id_var',
    'user_id_var',
    'correlation_id_var'
]
