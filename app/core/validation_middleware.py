"""
Validation middleware for business rule enforcement
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BusinessRuleValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce business rules and validation
    """
    
    def __init__(self, app, strict_mode: bool = True):
        super().__init__(app)
        self.strict_mode = strict_mode
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and apply business rule validation
        """
        try:
            # Log request for audit
            await self._log_request(request)
            
            # Apply pre-request validation
            await self._validate_request(request)
            
            # Process request
            response = await call_next(request)
            
            # Apply post-response validation
            await self._validate_response(request, response)
            
            return response
            
        except HTTPException as e:
            logger.warning(f"Validation error: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail, "type": "validation_error"}
            )
        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}")
            if self.strict_mode:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Internal validation error", "type": "system_error"}
                )
            return await call_next(request)
    
    async def _log_request(self, request: Request):
        """Log request for audit purposes"""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} with {user_agent}"
        )
    
    async def _validate_request(self, request: Request):
        """Apply pre-request validation rules"""
        # Rate limiting validation (basic)
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._validate_rate_limits(request)
        
        # Content type validation
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._validate_content_type(request)
        
        # Path-specific validation
        await self._validate_path_specific_rules(request)
    
    async def _validate_response(self, request: Request, response):
        """Apply post-response validation rules"""
        # Log response status
        if response.status_code >= 400:
            logger.warning(
                f"Error response: {response.status_code} for {request.method} {request.url.path}"
            )
    
    async def _validate_rate_limits(self, request: Request):
        """Basic rate limiting validation"""
        # This would integrate with your rate limiting system
        # For now, just log the attempt
        logger.debug(f"Rate limit check for {request.client.host}")
    
    async def _validate_content_type(self, request: Request):
        """Validate content type for requests with body"""
        content_type = request.headers.get("content-type", "")
        
        if request.method in ["POST", "PUT", "PATCH"]:
            if not content_type.startswith("application/json"):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Content-Type must be application/json"
                )
    
    async def _validate_path_specific_rules(self, request: Request):
        """Apply path-specific validation rules"""
        path = request.url.path
        
        # Booking-specific validation
        if "/bookings" in path and request.method == "POST":
            await self._validate_booking_request(request)
        
        # Order-specific validation
        if "/orders" in path and request.method == "POST":
            await self._validate_order_request(request)
        
        # Service availability validation
        if "/services/availability" in path and request.method == "POST":
            await self._validate_availability_request(request)
    
    async def _validate_booking_request(self, request: Request):
        """Validate booking request business rules"""
        # This would parse and validate the booking request body
        # For now, just log the validation attempt
        logger.debug("Validating booking request business rules")
    
    async def _validate_order_request(self, request: Request):
        """Validate order request business rules"""
        # This would parse and validate the order request body
        logger.debug("Validating order request business rules")
    
    async def _validate_availability_request(self, request: Request):
        """Validate availability request business rules"""
        # This would parse and validate the availability request body
        logger.debug("Validating availability request business rules")


def create_validation_error_response(
    detail: str,
    field: str = None,
    error_code: str = None
) -> JSONResponse:
    """
    Create a standardized validation error response
    """
    error_data = {
        "detail": detail,
        "type": "validation_error"
    }
    
    if field:
        error_data["field"] = field
    
    if error_code:
        error_data["error_code"] = error_code
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_data
    )


def create_business_rule_error_response(
    detail: str,
    rule: str = None,
    suggestion: str = None
) -> JSONResponse:
    """
    Create a standardized business rule error response
    """
    error_data = {
        "detail": detail,
        "type": "business_rule_error"
    }
    
    if rule:
        error_data["rule"] = rule
    
    if suggestion:
        error_data["suggestion"] = suggestion
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_data
    )
