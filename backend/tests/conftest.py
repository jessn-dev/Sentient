import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app, get_session

# 1. Create a shared in-memory DB that persists for the whole test session
# StaticPool is CRITICAL: it prevents the DB from being deleted when connections close
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# 2. Override the API's dependency
def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

# 3. Client Fixture (Setup/Teardown DB per test)
@pytest.fixture(name="client")
def client_fixture():
    # Create tables before each test
    SQLModel.metadata.create_all(engine)

    with TestClient(app) as client:
        yield client

    # Drop tables after each test (Clean slate)
    SQLModel.metadata.drop_all(engine)

# 4. Session Fixture (For checking DB content in tests)
@pytest.fixture(name="session")
def session_fixture():
    with Session(engine) as session:
        yield session