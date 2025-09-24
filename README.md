# 🍁 MapleHustle

MapleHustle is a comprehensive Canadian services & marketplace platform that connects clients with service providers for various services like house sitting, dog walking, and more. The platform also supports buying and selling handmade products with a focus on Canadian artisans and service providers.

## ✨ Features

### 🛠️ Services Marketplace
- **Service Categories**: Dog walking, house sitting, pet care, home maintenance, and more
- **Provider Profiles**: Detailed provider profiles with ratings and reviews
- **Availability Management**: Real-time availability scheduling
- **Booking System**: Seamless booking and payment processing
- **Location-Based Search**: Find services in your area

### 🛍️ Product Marketplace
- **Handmade Products**: Support for Canadian artisans and crafters
- **Category Management**: Organized product categories
- **Inventory Tracking**: Real-time stock management
- **Order Processing**: Complete order lifecycle management
- **Shipping Integration**: Automated shipping calculations

### 💬 Communication
- **Messaging System**: Direct communication between users
- **File Attachments**: Share images and documents
- **Notification System**: Real-time updates and alerts
- **Email & SMS**: Multi-channel notifications

### 🔒 Security & Trust
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: Client, Provider, and Admin roles
- **Rate Limiting**: Protection against abuse
- **Data Validation**: Comprehensive input validation
- **Audit Logging**: Complete activity tracking

## 🚀 Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: Python SQL toolkit and ORM
- **PostgreSQL**: Robust relational database with PostGIS support
- **Alembic**: Database migration tool
- **Redis**: Caching and session storage
- **Celery**: Background task processing

### Frontend (Planned)
- **Nuxt.js**: Vue.js framework for production
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Beautiful component library

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and load balancer
- **PostgreSQL**: Primary database
- **Redis**: Caching layer

### Integrations
- **Stripe**: Payment processing
- **Twilio**: SMS notifications
- **SendGrid**: Email delivery
- **AWS S3**: File storage (planned)

## 📂 Project Structure

```
MapleHustle/
├── app/                          # FastAPI backend application
│   ├── core/                     # Core application infrastructure
│   │   ├── config.py            # Configuration management
│   │   ├── security.py          # Security policies and middleware
│   │   ├── middleware.py        # Custom middleware
│   │   ├── cache.py             # Caching layer
│   │   └── error_tracking.py    # Error monitoring
│   ├── models/                   # SQLAlchemy database models
│   │   ├── users.py             # User and authentication models
│   │   ├── services.py          # Service and availability models
│   │   ├── bookings.py          # Booking models
│   │   ├── orders.py            # Order and payment models
│   │   └── messages.py          # Messaging system models
│   ├── schemas/                  # Pydantic validation schemas
│   │   ├── users.py             # User-related schemas
│   │   ├── services.py          # Service-related schemas
│   │   └── bookings.py          # Booking-related schemas
│   ├── routers/                  # FastAPI route handlers
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── users.py             # User management
│   │   ├── services.py          # Service management
│   │   ├── bookings.py          # Booking management
│   │   └── health.py            # Health check endpoints
│   ├── repositories/             # Data access layer
│   │   ├── users.py             # User data access
│   │   ├── services.py          # Service data access
│   │   └── bookings.py          # Booking data access
│   ├── services/                 # Business logic layer
│   │   ├── users.py             # User business logic
│   │   ├── services.py          # Service business logic
│   │   └── bookings.py          # Booking business logic
│   ├── tasks/                    # Background tasks
│   │   ├── email_tasks.py       # Email sending tasks
│   │   └── cleanup_tasks.py     # Maintenance tasks
│   ├── utils/                    # Utility functions
│   │   ├── auth.py              # Authentication utilities
│   │   ├── email.py             # Email utilities
│   │   └── storage.py           # File storage utilities
│   └── db/                       # Database configuration
│       ├── base.py              # SQLAlchemy base class
│       └── session.py           # Database session management
├── alembic/                      # Database migrations
├── tests/                        # Test suite
│   ├── test_auth_router.py      # Authentication tests
│   ├── test_services.py         # Service tests
│   ├── test_bookings.py         # Booking tests
│   └── test_security.py         # Security tests
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md          # Architecture guide
│   ├── SECURITY.md              # Security documentation
│   └── API_DOCUMENTATION.md     # Complete API reference
├── scripts/                      # Utility scripts
├── docker-compose.yml           # Development environment
├── docker-compose.prod.yml      # Production environment
├── Dockerfile                   # Backend container
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/maplehustle.git
cd maplehustle
```

### 2. Set Up Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**
```env
# Database
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/maplehustle

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-here
ENVIRONMENT=development

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 4. Set Up Database
```bash
# Start PostgreSQL and Redis (using Docker)
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head

# Seed initial data (optional)
python scripts/seed_database.py
```

### 5. Start the Application
```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Docker Compose
docker-compose up
```

### 6. Access the Application
- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🧪 Testing

### Run All Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run specific test categories
python run_tests.py unit      # Unit tests
python run_tests.py integration  # Integration tests
python run_tests.py security  # Security tests
python run_tests.py load      # Load tests
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Security Tests**: Authentication, authorization, and security features
- **Load Tests**: Performance and scalability testing

## 📚 Documentation

### API Documentation
- **[Complete API Reference](API_DOCUMENTATION.md)**: Comprehensive API documentation
- **[Architecture Guide](docs/ARCHITECTURE.md)**: System architecture and design patterns
- **[Security Documentation](docs/SECURITY.md)**: Security features and best practices

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐳 Docker Deployment

### Development
```bash
# Start all services
docker-compose up

# Start specific services
docker-compose up postgres redis

# View logs
docker-compose logs -f app
```

### Production
```bash
# Build production image
docker build -f Dockerfile.prod -t maplehustle:latest .

# Run production container
docker run -p 8000:8000 --env-file .env.prod maplehustle:latest
```

## 🔧 Development

### Code Quality
```bash
# Linting
python -m flake8 app/ tests/
python -m mypy app/

# Security scanning
python -m bandit -r app/
python -m safety check

# Auto-formatting
python -m autopep8 --in-place --recursive app/ tests/
python -m isort app/ tests/
```

### Database Management
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check migration status
alembic current
```

### Adding New Features
1. **Create Model**: Define database schema in `app/models/`
2. **Create Schema**: Add validation schemas in `app/schemas/`
3. **Create Repository**: Implement data access in `app/repositories/`
4. **Create Service**: Add business logic in `app/services/`
5. **Create Router**: Define API endpoints in `app/routers/`
6. **Write Tests**: Add comprehensive tests
7. **Update Documentation**: Update API docs and README

## 🚀 Deployment

### Environment Setup
1. **Production Database**: Set up PostgreSQL with PostGIS
2. **Redis Instance**: Configure Redis for caching
3. **Environment Variables**: Set production configuration
4. **SSL Certificate**: Configure HTTPS
5. **Domain Setup**: Point domain to server

### Monitoring
- **Health Checks**: Built-in health monitoring endpoints
- **Logging**: Structured JSON logging
- **Error Tracking**: Sentry integration (optional)
- **Performance**: Request/response metrics

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints consistently
- Write comprehensive docstrings
- Maintain test coverage above 80%
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check the [API Documentation](API_DOCUMENTATION.md)
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions

### Common Issues
- **Database Connection**: Ensure PostgreSQL is running and accessible
- **Redis Connection**: Verify Redis is running on the correct port
- **Environment Variables**: Check all required variables are set
- **Dependencies**: Ensure all Python packages are installed

---

**Built with ❤️ in Canada** 🇨🇦