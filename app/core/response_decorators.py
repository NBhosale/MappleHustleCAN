"""
Response decorators for consistent JSON responses
"""

from functools import wraps
from typing import Any, Dict, Optional, Union, List
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.schemas.errors import (
    create_success_response,
    create_paginated_response,
    create_error_response,
    ErrorCode
)
from app.core.structured_logging import get_api_logger

logger = get_api_logger()


def standardize_response(func):
    """Decorator to standardize API responses"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            
            # If result is already a JSONResponse, return it
            if isinstance(result, JSONResponse):
                return result
            
            # If result is a dict, wrap it in success response
            if isinstance(result, dict):
                return JSONResponse(
                    content=create_success_response(
                        message="Success",
                        data=result
                    ).dict()
                )
            
            # If result is a list, wrap it in success response
            if isinstance(result, list):
                return JSONResponse(
                    content=create_success_response(
                        message="Success",
                        data=result
                    ).dict()
                )
            
            # For other types, wrap in success response
            return JSONResponse(
                content=create_success_response(
                    message="Success",
                    data=result
                ).dict()
            )
            
        except HTTPException as e:
            # Re-raise HTTP exceptions as they're already properly formatted
            raise e
            
        except Exception as e:
            # Log the error
            logger.logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            
            # Return standardized error response
            error_response = create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="An internal error occurred"
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.dict()
            )
    
    return wrapper


def paginated_response(page: int = 1, limit: int = 10):
    """Decorator for paginated responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                if isinstance(result, dict) and 'items' in result:
                    # Result is already paginated
                    return JSONResponse(
                        content=create_paginated_response(
                            data=result['items'],
                            pagination={
                                'page': result.get('page', page),
                                'limit': result.get('limit', limit),
                                'total': result.get('total', len(result['items'])),
                                'pages': result.get('pages', 1)
                            },
                            message="Success"
                        ).dict()
                    )
                
                # Wrap single result in paginated format
                return JSONResponse(
                    content=create_paginated_response(
                        data=result if isinstance(result, list) else [result],
                        pagination={
                            'page': page,
                            'limit': limit,
                            'total': len(result) if isinstance(result, list) else 1,
                            'pages': 1
                        },
                        message="Success"
                    ).dict()
                )
                
            except Exception as e:
                logger.logger.error(f"Error in paginated response {func.__name__}: {str(e)}", exc_info=True)
                
                error_response = create_error_response(
                    error_code=ErrorCode.INTERNAL_ERROR,
                    message="An internal error occurred"
                )
                
                return JSONResponse(
                    status_code=500,
                    content=error_response.dict()
                )
        
        return wrapper
    return decorator


def success_response(message: str = "Success"):
    """Decorator for success responses with custom message"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                return JSONResponse(
                    content=create_success_response(
                        message=message,
                        data=result
                    ).dict()
                )
                
            except Exception as e:
                logger.logger.error(f"Error in success response {func.__name__}: {str(e)}", exc_info=True)
                
                error_response = create_error_response(
                    error_code=ErrorCode.INTERNAL_ERROR,
                    message="An internal error occurred"
                )
                
                return JSONResponse(
                    status_code=500,
                    content=error_response.dict()
                )
        
        return wrapper
    return decorator


def error_response(error_code: ErrorCode, message: str = None, status_code: int = 400):
    """Decorator for error responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # If function returns a result, it means no error occurred
                return JSONResponse(
                    content=create_success_response(
                        message="Success",
                        data=result
                    ).dict()
                )
                
            except Exception as e:
                logger.logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                
                error_response = create_error_response(
                    error_code=error_code,
                    message=message or str(e)
                )
                
                return JSONResponse(
                    status_code=status_code,
                    content=error_response.dict()
                )
        
        return wrapper
    return decorator


def validate_request_data(schema_class):
    """Decorator to validate request data"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Find request data in kwargs
                request_data = None
                for key, value in kwargs.items():
                    if hasattr(value, 'dict'):  # Pydantic model
                        request_data = value
                        break
                
                if request_data:
                    # Validate data
                    try:
                        validated_data = schema_class(**request_data.dict())
                        # Replace original data with validated data
                        for key, value in kwargs.items():
                            if value == request_data:
                                kwargs[key] = validated_data
                                break
                    except Exception as validation_error:
                        logger.log_validation_error(
                            endpoint=func.__name__,
                            errors=[str(validation_error)]
                        )
                        
                        error_response = create_error_response(
                            error_code=ErrorCode.VALIDATION_ERROR,
                            message="Validation failed",
                            details=[{
                                'field': 'data',
                                'message': str(validation_error),
                                'code': 'validation_error'
                            }]
                        )
                        
                        return JSONResponse(
                            status_code=422,
                            content=error_response.dict()
                        )
                
                # Call original function
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.logger.error(f"Error in validation decorator {func.__name__}: {str(e)}", exc_info=True)
                
                error_response = create_error_response(
                    error_code=ErrorCode.INTERNAL_ERROR,
                    message="An internal error occurred"
                )
                
                return JSONResponse(
                    status_code=500,
                    content=error_response.dict()
                )
        
        return wrapper
    return decorator


def log_endpoint_access(func):
    """Decorator to log endpoint access"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from args if present
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        try:
            result = await func(*args, **kwargs)
            
            # Log successful access
            if request:
                logger.log_endpoint_access(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=200
                )
            
            return result
            
        except HTTPException as e:
            # Log failed access
            if request:
                logger.log_endpoint_access(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=e.status_code
                )
            
            raise e
            
        except Exception as e:
            # Log error
            if request:
                logger.log_endpoint_access(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=500
                )
            
            raise e
    
    return wrapper


# Export main components
__all__ = [
    'standardize_response',
    'paginated_response',
    'success_response',
    'error_response',
    'validate_request_data',
    'log_endpoint_access'
]
