import os
from sqlmodel import create_engine, SQLModel, Session

# Default to SQLite for local, but allow env var for Prod
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./predictions.db")

# Fix: Postgres URLs usually start with "postgres://", SQLAlchemy needs "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session