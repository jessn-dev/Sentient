import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool  # ✅ REQUIRED for in-memory tests

from app.main import app
# Import the model to ensure SQLModel knows about the table structure
from app.models import Prediction
from app.core.database import get_session
from app.core.auth import get_current_user


@pytest.fixture(name="session")
def session_fixture():
    # ✅ Use StaticPool to ensure all connections share the same in-memory DB
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # Create the tables in this shared database
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # Cleanup (optional for in-memory, but good practice)
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    # Override the get_session dependency to use our test session
    def get_session_override():
        return session

    # Override auth to always return a fake user ID (skips login)
    def get_current_user_override():
        return "test-user-id"

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_user] = get_current_user_override

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()