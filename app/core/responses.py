"""
Standardized API response format for consistent error handling and success responses.
"""

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Optional, Dict
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standardized API response format."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


def success_response(
    data: Any = None,
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized success response."""
    response = APIResponse(
        success=True,
        message=message,
        data=data,
        meta=meta
    )
    return JSONResponse(content=response.dict())


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response."""
    response = ErrorResponse(
        success=False,
        message=message,
        error_code=error_code,
        details=details
    )
    return JSONResponse(
        status_code=status_code,
        content=response.dict()
    )


def validation_error_response(
    errors: Dict[str, Any],
    message: str = "Validation failed"
) -> JSONResponse:
    """Create a standardized validation error response."""
    response = APIResponse(
        success=False,
        message=message,
        errors=errors
    )
    return JSONResponse(
        status_code=422,
        content=response.dict()
    )


def not_found_response(
    resource: str = "Resource",
    message: Optional[str] = None
) -> JSONResponse:
    """Create a standardized not found response."""
    if not message:
        message = f"{resource} not found"
    
    return error_response(
        message=message,
        status_code=404,
        error_code="NOT_FOUND"
    )


def unauthorized_response(
    message: str = "Unauthorized access"
) -> JSONResponse:
    """Create a standardized unauthorized response."""
    return error_response(
        message=message,
        status_code=401,
        error_code="UNAUTHORIZED"
    )


def forbidden_response(
    message: str = "Access forbidden"
) -> JSONResponse:
    """Create a standardized forbidden response."""
    return error_response(
        message=message,
        status_code=403,
        error_code="FORBIDDEN"
    )


def conflict_response(
    message: str = "Resource conflict",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized conflict response."""
    return error_response(
        message=message,
        status_code=409,
        error_code="CONFLICT",
        details=details
    )


def server_error_response(
    message: str = "Internal server error"
) -> JSONResponse:
    """Create a standardized server error response."""
    return error_response(
        message=message,
        status_code=500,
        error_code="INTERNAL_ERROR"
    )


def rate_limit_response(
    message: str = "Too many requests"
) -> JSONResponse:
    """Create a standardized rate limit response."""
    return error_response(
        message=message,
        status_code=429,
        error_code="RATE_LIMIT_EXCEEDED"
    )


# Custom HTTPException for consistent error handling
class APIException(HTTPException):
    """Custom HTTPException with standardized error format."""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.details = details
        super().__init__(status_code=status_code, detail=message)


# Global exception handlers
def handle_api_exception(exc: APIException) -> JSONResponse:
    """Handle custom API exceptions."""
    return error_response(
        message=str(exc.detail),
        status_code=exc.status_code,
        error_code=exc.error_code,
        details=exc.details
    )


def handle_http_exception(exc: HTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    return error_response(
        message=str(exc.detail),
        status_code=exc.status_code
    )


def handle_validation_exception(exc) -> JSONResponse:
    """Handle Pydantic validation exceptions."""
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors[field] = error["msg"]
    
    return validation_error_response(errors)


def handle_generic_exception(exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return server_error_response(
        message="An unexpected error occurred"
    )
