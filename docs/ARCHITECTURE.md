# MapleHustleCAN Architecture Guide

This document outlines the architecture, design patterns, and responsibilities of each component in the MapleHustleCAN platform.

## 🏗️ **Project Structure**

```
app/
├── core/           # Core application infrastructure
├── db/             # Database configuration and session management
├── models/         # SQLAlchemy database models
├── schemas/        # Pydantic validation schemas
├── routers/        # FastAPI route handlers
├── repositories/   # Data access layer
├── services/       # Business logic layer
├── tasks/          # Background task definitions
└── utils/          # Utility functions and helpers
```

## 📋 **Layer Responsibilities**

### **Core Layer (`app/core/`)**
**Purpose**: Application infrastructure and cross-cutting concerns

**Responsibilities**:
- Configuration management (`config.py`)
- Security middleware and policies (`security.py`, `middleware.py`)
- Logging and monitoring (`logging.py`, `performance_monitoring.py`)
- Caching infrastructure (`cache.py`)
- Background task orchestration (`celery_app.py`)
- Error tracking and alerting (`error_tracking.py`)

**Key Files**:
- `config.py`: Environment configuration and settings
- `security.py`: Security policies, CORS, CSRF, rate limiting
- `middleware.py`: Request/response middleware
- `cache.py`: Redis caching layer
- `celery_app.py`: Background task configuration

### **Database Layer (`app/db/`)**
**Purpose**: Database connection and session management

**Responsibilities**:
- Database engine configuration
- Connection pooling
- Session factory
- Transaction management
- Database health monitoring

**Key Files**:
- `base.py`: SQLAlchemy base class and model imports
- `session.py`: Database session management and pooling

### **Models Layer (`app/models/`)**
**Purpose**: Database schema definition and ORM mapping

**Responsibilities**:
- Define database tables and relationships
- Enforce data constraints and validation
- Handle database-specific features (PostGIS, enums)
- Define indexes and foreign keys

**Key Files**:
- `users.py`: User and authentication models
- `services.py`: Service and availability models
- `bookings.py`: Booking and appointment models
- `orders.py`: Order and payment models
- `messages.py`: Messaging system models
- `notifications.py`: Notification models
- `system.py`: System and audit models

### **Schemas Layer (`app/schemas/`)**
**Purpose**: Data validation and serialization

**Responsibilities**:
- Validate incoming request data
- Serialize response data
- Define API contracts
- Handle data transformation
- Exclude sensitive fields from responses

**Key Files**:
- `users.py`: User-related schemas
- `services.py`: Service-related schemas
- `bookings.py`: Booking-related schemas
- `orders.py`: Order-related schemas
- `validation.py`: Business rule validation schemas

### **Routers Layer (`app/routers/`)**
**Purpose**: API endpoint definition and HTTP handling

**Responsibilities**:
- Define REST API endpoints
- Handle HTTP requests and responses
- Route requests to appropriate services
- Apply authentication and authorization
- Handle file uploads and downloads

**Key Files**:
- `users.py`: User authentication and management
- `services.py`: Service management
- `bookings.py`: Booking management
- `orders.py`: Order management
- `payments.py`: Payment processing
- `messages.py`: Messaging system
- `notifications.py`: Notification system
- `health.py`: Health check endpoints
- `security.py`: Security monitoring

### **Repositories Layer (`app/repositories/`)**
**Purpose**: Data access and persistence operations

**Responsibilities**:
- Abstract database operations
- Handle complex queries
- Manage data relationships
- Provide data access interfaces
- Handle database-specific logic

**Key Files**:
- `users.py`: User data access
- `services.py`: Service data access
- `bookings.py`: Booking data access
- `orders.py`: Order data access

### **Services Layer (`app/services/`)**
**Purpose**: Business logic and domain operations

**Responsibilities**:
- Implement business rules
- Orchestrate complex operations
- Handle cross-cutting concerns
- Manage transactions
- Coordinate between repositories

**Key Files**:
- `users.py`: User business logic
- `services.py`: Service business logic
- `bookings.py`: Booking business logic
- `orders.py`: Order business logic

### **Tasks Layer (`app/tasks/`)**
**Purpose**: Background task definitions and processing

