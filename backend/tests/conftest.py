"""
Shared pytest fixtures for MoveWise backend tests.

Uses an in-memory SQLite database so tests are fully isolated from any
real database and require no external services.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
# Import models so they register with Base before create_all is called
import app.models.user      # noqa: F401
import app.models.profile   # noqa: F401
import app.models.analysis  # noqa: F401
from app.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite test database
# StaticPool forces all sessions to share one connection, which is required
# for sqlite:///:memory: — otherwise each new connection gets an empty DB.
# ---------------------------------------------------------------------------
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_db():
    """Create all tables before each test, drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(reset_db):
    """FastAPI TestClient with the test DB injected."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helper fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registered_user(client):
    """Register a test user and return credentials + Bearer token."""
    resp = client.post("/auth/register", json={
        "email": "user@example.com",
        "name": "Test User",
        "password": "password123",
    })
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {
        "email": "user@example.com",
        "name": "Test User",
        "password": "password123",
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def auth_headers(registered_user):
    """Convenience: just the Authorization header dict."""
    return registered_user["headers"]


@pytest.fixture
def second_user(client):
    """A second registered user — used to test ownership checks."""
    resp = client.post("/auth/register", json={
        "email": "other@example.com",
        "name": "Other User",
        "password": "otherpass123",
    })
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {
        "email": "other@example.com",
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }
