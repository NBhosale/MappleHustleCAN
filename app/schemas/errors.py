"""
Global error response schemas for consistent API error handling
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Standardized error codes"""
    # Authentication & Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"

    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Business Logic Errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"

    # System Errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"

    # File Upload Errors
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    UPLOAD_FAILED = "UPLOAD_FAILED"

    # Payment Errors
    PAYMENT_FAILED = "PAYMENT_FAILED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    PAYMENT_METHOD_INVALID = "PAYMENT_METHOD_INVALID"

    # Booking Errors
    BOOKING_CONFLICT = "BOOKING_CONFLICT"
    BOOKING_NOT_AVAILABLE = "BOOKING_NOT_AVAILABLE"
    BOOKING_EXPIRED = "BOOKING_EXPIRED"

    # Generic
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None
    value: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standardized error response schema"""
    success: bool = False
    error: ErrorCode
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: str
    request_id: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None

    class Config:
        use_enum_values = True


class ValidationErrorResponse(BaseModel):
    """Validation error response schema"""
    success: bool = False
    error: ErrorCode = ErrorCode.VALIDATION_ERROR
    message: str = "Validation failed"
    details: List[ErrorDetail]
    timestamp: str
    request_id: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None

    class Config:
        use_enum_values = True


class BusinessErrorResponse(BaseModel):
    """Business logic error response schema"""
    success: bool = False
    error: ErrorCode
    message: str
    business_rule: Optional[str] = None
    suggested_action: Optional[str] = None
    timestamp: str
    request_id: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None

    class Config:
        use_enum_values = True


class SystemErrorResponse(BaseModel):
    """System error response schema"""
    success: bool = False
    error: ErrorCode = ErrorCode.INTERNAL_ERROR
    message: str = "An internal error occurred"
    error_id: Optional[str] = None
    timestamp: str
    request_id: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None

    class Config:
        use_enum_values = True


class RateLimitErrorResponse(BaseModel):
    """Rate limit error response schema"""
    success: bool = False
    error: ErrorCode = ErrorCode.RATE_LIMIT_EXCEEDED
    message: str = "Rate limit exceeded"
    retry_after: Optional[int] = None
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_time: Optional[str] = None
    timestamp: str
    request_id: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None

    class Config:
        use_enum_values = True


class SuccessResponse(BaseModel):
    """Standardized success response schema"""
    success: bool = True
    message: str
    data: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated response schema"""
    success: bool = True
    message: str = "Success"
    data: List[Any]
    pagination: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: Optional[str] = None


# Error message templates
ERROR_MESSAGES = {
    ErrorCode.UNAUTHORIZED: "Authentication required",
    ErrorCode.FORBIDDEN: "Access denied",
    ErrorCode.TOKEN_EXPIRED: "Token has expired",
    ErrorCode.INVALID_CREDENTIALS: "Invalid credentials",
    ErrorCode.ACCOUNT_LOCKED: "Account is locked",
    ErrorCode.VALIDATION_ERROR: "Validation failed",
    ErrorCode.INVALID_INPUT: "Invalid input provided",
    ErrorCode.MISSING_REQUIRED_FIELD: "Required field is missing",
    ErrorCode.INVALID_FORMAT: "Invalid format",
    ErrorCode.RESOURCE_NOT_FOUND: "Resource not found",
    ErrorCode.RESOURCE_ALREADY_EXISTS: "Resource already exists",
    ErrorCode.BUSINESS_RULE_VIOLATION: "Business rule violation",
    ErrorCode.INSUFFICIENT_PERMISSIONS: "Insufficient permissions",
    ErrorCode.OPERATION_NOT_ALLOWED: "Operation not allowed",
    ErrorCode.INTERNAL_ERROR: "Internal server error",
    ErrorCode.SERVICE_UNAVAILABLE: "Service temporarily unavailable",
    ErrorCode.DATABASE_ERROR: "Database error occurred",
    ErrorCode.EXTERNAL_SERVICE_ERROR: "External service error",
    ErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded",
    ErrorCode.TOO_MANY_REQUESTS: "Too many requests",
    ErrorCode.FILE_TOO_LARGE: "File too large",
    ErrorCode.INVALID_FILE_TYPE: "Invalid file type",
    ErrorCode.UPLOAD_FAILED: "File upload failed",
    ErrorCode.PAYMENT_FAILED: "Payment failed",
    ErrorCode.INSUFFICIENT_FUNDS: "Insufficient funds",
    ErrorCode.PAYMENT_METHOD_INVALID: "Invalid payment method",
    ErrorCode.BOOKING_CONFLICT: "Booking time conflict",
    ErrorCode.BOOKING_NOT_AVAILABLE: "Booking not available",
    ErrorCode.BOOKING_EXPIRED: "Booking has expired",
    ErrorCode.UNKNOWN_ERROR: "Unknown error occurred",
}


def get_error_message(error_code: ErrorCode) -> str:
    """Get standardized error message for error code"""
    return ERROR_MESSAGES.get(error_code, "An error occurred")


def create_error_response(
    error_code: ErrorCode,
    message: Optional[str] = None,
    details: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None
) -> ErrorResponse:
    """Create standardized error response"""
    return ErrorResponse(
        error=error_code,
        message=message or get_error_message(error_code),
        details=details,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id,
        path=path,
        method=method
    )


def create_validation_error_response(
    details: List[ErrorDetail],
    request_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None
) -> ValidationErrorResponse:
    """Create validation error response"""
    return ValidationErrorResponse(
        details=details,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id,
        path=path,
        method=method
    )


def create_business_error_response(
    error_code: ErrorCode,
    message: str,
    business_rule: Optional[str] = None,
    suggested_action: Optional[str] = None,
    request_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None
) -> BusinessErrorResponse:
    """Create business error response"""
    return BusinessErrorResponse(
        error=error_code,
        message=message,
        business_rule=business_rule,
        suggested_action=suggested_action,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id,
        path=path,
        method=method
    )


def create_system_error_response(
    message: str = "An internal error occurred",
    error_id: Optional[str] = None,
    request_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None
) -> SystemErrorResponse:
    """Create system error response"""
    return SystemErrorResponse(
        message=message,
        error_id=error_id,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id,
        path=path,
        method=method
    )


def create_rate_limit_error_response(
    retry_after: Optional[int] = None,
    limit: Optional[int] = None,
    remaining: Optional[int] = None,
    reset_time: Optional[str] = None,
    request_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None
) -> RateLimitErrorResponse:
    """Create rate limit error response"""
    return RateLimitErrorResponse(
        retry_after=retry_after,
        limit=limit,
        remaining=remaining,
        reset_time=reset_time,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id,
        path=path,
        method=method
    )


def create_success_response(
    message: str = "Success",
    data: Optional[Any] = None,
    meta: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> SuccessResponse:
    """Create success response"""
    return SuccessResponse(
        message=message,
        data=data,
        meta=meta,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id
    )


def create_paginated_response(
    data: List[Any],
    pagination: Dict[str, Any],
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> PaginatedResponse:
    """Create paginated response"""
    return PaginatedResponse(
        data=data,
        pagination=pagination,
        message=message,
        meta=meta,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id
    )
