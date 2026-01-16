from sqlmodel import SQLModel, create_engine, Session
import os

# We use an absolute path for the DB file to ensure Docker finds it in the volume
# "sqlite:////app/data/predictions.db" maps to the volume we set up
sqlite_file_name = "/app/data/predictions.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False is needed for SQLite with FastAPI
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    # Ensure the directory exists
    os.makedirs(os.path.dirname(sqlite_file_name), exist_ok=True)
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session