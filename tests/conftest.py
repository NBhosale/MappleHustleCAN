# fimport pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal, Base, engine

# ✅ Recreate database for tests
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# ✅ Client fixture
@pytest.fixture
def client():
    return TestClient(app)
ixtures (DB session, client, test user, tokens)
