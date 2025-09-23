from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from jose import JWTError, ExpiredSignatureError

from app.core.exceptions import jwt_exception_handler, validation_exception_handler
from app.core.middleware import AuthLoggingMiddleware
from app.routers import users


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


# ✅ Root endpoint
@app.get("/")
def root():
    return {"message": "Maple Hussle API is running 🚀"}