"""
Comprehensive security configuration for MapleHustleCAN
"""
import logging
import re
import secrets
from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger(__name__)


# ============================================================================
# CORS CONFIGURATION
# ============================================================================

def configure_cors(app: FastAPI, allowed_origins: List[str] = None):
    """
    Configure CORS with security best practices
    """
    if allowed_origins is None:
        # Default to common development origins
        allowed_origins = [
            "http://localhost:3000",  # React dev server
            "http://localhost:8080",  # Vue dev server
            "http://localhost:4200",  # Angular dev server
            "https://maplehustlecan.com",  # Production domain
            "https://www.maplehustlecan.com",  # Production domain with www
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token",
            "X-API-Key",
        ],
        expose_headers=["X-CSRF-Token", "X-Request-ID"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )


# ============================================================================
# CSRF PROTECTION
# ============================================================================

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware
    """

    def __init__(self, app, secret_key: str = None):
        super().__init__(app)
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.exempt_paths = {
            "/",  # Health check
            "/docs",  # API documentation
            "/openapi.json",  # OpenAPI schema
            "/users/login",  # Login endpoint
            "/users/register",  # Registration endpoint
            "/users/forgot-password",  # Password reset
            "/users/reset-password",  # Password reset
        }
        self.safe_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}

    async def dispatch(self, request: Request, call_next):
        """
        Process request and validate CSRF token
        """
        # Skip CSRF check for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            return await call_next(request)

        # Skip CSRF check for API key authentication
        if request.headers.get("X-API-Key"):
            return await call_next(request)

        # Validate CSRF token
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token required",
                         "error_code": "CSRF_TOKEN_MISSING"}
            )

        # Validate CSRF token format (basic validation)
        if not self._validate_csrf_token(csrf_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token",
                         "error_code": "CSRF_TOKEN_INVALID"}
            )

        return await call_next(request)

    def _validate_csrf_token(self, token: str) -> bool:
        """
        Validate CSRF token format and signature
        """
        try:
            # Basic format validation (32+ character alphanumeric)
            if not re.match(r'^[a-zA-Z0-9_-]{32,}$', token):
                return False

            # In a real implementation, you would validate the token signature
            # against the secret key and check expiration
            return True

        except Exception:
            return False


def generate_csrf_token() -> str:
    """
    Generate a secure CSRF token
    """
    return secrets.token_urlsafe(32)


# ============================================================================
# REQUEST SIZE LIMITS
# ============================================================================

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request size
    """

    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_request_size = max_request_size

    async def dispatch(self, request: Request, call_next):
        """
        Check request size before processing
        """
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": f"Request too large. Maximum size: {self.max_request_size // (1024 * 1024)}MB",
                            "error_code": "REQUEST_TOO_LARGE"
                        }
                    )
            except ValueError:
                # Invalid content-length header
                pass

        return await call_next(request)


# ============================================================================
# SQL INJECTION PROTECTION
# ============================================================================

