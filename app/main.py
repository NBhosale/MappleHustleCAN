from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from jose import JWTError, ExpiredSignatureError
from app.core.logging import setup_logging
from app.core.lifecycle import lifespan
from app.core.logging_context import LoggingContext, get_logger
from app.core.error_tracking import error_tracker, track_errors, track_async_errors
from app.core.performance_monitoring import performance_monitor, monitor_performance, start_performance_monitoring
import time
setup_logging()

from app.core.exceptions import jwt_exception_handler, validation_exception_handler
from app.core.middleware import AuthLoggingMiddleware
from app.core.validation_middleware import BusinessRuleValidationMiddleware
from app.core.security import configure_security, get_security_config
from app.core.security_monitoring import initialize_security_monitoring, get_security_config
from app.routers import (
    users,
    services,
    bookings,
    items,
    orders,
    payments,
    messages,
    notifications,
    provinces,
    files,
    search,
    security,
    health,
    auth,
)

from app.core.middleware import (
    limiter, 
    rate_limit_exceeded_handler, 
    SecurityHeadersMiddleware,
    CSRFProtectionMiddleware,
    RequestSizeLimitMiddleware
)
from app.core.responses import (
    handle_api_exception,
    handle_http_exception,
    handle_validation_exception,
    handle_generic_exception
)
from slowapi.errors import RateLimitExceeded


# ✅ Initialize FastAPI with branding and lifecycle management
app = FastAPI(
    title="Maple Hussle API",
    description="""
Welcome to the **Maple Hussle API** 🌿🚀  

This backend powers the Maple Hussle platform for:  
- 🔑 Authentication (register, login, JWT refresh, logout)  
- 👤 User profiles and dashboards  
- 🛠️ Admin tools (manage users, revoke tokens)  
- 🔐 Password management (reset, change, forgot-password)  
- 🛠️ Services and bookings  
- 🛍️ Marketplace items and orders  
- 💳 Payments and refunds  
- 💬 Messaging and notifications  
- 🏥 Health checks and monitoring
- 🔒 Security features and monitoring

All endpoints are secured with JWT authentication.  
Use the `/users/login` endpoint to obtain your tokens.
""",
    version="1.0.0",
    contact={
        "name": "Maple Hussle Dev Team",
        "url": "https://maplehussle.com",
        "email": "support@maplehussle.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://maplehussle.com/legal",
    },
    openapi_tags=[
        {"name": "Authentication", "description": "User registration, login, refresh, logout"},
        {"name": "Password Management", "description": "Change, forgot, and reset passwords"},
        {"name": "Profile", "description": "User dashboards and profile info"},
        {"name": "Admin", "description": "Admin-only tools for user and token management"},
        {"name": "Services", "description": "Providers create and manage services"},
        {"name": "Bookings", "description": "Clients book services"},
        {"name": "Items", "description": "Marketplace items (handmade, home products, etc.)"},
        {"name": "Orders", "description": "Client orders and shipments"},
        {"name": "Payments", "description": "Payment processing and refunds"},
        {"name": "Messages", "description": "Client ↔ Provider messaging"},
        {"name": "Notifications", "description": "System notifications"},
        {"name": "Health", "description": "Health checks and system monitoring"},
        {"name": "Security", "description": "Security monitoring and admin dashboard"},
    ],
    lifespan=lifespan,  # Add lifecycle management
)

# ✅ Configure security
security_config = get_security_config()
configure_security(app, security_config)

# ✅ Initialize security monitoring
monitoring_config = {
    "enabled": True,
    "anomaly_detection": True,
    "alerting": True,
    "email_alerts": False,  # Set to True in production
    "webhook_alerts": False,  # Set to True in production
    "thresholds": {
        "brute_force_attempts": 10,
        "ddos_requests": 100,
        "sql_injection_attempts": 5
    },
    "alert_cooldown": 300  # 5 minutes
}
initialize_security_monitoring(monitoring_config)

# ✅ Start performance monitoring
start_performance_monitoring()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)


# ✅ Register middleware
app.add_middleware(AuthLoggingMiddleware)
app.add_middleware(BusinessRuleValidationMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFProtectionMiddleware, secret_key=settings.JWT_SECRET_KEY)
app.add_middleware(RequestSizeLimitMiddleware, max_size=settings.MAX_REQUEST_SIZE)

# ✅ Add request logging and performance monitoring middleware
@app.middleware("http")
async def logging_and_performance_middleware(request: Request, call_next):
    """Middleware for request logging and performance monitoring"""
    start_time = time.time()
    
    # Extract user info from request if available
    user_id = None
    if hasattr(request.state, 'user') and request.state.user:
        user_id = str(request.state.user.id)
    
    # Create logging context
    with LoggingContext(user_id=user_id) as context:
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record performance metrics
            performance_monitor.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            # Log API request
            from app.core.logging_context import log_api_request
            log_api_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
                user_id=user_id
            )
            
            return response
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            error_tracker.capture_exception(e, {
                "method": request.method,
                "path": request.url.path,
                "duration": duration,
                "user_id": user_id
            })
            raise


# ✅ Register exception handlers
app.add_exception_handler(JWTError, jwt_exception_handler)
app.add_exception_handler(ExpiredSignatureError, jwt_exception_handler)
app.add_exception_handler(RequestValidationError, handle_validation_exception)
app.add_exception_handler(HTTPException, handle_http_exception)
app.add_exception_handler(Exception, handle_generic_exception)

# ✅ Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(provinces.router)
app.include_router(services.router)
app.include_router(bookings.router)
app.include_router(items.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(messages.router)
app.include_router(notifications.router)
app.include_router(files.router)
app.include_router(search.router)
app.include_router(security.router)
app.include_router(health.router)

# ✅ Root endpoint
@app.get("/")
def root():
    return {"message": "Maple Hussle API is running 🚀"}
