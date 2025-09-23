import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import get_db, Base
from app.core.config import settings
import tempfile
import os

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    from app.models.users import User
    provider = User(
        email="provider@example.com",
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
    from app.models.users import User
    admin = User(
        email="admin@example.com",
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
    response = client.post("/users/login", json={
        "email": test_user.email,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def provider_headers(client, test_provider):
    response = client.post("/users/login", json={
        "email": test_provider.email,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client, test_admin):
    response = client.post("/users/login", json={
        "email": test_admin.email,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