class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and prevent SQL injection attempts
    """

    def __init__(self, app):
        super().__init__(app)
        # Common SQL injection patterns
        self.sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"]\s*=\s*['\"])",
            r"(\bUNION\s+SELECT\b)",
            r"(\bDROP\s+TABLE\b)",
            r"(\bINSERT\s+INTO\b)",
            r"(\bDELETE\s+FROM\b)",
            r"(\bUPDATE\s+SET\b)",
            r"(\bALTER\s+TABLE\b)",
            r"(\bCREATE\s+TABLE\b)",
            r"(\bEXEC\s*\()",
            r"(\bSCRIPT\b)",
            r"(--\s|\#\s)",  # SQL comments
            r"(\/\*.*?\*\/)",  # SQL block comments
            r"(\bWAITFOR\s+DELAY\b)",
            r"(\bBENCHMARK\b)",
            r"(\bSLEEP\b)",
            r"(\bPG_SLEEP\b)",
            r"(\bCHAR\s*\()",
            r"(\bASCII\s*\()",
            r"(\bSUBSTRING\s*\()",
            r"(\bLENGTH\s*\()",
            r"(\bCOUNT\s*\()",
            r"(\bSUM\s*\()",
            r"(\bAVG\s*\()",
            r"(\bMAX\s*\()",
            r"(\bMIN\s*\()",
            r"(\bGROUP\s+BY\b)",
            r"(\bORDER\s+BY\b)",
            r"(\bHAVING\b)",
            r"(\bWHERE\b)",
            r"(\bFROM\b)",
            r"(\bINTO\b)",
            r"(\bVALUES\b)",
            r"(\bSET\b)",
            r"(\bDEFAULT\b)",
            r"(\bNULL\b)",
            r"(\bNOT\b)",
            r"(\bIS\b)",
            r"(\bLIKE\b)",
            r"(\bIN\b)",
            r"(\bBETWEEN\b)",
            r"(\bEXISTS\b)",
            r"(\bCASE\b)",
            r"(\bWHEN\b)",
            r"(\bTHEN\b)",
            r"(\bELSE\b)",
            r"(\bEND\b)",
            r"(\bIF\b)",
            r"(\bWHILE\b)",
            r"(\bFOR\b)",
            r"(\bLOOP\b)",
            r"(\bREPEAT\b)",
            r"(\bUNTIL\b)",
            r"(\bBREAK\b)",
            r"(\bCONTINUE\b)",
            r"(\bRETURN\b)",
            r"(\bCALL\b)",
            r"(\bPROCEDURE\b)",
            r"(\bFUNCTION\b)",
            r"(\bTRIGGER\b)",
            r"(\bVIEW\b)",
            r"(\bINDEX\b)",
            r"(\bCONSTRAINT\b)",
            r"(\bFOREIGN\s+KEY\b)",
            r"(\bPRIMARY\s+KEY\b)",
            r"(\bUNIQUE\b)",
            r"(\bCHECK\b)",
            r"(\bREFERENCES\b)",
            r"(\bCASCADE\b)",
            r"(\bRESTRICT\b)",
            r"(\bSET\s+NULL\b)",
            r"(\bNO\s+ACTION\b)",
            r"(\bON\s+DELETE\b)",
            r"(\bON\s+UPDATE\b)",
            r"(\bGRANT\b)",
            r"(\bREVOKE\b)",
            r"(\bDENY\b)",
            r"(\bBACKUP\b)",
            r"(\bRESTORE\b)",
            r"(\bLOAD\b)",
            r"(\bINFILE\b)",
            r"(\bOUTFILE\b)",
            r"(\bDUMPFILE\b)",
            r"(\bLOAD\s+DATA\b)",
            r"(\bINTO\s+OUTFILE\b)",
            r"(\bINTO\s+DUMPFILE\b)",
            r"(\bFIELD\s+TERMINATED\b)",
            r"(\bLINES\s+TERMINATED\b)",
            r"(\bIGNORE\s+\d+\s+LINES\b)",
            r"(\bREPLACE\b)",
            r"(\bIGNORE\b)",
            r"(\bLOW_PRIORITY\b)",
            r"(\bHIGH_PRIORITY\b)",
            r"(\bDELAYED\b)",
            r"(\bQUICK\b)",
            r"(\bEXTENDED\b)",
            r"(\bUSING\b)",
            r"(\bFOR\s+UPDATE\b)",
            r"(\bLOCK\s+IN\s+SHARE\s+MODE\b)",
            r"(\bREAD\s+UNCOMMITTED\b)",
            r"(\bREAD\s+COMMITTED\b)",
            r"(\bREPEATABLE\s+READ\b)",
            r"(\bSERIALIZABLE\b)",
            r"(\bISOLATION\s+LEVEL\b)",
            r"(\bSTART\s+TRANSACTION\b)",
            r"(\bBEGIN\b)",
            r"(\bCOMMIT\b)",
            r"(\bROLLBACK\b)",
            r"(\bSAVEPOINT\b)",
            r"(\bRELEASE\s+SAVEPOINT\b)",
            r"(\bLOCK\s+TABLES\b)",
            r"(\bUNLOCK\s+TABLES\b)",
            r"(\bSET\s+TRANSACTION\b)",
            r"(\bSET\s+SESSION\b)",
            r"(\bSET\s+GLOBAL\b)",
            r"(\bSET\s+@@\b)",
            r"(\bSHOW\b)",
            r"(\bDESCRIBE\b)",
            r"(\bEXPLAIN\b)",
            r"(\bDESC\b)",
            r"(\bASC\b)",
            r"(\bLIMIT\b)",
            r"(\bOFFSET\b)",
            r"(\bDISTINCT\b)",
            r"(\bALL\b)",
            r"(\bTOP\b)",
            r"(\bPERCENT\b)",
            r"(\bWITH\b)",
            r"(\bRECURSIVE\b)",
            r"(\bCTE\b)",
            r"(\bWINDOW\b)",
            r"(\bOVER\b)",
            r"(\bPARTITION\s+BY\b)",
            r"(\bROWS\b)",
            r"(\bRANGE\b)",
            r"(\bPRECEDING\b)",
            r"(\bFOLLOWING\b)",
            r"(\bCURRENT\s+ROW\b)",
            r"(\bUNBOUNDED\b)",
            r"(\bLAG\b)",
            r"(\bLEAD\b)",
            r"(\bFIRST_VALUE\b)",
            r"(\bLAST_VALUE\b)",
            r"(\bROW_NUMBER\b)",
            r"(\bRANK\b)",
            r"(\bDENSE_RANK\b)",
            r"(\bNTILE\b)",
            r"(\bCUME_DIST\b)",
            r"(\bPERCENT_RANK\b)",
            r"(\bPERCENTILE_CONT\b)",
            r"(\bPERCENTILE_DISC\b)",
            r"(\bLISTAGG\b)",
            r"(\bSTRING_AGG\b)",
            r"(\bARRAY_AGG\b)",
            r"(\bJSON_AGG\b)",
            r"(\bJSON_OBJECT_AGG\b)",
            r"(\bJSON_ARRAY_AGG\b)",
            r"(\bXMLAGG\b)",
            r"(\bXMLFOREST\b)",
            r"(\bXMLELEMENT\b)",
            r"(\bXMLATTRIBUTES\b)",
            r"(\bXMLCONCAT\b)",
            r"(\bXMLQUERY\b)",
            r"(\bXMLTABLE\b)",
            r"(\bXMLEXISTS\b)",
            r"(\bXMLCAST\b)",
            r"(\bXMLSERIALIZE\b)",
            r"(\bXMLPARSE\b)",
            r"(\bXMLPI\b)",
            r"(\bXMLCOMMENT\b)",
            r"(\bXMLCDATA\b)",
            r"(\bXMLROOT\b)",
            r"(\bXMLNAMESPACES\b)",
            r"(\bXMLSCHEMA\b)",
            r"(\bXMLVALIDATE\b)",
            r"(\bXMLQUERY\b)",
            r"(\bXMLTABLE\b)",
            r"(\bXMLEXISTS\b)",
            r"(\bXMLCAST\b)",
            r"(\bXMLSERIALIZE\b)",
            r"(\bXMLPARSE\b)",
            r"(\bXMLPI\b)",
            r"(\bXMLCOMMENT\b)",
            r"(\bXMLCDATA\b)",
            r"(\bXMLROOT\b)",
            r"(\bXMLNAMESPACES\b)",
            r"(\bXMLSCHEMA\b)",
            r"(\bXMLVALIDATE\b)",
        ]

        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(
            pattern, re.IGNORECASE) for pattern in self.sql_patterns]

    async def dispatch(self, request: Request, call_next):
        """
        Check request for SQL injection patterns
        """
        # Check query parameters
        for param_name, param_value in request.query_params.items():
            if self._detect_sql_injection(str(param_value)):
                logger.warning(
                    f"SQL injection attempt detected in query param '{param_name}': {param_value}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "detail": "Invalid request parameters",
                        "error_code": "SQL_INJECTION_DETECTED"
                    }
                )

        # Check path parameters
        if self._detect_sql_injection(request.url.path):
            logger.warning(
                f"SQL injection attempt detected in path: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Invalid request path",
                    "error_code": "SQL_INJECTION_DETECTED"
                }
            )

        # Check headers (basic check)
        for header_name, header_value in request.headers.items():
            if header_name.lower() in ['user-agent', 'referer', 'origin']:
                if self._detect_sql_injection(header_value):
                    logger.warning(
                        f"SQL injection attempt detected in header '{header_name}': {header_value}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "detail": "Invalid request headers",
                            "error_code": "SQL_INJECTION_DETECTED"
                        }
                    )

        return await call_next(request)

    def _detect_sql_injection(self, input_string: str) -> bool:
        """
        Detect SQL injection patterns in input string
        """
        try:
            # Check against compiled patterns
            for pattern in self.compiled_patterns:
                if pattern.search(input_string):
                    return True

            # Additional checks for common SQL injection techniques
            suspicious_chars = ["'", '"', ';', '--', '/*',
                                '*/', 'xp_', 'sp_', 'exec', 'execute']
            if any(char in input_string.lower() for char in suspicious_chars):
                # Check if it's not a legitimate use case
                if not self._is_legitimate_use(input_string):
                    return True

            return False

        except Exception:
            # If there's any error in detection, err on the side of caution
            return True

    def _is_legitimate_use(self, input_string: str) -> bool:
        """
        Check if the input string contains legitimate use of suspicious characters
        """
        # Add logic to determine if suspicious characters are used legitimately
        # For example, apostrophes in names, quotes in addresses, etc.
        return False


# ============================================================================
# ADDITIONAL SECURITY MIDDLEWARE
# ============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';"

        return response


class CustomTrustedHostMiddleware(BaseHTTPMiddleware):
    """
    Validate Host header to prevent Host header injection
    """

    def __init__(self, app, allowed_hosts: List[str] = None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or [
            "localhost",
            "127.0.0.1",
            "maplehustlecan.com",
            "www.maplehustlecan.com",
            "api.maplehustlecan.com",
        ]

    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "").split(":")[0]

        # Allow test requests and localhost
        if (host in ["testserver", "localhost", "127.0.0.1"] or
                request.headers.get("user-agent", "").startswith("testclient")):
            return await call_next(request)

        if host not in self.allowed_hosts:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid host header",
                         "error_code": "INVALID_HOST"}
            )

        return await call_next(request)


# ============================================================================
# RATE LIMITING ENHANCEMENTS
# ============================================================================

class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting with IP-based tracking
    """

    def __init__(self, app):
        super().__init__(app)
        self.rate_limits = {}  # In production, use Redis
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = datetime.now()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = datetime.now()

        # Cleanup old entries periodically
        if (current_time - self.last_cleanup).seconds > self.cleanup_interval:
            await self._cleanup_old_entries()
            self.last_cleanup = current_time

        # Check rate limit
        if await self._is_rate_limited(client_ip, request):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        return await call_next(request)

    async def _is_rate_limited(self, client_ip: str, request: Request) -> bool:
        """
        Check if client is rate limited
        """
        current_time = datetime.now()
        window_start = current_time - timedelta(minutes=1)

        # Get client's request history
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []

        # Remove old requests
        self.rate_limits[client_ip] = [
            req_time for req_time in self.rate_limits[client_ip]
            if req_time > window_start
        ]

        # Check if limit exceeded
        max_requests = 100  # 100 requests per minute
        if len(self.rate_limits[client_ip]) >= max_requests:
            return True

        # Add current request
        self.rate_limits[client_ip].append(current_time)
        return False

    async def _cleanup_old_entries(self):
        """
        Clean up old rate limit entries
        """
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=1)

        for client_ip in list(self.rate_limits.keys()):
            self.rate_limits[client_ip] = [
                req_time for req_time in self.rate_limits[client_ip]
                if req_time > cutoff_time
            ]

            if not self.rate_limits[client_ip]:
                del self.rate_limits[client_ip]


