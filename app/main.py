from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from jose import JWTError, ExpiredSignatureError

from app.core.exceptions import jwt_exception_handler, validation_exception_handler
from app.core.middleware import AuthLoggingMiddleware
from app.routers import (
    users,
    services,
    bookings,
    items,
    orders,
    payments,
    messages,
    notifications,
)

# ✅ Initialize FastAPI with branding
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
    ],
)

# ✅ Register middleware
app.add_middleware(AuthLoggingMiddleware)

# ✅ Register exception handlers
app.add_exception_handler(JWTError, jwt_exception_handler)
app.add_exception_handler(ExpiredSignatureError, jwt_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ✅ Include routers
app.include_router(users.router)
app.include_router(services.router)
app.include_router(bookings.router)
app.include_router(items.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(messages.router)
app.include_router(notifications.router)

# ✅ Root endpoint
@app.get("/")
def root():
    return {"message": "Maple Hussle API is running 🚀"}