**Responsibilities**:
- Define asynchronous tasks
- Handle long-running operations
- Process background jobs
- Manage task queues
- Handle task retries and failures

**Key Files**:
- `email_tasks.py`: Email sending tasks
- `cleanup_tasks.py`: Maintenance tasks
- `notification_tasks.py`: Notification tasks

### **Utils Layer (`app/utils/`)**
**Purpose**: Utility functions and helpers

**Responsibilities**:
- Provide common utilities
- Handle external integrations
- Manage file operations
- Provide validation helpers
- Handle authentication utilities

**Key Files**:
- `auth.py`: Authentication utilities
- `email.py`: Email utilities
- `sms.py`: SMS utilities
- `storage.py`: File storage utilities
- `validation.py`: Validation utilities

## 🔄 **Data Flow**

### **Request Flow**
1. **Router** receives HTTP request
2. **Middleware** processes request (auth, logging, rate limiting)
3. **Router** validates request data using **Schemas**
4. **Router** calls appropriate **Service**
5. **Service** orchestrates business logic
6. **Service** calls **Repository** for data operations
7. **Repository** executes database queries via **Models**
8. **Service** returns processed data
9. **Router** serializes response using **Schemas**
10. **Middleware** processes response (logging, headers)

### **Background Task Flow**
1. **Service** queues task via **Celery**
2. **Task** processes asynchronously
3. **Task** may call **Repository** for data operations
4. **Task** updates status and results
5. **Task** may trigger notifications or other tasks

## 🛡️ **Security Architecture**

### **Authentication & Authorization**
- JWT-based authentication with refresh tokens
- Role-based access control (client, provider, admin)
- Row-Level Security (RLS) for data isolation
- API key authentication for admin endpoints

### **Security Middleware**
- CORS protection
- CSRF protection
- Rate limiting
- Request size limits
- SQL injection protection
- Security headers (HSTS, CSP, X-Frame-Options)

### **Data Protection**
- Password hashing with bcrypt
- Sensitive field exclusion from responses
- Input validation and sanitization
- Secure file upload handling

## 🚀 **Performance Architecture**

### **Caching Strategy**
- Redis for session storage
- Query result caching
- API response caching
- Background task result caching

### **Database Optimization**
- Connection pooling
- Query optimization
- Index optimization
- Read replica support

### **Background Processing**
- Celery for async tasks
- Task queues for different priorities
- Retry mechanisms
- Dead letter queues

## 📊 **Monitoring & Observability**

### **Logging**
- Structured JSON logging
- Correlation IDs for request tracking
- Performance metrics
- Error tracking with Sentry

### **Health Monitoring**
- Database health checks
- Redis health checks
- Application health endpoints
- External service health checks

### **Metrics**
- Request/response metrics
- Database performance metrics
- Cache hit/miss ratios
- Background task metrics

## 🔧 **Development Guidelines**

### **Adding New Features**
1. Define **Model** for database schema
2. Create **Schema** for validation
3. Implement **Repository** for data access
4. Create **Service** for business logic
5. Add **Router** for API endpoints
6. Write **Tests** for all layers
7. Update **Documentation**

### **Code Standards**
- Use type hints consistently
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Implement proper error handling
- Use dependency injection
- Write unit and integration tests

### **Database Changes**
1. Create **Alembic migration**
2. Test migration up and down
3. Update **Models** if needed
4. Update **Schemas** if needed
5. Run migration in CI/CD
6. Document breaking changes

## 🚨 **Common Anti-Patterns to Avoid**

### **Repository Layer**
- ❌ Don't put business logic in repositories
- ❌ Don't expose raw database queries
- ❌ Don't handle transactions in repositories

### **Service Layer**
- ❌ Don't access database directly
- ❌ Don't handle HTTP concerns
- ❌ Don't put data access logic in services

### **Router Layer**
- ❌ Don't put business logic in routers
- ❌ Don't handle database operations directly
- ❌ Don't skip input validation

### **Model Layer**
- ❌ Don't put business logic in models
- ❌ Don't expose sensitive fields
- ❌ Don't skip proper indexing

## 📚 **Further Reading**

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
