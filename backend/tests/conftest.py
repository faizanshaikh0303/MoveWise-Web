"""
Shared test fixtures.

Environment variables are set before any app module is imported so that
pydantic-settings can find them at class-definition time.
"""
import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-minimum-32chars!")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "test-google-key")

# Patch external service clients before the app modules are imported so that
# service singletons can be constructed without live API keys.
_gmaps_patcher = patch("googlemaps.Client", return_value=MagicMock())
_gmaps_patcher.start()

_groq_patcher = patch("groq.Groq", return_value=MagicMock())
_groq_patcher.start()

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# StaticPool forces all connections to reuse the same underlying
# in-memory SQLite connection so that data seeded in one session is
# visible to sessions opened by the request handler.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.core.security import get_password_hash, create_access_token  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.profile import UserProfile  # noqa: E402
from app.models.analysis import Analysis  # noqa: E402


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Create all tables before each test; drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(reset_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(reset_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def token(test_user):
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_profile(db, test_user):
    profile = UserProfile(
        user_id=test_user.id,
        work_hours="9:00 - 17:00",
        work_address="789 Work St, New York, NY",
        commute_preference="driving",
        sleep_hours="23:00 - 07:00",
        noise_preference="moderate",
        hobbies=["gym", "hiking"],
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def analysis(db, test_user):
    a = Analysis(
        user_id=test_user.id,
        current_address="123 Main St, New York, NY",
        destination_address="456 Oak Ave, Los Angeles, CA",
        overall_weighted_score=75.5,
        overall_grade="B+",
        crime_safety_score=80.0,
        cost_affordability_score=70.0,
        noise_environment_score=75.0,
        lifestyle_score=72.0,
        convenience_score=68.0,
        overview_summary="Good move overall.",
        lifestyle_changes=["More sunshine", "Higher traffic"],
        ai_insights="This looks promising.",
        action_steps_json=json.dumps(["Research neighborhoods", "Visit the city"]),
        crime_data={"destination": {"safety_score": 80}, "comparison": {}},
        cost_data={"destination": {"affordability_score": 70}, "comparison": {}},
        noise_data={"destination": {"noise_score": 75}, "comparison": {}},
        amenities_data={"destination": {"total_count": 5}},
        commute_data={"duration_minutes": 30, "method": "driving", "convenience_score": 68.0},
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a
