import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Import your real app and get_session function
from app.main import app, get_session
from app.config import settings

# 1. Create an In-Memory SQLite Database (Destroyed after tests)
# connect_args={"check_same_thread": False} is needed for SQLite + FastAPI
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# 2. Override the Dependency
# This forces the app to use our fake DB instead of the real file/Postgres
def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

# 3. Create the Test Client Fixture
@pytest.fixture(name="client")
def client_fixture():
    # Create tables in the fake DB
    SQLModel.metadata.create_all(engine)

    with TestClient(app) as client:
        yield client

    # Drop tables after test (Clean slate)
    SQLModel.metadata.drop_all(engine)