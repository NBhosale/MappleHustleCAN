"""
Advanced rate limiting configuration for MapleHustleCAN
"""
from typing import Callable

import redis
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings

# Redis connection for distributed rate limiting
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_remote_address_enhanced(request: Request) -> str:
    """Enhanced remote address detection with proxy support"""
    # Check for forwarded IP (when behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct connection
    return get_remote_address(request)


def get_user_id_for_rate_limit(request: Request) -> str:
    """Get user ID for user-specific rate limiting"""
    # Try to get user ID from JWT token or session
    user_id = getattr(request.state, 'user_id', None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address
    return get_remote_address_enhanced(request)


# Create limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address_enhanced,
    storage_uri=settings.REDIS_URL,
    enabled=True
)

# Rate limit configurations
RATE_LIMITS = {
    # Authentication endpoints - very strict
    "login": "5/minute",
    "register": "3/minute",
    "password_reset": "2/minute",
    "password_reset_confirm": "5/minute",
    "verify_email": "3/minute",
    "resend_verification": "2/minute",

    # General API endpoints - moderate
    "api_general": "100/hour",
    "api_strict": "50/hour",

    # File upload endpoints - strict
    "file_upload": "10/minute",
    "image_upload": "20/minute",

    # Search endpoints - moderate
    "search": "60/minute",
    "search_strict": "30/minute",

    # Admin endpoints - very strict
    "admin": "20/hour",
    "admin_strict": "10/hour",

    # Public endpoints - lenient
    "public": "200/hour",
    "public_strict": "100/hour",

    # User-specific limits
    "user_actions": "200/hour",
    "user_creation": "10/hour",
    "user_updates": "50/hour",
}


def get_rate_limit_for_endpoint(endpoint_name: str) -> str:
    """Get rate limit for specific endpoint"""
    return RATE_LIMITS.get(endpoint_name, "100/hour")


def create_rate_limit_decorator(limit: str, key_func: Callable = None):
    """Create rate limit decorator with custom key function"""
    if key_func is None:
        key_func = get_remote_address_enhanced

    return limiter.limit(limit, key_func=key_func)


# Predefined rate limit decorators
rate_limit_login = create_rate_limit_decorator("5/minute")
rate_limit_register = create_rate_limit_decorator("3/minute")
rate_limit_password_reset = create_rate_limit_decorator("2/minute")
rate_limit_file_upload = create_rate_limit_decorator("10/minute")
rate_limit_search = create_rate_limit_decorator("60/minute")
rate_limit_admin = create_rate_limit_decorator("20/hour")
rate_limit_user_actions = create_rate_limit_decorator(
    "200/hour", key_func=get_user_id_for_rate_limit)

# Brute force protection


def check_brute_force_attempts(
        identifier: str,
        max_attempts: int = 5,
        window_minutes: int = 15) -> bool:
    """Check if identifier has exceeded brute force attempts"""
    key = f"brute_force:{identifier}"
    attempts = redis_client.get(key)

    if attempts is None:
        return False

    return int(attempts) >= max_attempts


def record_brute_force_attempt(
        identifier: str,
        max_attempts: int = 5,
        window_minutes: int = 15):
    """Record a brute force attempt"""
    key = f"brute_force:{identifier}"

    # Increment counter
    current_attempts = redis_client.incr(key)

    # Set expiration on first attempt
    if current_attempts == 1:
        redis_client.expire(key, window_minutes * 60)

    return current_attempts


def clear_brute_force_attempts(identifier: str):
    """Clear brute force attempts for identifier"""
    key = f"brute_force:{identifier}"
    redis_client.delete(key)


def enhanced_rate_limit_exceeded_handler(
        request: Request, exc: RateLimitExceeded):
    """Enhanced rate limit exceeded handler with retry information"""
    retry_after = getattr(exc, 'retry_after', 60)

    response_data = {
        "success": False,
        "error": "RATE_LIMIT_EXCEEDED",
        "message": "Too many requests. Please slow down.",
        "retry_after": retry_after,
        "limit": getattr(
            exc,
            'limit',
            "unknown"),
        "remaining": getattr(
            exc,
            'remaining',
            0),
        "reset_time": getattr(
            exc,
            'reset_time',
            None),
        "timestamp": exc.detail.get(
            'timestamp',
            None) if hasattr(
            exc,
            'detail') else None,
        "request_id": getattr(
            request.state,
            'request_id',
            None),
        "path": str(
            request.url.path),
        "method": request.method}

    return JSONResponse(
        status_code=429,
        content=response_data,
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(getattr(exc, 'limit', 'unknown')),
            "X-RateLimit-Remaining": str(getattr(exc, 'remaining', 0)),
            "X-RateLimit-Reset": str(getattr(exc, 'reset_time', None) or 'unknown')
        }
    )

# IP-based blocking for repeated violations


def block_ip_temporarily(ip: str, duration_minutes: int = 60):
    """Block IP address temporarily"""
    key = f"blocked_ip:{ip}"
    redis_client.setex(key, duration_minutes * 60, "blocked")


def is_ip_blocked(ip: str) -> bool:
    """Check if IP is blocked"""
    key = f"blocked_ip:{ip}"
    return redis_client.exists(key) > 0


def unblock_ip(ip: str):
    """Unblock IP address"""
    key = f"blocked_ip:{ip}"
    redis_client.delete(key)


# Rate limit bypass for trusted sources
TRUSTED_IPS = [
    "127.0.0.1",
    "::1",
    "localhost"
]


def is_trusted_ip(ip: str) -> bool:
    """Check if IP is trusted (bypass rate limits)"""
    return ip in TRUSTED_IPS

# Rate limit middleware


class AdvancedRateLimitMiddleware:
    """Advanced rate limiting middleware with IP blocking"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        ip = get_remote_address_enhanced(request)

        # Check if IP is blocked
        if is_ip_blocked(ip):
            response = JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "IP_BLOCKED",
                    "message": "Your IP address has been temporarily blocked due to excessive requests.",
                    "timestamp": None,
                    "request_id": getattr(
                        request.state,
                        'request_id',
                        None),
                    "path": str(
                        request.url.path),
                    "method": request.method})
            await response(scope, receive, send)
            return

        # Skip rate limiting for trusted IPs
        if is_trusted_ip(ip):
            await self.app(scope, receive, send)
            return

        await self.app(scope, receive, send)


# Export main components
__all__ = [
    'limiter',
    'rate_limit_login',
    'rate_limit_register',
    'rate_limit_password_reset',
    'rate_limit_file_upload',
    'rate_limit_search',
    'rate_limit_admin',
    'rate_limit_user_actions',
    'enhanced_rate_limit_exceeded_handler',
    'check_brute_force_attempts',
    'record_brute_force_attempt',
    'clear_brute_force_attempts',
    'block_ip_temporarily',
    'is_ip_blocked',
    'unblock_ip',
    'AdvancedRateLimitMiddleware'
]
