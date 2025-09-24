"""
Global exception handlers for consistent error responses
"""
import logging
import traceback
from datetime import datetime
from typing import Union

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, JWTError
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.errors import (
    ErrorCode,
    create_business_error_response,
    create_error_response,
    create_system_error_response,
    create_validation_error_response,
)

logger = logging.getLogger(__name__)


async def jwt_exception_handler(
        request: Request, exc: Union[JWTError, ExpiredSignatureError]):
    """Handle JWT authentication errors"""
    error_response = create_error_response(
        error_code=ErrorCode.UNAUTHORIZED,
        message="Invalid or expired token",
        request_id=getattr(request.state, 'request_id', None),
        path=str(request.url.path),
        method=request.method
    )

    logger.warning(f"JWT error: {exc} for {request.method} {request.url.path}")

    return JSONResponse(
        status_code=401,
        content=error_response.dict()
    )


async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        details.append({
            "field": field,
            "message": error["msg"],
            "code": error["type"],
            "value": error.get("input")
        })

    error_response = create_validation_error_response(
        details=details,
        request_id=getattr(request.state, 'request_id', None),
        path=str(request.url.path),
        method=request.method
    )

    logger.warning(
        f"Validation error: {exc} for {request.method} {request.url.path}")

    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    error_code = ErrorCode.UNKNOWN_ERROR

    # Map HTTP status codes to error codes
    if exc.status_code == 401:
        error_code = ErrorCode.UNAUTHORIZED
    elif exc.status_code == 403:
        error_code = ErrorCode.FORBIDDEN
    elif exc.status_code == 404:
        error_code = ErrorCode.RESOURCE_NOT_FOUND
    elif exc.status_code == 409:
        error_code = ErrorCode.RESOURCE_ALREADY_EXISTS
    elif exc.status_code == 422:
        error_code = ErrorCode.VALIDATION_ERROR
    elif exc.status_code == 429:
        error_code = ErrorCode.RATE_LIMIT_EXCEEDED

    error_response = create_error_response(
        error_code=error_code,
        message=exc.detail,
        request_id=getattr(request.state, 'request_id', None),
        path=str(request.url.path),
        method=request.method
    )

    logger.warning(
        f"HTTP error {
            exc.status_code}: {
            exc.detail} for {
                request.method} {
                    request.url.path}")

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors"""
    error_response = create_system_error_response(
        message="Database error occurred",
        error_id=f"DB_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        request_id=getattr(request.state, 'request_id', None),
        path=str(request.url.path),
        method=request.method
    )

    logger.error(
        f"Database error: {exc} for {request.method} {request.url.path}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


async def business_exception_handler(request: Request, exc: Exception):
    """Handle business logic errors"""
    error_response = create_business_error_response(
        error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
        message=str(exc),
        request_id=getattr(request.state, 'request_id', None),
        path=str(request.url.path),
        method=request.method
    )

    logger.warning(
        f"Business error: {exc} for {request.method} {request.url.path}")

    return JSONResponse(
        status_code=400,
        content=error_response.dict()
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    error_response = create_system_error_response(
        message="An unexpected error occurred",
        error_id=f"ERR_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        request_id=getattr(request.state, 'request_id', None),
        path=str(request.url.path),
        method=request.method
    )

    logger.error(
        f"Unexpected error: {exc} for {request.method} {request.url.path}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


class BusinessError(Exception):
    """Custom business logic error"""

    def __init__(
            self,
            message: str,
            error_code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ValidationError(Exception):
    """Custom validation error"""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class ResourceNotFoundError(Exception):
    """Resource not found error"""

    def __init__(self, resource_type: str, resource_id: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        message = f"{resource_type} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        super().__init__(message)


class InsufficientPermissionsError(Exception):
    """Insufficient permissions error"""

    def __init__(self, action: str, resource: str = None):
        self.action = action
        self.resource = resource
        message = f"Insufficient permissions to {action}"
        if resource:
            message += f" {resource}"
        super().__init__(message)


class ResourceConflictError(Exception):
    """Resource conflict error"""

    def __init__(self, message: str, conflicting_field: str = None):
        self.message = message
        self.conflicting_field = conflicting_field
        super().__init__(message)


# Export exception classes for use in services
__all__ = [
    'BusinessError',
    'ValidationError',
    'ResourceNotFoundError',
    'InsufficientPermissionsError',
    'ResourceConflictError'
]
