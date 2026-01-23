import pytest
import os
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_KEY"] = "mock-key"
os.environ["ALPACA_KEY"] = "mock-key"
os.environ["ALPACA_SECRET"] = "mock-secret"

# 1. Import the app
from app.main import app, get_session

# 2. CRITICAL: Import ALL models here.
# This registers them with SQLModel so create_all() knows they exist.
from app.models import Prediction
from app.auth import get_current_user

# 3. Create a temporary in-memory database for tests
# We do NOT use the engine from database.py because we want a blank slate.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    # Mock function to bypass real authentication
    def override_get_current_user():
        return "user_123"

    # Apply the overrides to the app instance
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    # Clear overrides to prevent leaking into other tests
    app.dependency_overrides.clear()