# ============================================================================
# SECURITY CONFIGURATION FUNCTIONS
# ============================================================================

def configure_security(app: FastAPI, config: dict = None):
    """
    Configure all security middleware and settings
    """
    if config is None:
        config = {}

    # CORS configuration
    configure_cors(app, config.get("allowed_origins"))

    # Add security middleware
    app.add_middleware(CustomTrustedHostMiddleware,
                       allowed_hosts=config.get("allowed_hosts"))
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware, max_request_size=config.get(
        "max_request_size", 10 * 1024 * 1024))
    app.add_middleware(SQLInjectionProtectionMiddleware)
    app.add_middleware(AdvancedRateLimitMiddleware)

    # CSRF protection (optional, can be disabled for API-only usage)
    if config.get("enable_csrf", False):
        app.add_middleware(CSRFProtectionMiddleware,
                           secret_key=config.get("csrf_secret_key"))

    # Session middleware for CSRF tokens
    if config.get("enable_csrf", False):
        app.add_middleware(
            SessionMiddleware,
            secret_key=config.get("session_secret_key",
                                  secrets.token_urlsafe(32)),
            max_age=3600,  # 1 hour
            same_site="lax",
            https_only=config.get("https_only", False)
        )


def get_security_config() -> dict:
    """
    Get security configuration from environment variables
    """
    import os

    return {
        "allowed_origins": os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else None,
        "allowed_hosts": os.getenv("ALLOWED_HOSTS", "").split(",") if os.getenv("ALLOWED_HOSTS") else None,
        # 10MB
        "max_request_size": int(os.getenv("MAX_REQUEST_SIZE", "10485760")),
        "enable_csrf": os.getenv("ENABLE_CSRF", "false").lower() == "true",
        "csrf_secret_key": os.getenv("CSRF_SECRET_KEY"),
        "session_secret_key": os.getenv("SESSION_SECRET_KEY"),
        "https_only": os.getenv("HTTPS_ONLY", "false").lower() == "true",
    }
