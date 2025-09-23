from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, ExpiredSignatureError


# Handle JWT errors globally
async def jwt_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, ExpiredSignatureError):
        return JSONResponse(
            status_code=401,
            content={"detail": "Token has expired. Please refresh or log in again."},
        )
    elif isinstance(exc, JWTError):
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid authentication token."},
        )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Handle Pydantic validation errors in a cleaner way
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
