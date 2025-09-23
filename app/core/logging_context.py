"""
Structured logging context for MapleHustleCAN
"""
import logging
import uuid
import time
import json
from typing import Dict, Any, Optional
from contextvars import ContextVar
from datetime import datetime
import traceback
import sys

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
start_time_var: ContextVar[Optional[float]] = ContextVar('start_time', default=None)


class StructuredLogger:
    """Structured logger with context awareness"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_formatter()
    
    def _setup_formatter(self):
        """Setup JSON formatter for structured logging"""
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_context(self) -> Dict[str, Any]:
        """Get current logging context"""
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
            "correlation_id": correlation_id_var.get(),
        }
        
        # Add timing information
        start_time = start_time_var.get()
        if start_time:
            context["duration_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return context
    
    def _log_structured(self, level: str, message: str, **kwargs):
        """Log with structured context"""
        context = self._get_context()
        context.update(kwargs)
        
        log_entry = {
            "level": level,
            "message": message,
            "context": context
        }
        
        # Log as JSON for structured logging
        self.logger.info(json.dumps(log_entry, default=str))
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self._log_structured("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self._log_structured("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self._log_structured("ERROR", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self._log_structured("DEBUG", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context"""
        self._log_structured("CRITICAL", message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        kwargs["exception"] = traceback.format_exc()
        self._log_structured("ERROR", message, **kwargs)


class LoggingContext:
    """Context manager for request logging"""
    
    def __init__(self, request_id: str = None, user_id: str = None, correlation_id: str = None):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.logger = StructuredLogger("request_context")
    
    def __enter__(self):
        """Set context variables"""
        request_id_var.set(self.request_id)
        user_id_var.set(self.user_id)
        correlation_id_var.set(self.correlation_id)
        start_time_var.set(self.start_time)
        
        self.logger.info("Request started", 
                        request_id=self.request_id,
                        user_id=self.user_id,
                        correlation_id=self.correlation_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up context and log request completion"""
        duration = time.time() - self.start_time
        
        if exc_type:
            self.logger.error("Request failed",
                            request_id=self.request_id,
                            user_id=self.user_id,
                            correlation_id=self.correlation_id,
                            duration_ms=round(duration * 1000, 2),
                            exception_type=str(exc_type),
                            exception_message=str(exc_val))
        else:
            self.logger.info("Request completed",
                           request_id=self.request_id,
                           user_id=self.user_id,
                           correlation_id=self.correlation_id,
                           duration_ms=round(duration * 1000, 2))
        
        # Clear context variables
        request_id_var.set(None)
        user_id_var.set(None)
        correlation_id_var.set(None)
        start_time_var.set(None)


def get_logger(name: str) -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger(name)


def set_user_context(user_id: str):
    """Set user context for logging"""
    user_id_var.set(user_id)


def set_correlation_id(correlation_id: str):
    """Set correlation ID for logging"""
    correlation_id_var.set(correlation_id)


def get_request_context() -> Dict[str, Any]:
    """Get current request context"""
    return {
        "request_id": request_id_var.get(),
        "user_id": user_id_var.get(),
        "correlation_id": correlation_id_var.get(),
        "start_time": start_time_var.get()
    }


# Performance logging decorator
def log_performance(logger: StructuredLogger = None):
    """Decorator to log function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not logger:
                func_logger = get_logger(func.__module__)
            else:
                func_logger = logger
            
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                func_logger.info(f"Function {func_name} completed",
                               function=func_name,
                               duration_ms=round(duration * 1000, 2),
                               success=True)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                func_logger.error(f"Function {func_name} failed",
                                function=func_name,
                                duration_ms=round(duration * 1000, 2),
                                success=False,
                                error=str(e),
                                error_type=type(e).__name__)
                raise
        
        return wrapper
    return decorator


# Database query logging
def log_database_query(query: str, params: Dict[str, Any] = None, duration: float = None):
    """Log database query with context"""
    logger = get_logger("database")
    
    log_data = {
        "query": query,
        "params": params,
        "type": "database_query"
    }
    
    if duration:
        log_data["duration_ms"] = round(duration * 1000, 2)
    
    logger.debug("Database query executed", **log_data)


# API request logging
def log_api_request(method: str, path: str, status_code: int, duration: float, user_id: str = None):
    """Log API request with context"""
    logger = get_logger("api")
    
    logger.info("API request processed",
               method=method,
               path=path,
               status_code=status_code,
               duration_ms=round(duration * 1000, 2),
               user_id=user_id,
               type="api_request")


# Security event logging
def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "medium"):
    """Log security event with context"""
    logger = get_logger("security")
    
    logger.warning("Security event detected",
                  event_type=event_type,
                  details=details,
                  severity=severity,
                  type="security_event")


# Business event logging
def log_business_event(event_type: str, entity_type: str, entity_id: str, details: Dict[str, Any] = None):
    """Log business event with context"""
    logger = get_logger("business")
    
    log_data = {
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "type": "business_event"
    }
    
    if details:
        log_data["details"] = details
    
    logger.info("Business event occurred", **log_data)


# Error tracking with context
def log_error(error: Exception, context: Dict[str, Any] = None, level: str = "error"):
    """Log error with full context"""
    logger = get_logger("error")
    
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "level": level,
        "type": "error"
    }
    
    if context:
        error_data["context"] = context
    
    if level == "critical":
        logger.critical("Critical error occurred", **error_data)
    else:
        logger.error("Error occurred", **error_data)
