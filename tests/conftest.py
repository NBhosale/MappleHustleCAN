import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app

# Rate limiting will be disabled in the setup_test_environment fixture

# Test database configuration - use PostgreSQL for PostGIS support
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/maplehustle"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

# ✅ Disable rate limiting for tests


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment and disable rate limiting"""
    # Set environment to testing
    os.environ["ENVIRONMENT"] = "testing"

    # Disable rate limiting for tests by setting a very high limit
    try:
        from app.core.middleware import limiter
        from app.core.rate_limiting import limiter as rate_limiter

        # Set very high limits for testing (effectively disabling rate
        # limiting)
        limiter._storage = None  # Disable storage
        rate_limiter._storage = None  # Disable storage

        # Override the limit method to always allow
        def no_limit(*args, **kwargs):
            def decorator(f):
                return f
            return decorator

        limiter.limit = no_limit
        rate_limiter.limit = no_limit

        print("✅ Rate limiting disabled for tests")
    except Exception as e:
        print(f"⚠️ Warning: Could not disable rate limiting: {e}")

    yield

    # Re-enable rate limiting after tests
    try:
        from app.core.middleware import limiter
        from app.core.rate_limiting import limiter as rate_limiter

        # Note: We don't re-enable as it would require complex state
        # restoration
    except Exception:
        pass

# ✅ Additional rate limiting disable for each test


@pytest.fixture(autouse=True)
def disable_rate_limiting():
    """Disable rate limiting for each individual test"""
    try:
        from app.core.middleware import limiter
        from app.core.rate_limiting import limiter as rate_limiter

        # Override the limit method to always allow
        def no_limit(*args, **kwargs):
            def decorator(f):
                return f
            return decorator

        limiter.limit = no_limit
        rate_limiter.limit = no_limit
    except Exception:
        pass
    yield
    # No need to re-enable here as it's handled by the session fixture

# ✅ Recreate database for tests


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# ✅ Database session fixture


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# ✅ Override database dependency


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# ✅ Client fixture


@pytest.fixture
def client():
    return TestClient(app)

# ✅ Test user fixture


@pytest.fixture
def test_user(db_session):
    from app.models.users import User
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password",
        role="client",
        status="active"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# ✅ Test provider fixture


@pytest.fixture
def test_provider(db_session):
    import uuid

    from app.models.users import User
    provider = User(
        email=f"provider-{uuid.uuid4().hex[:8]}@example.com",
        name="Test Provider",
        hashed_password="hashed_password",
        role="provider",
        status="active"
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider

# ✅ Test admin fixture


@pytest.fixture
def test_admin(db_session):
    import uuid

    from app.models.users import User
    admin = User(
        email=f"admin-{uuid.uuid4().hex[:8]}@example.com",
        name="Test Admin",
        hashed_password="hashed_password",
        role="admin",
        status="active"
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

# ✅ Authentication fixtures


@pytest.fixture
def client_headers(client, test_user):
    response = client.post("/auth/login", json={
        "email": test_user.email,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def provider_headers(client, test_provider):
    response = client.post("/auth/login", json={
        "email": test_provider.email,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, test_admin):
    response = client.post("/auth/login", json={
        "email": test_admin.email,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
