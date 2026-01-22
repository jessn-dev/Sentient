from sqlmodel import SQLModel, Field, create_engine, Session, text
from datetime import date
from typing import Optional
import os

# --- Database Model ---
class Prediction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str
    initial_price: float = Field(default=0.0)
    target_price: float = Field(default=0.0)
    final_price: float = Field(default=0.0)
    end_date: date
    finalized_date: Optional[date] = Field(default=None) # <--- NEW COLUMN
    created_at: date = Field(default_factory=date.today)

# --- Connection Logic ---
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./watchlist.db")

if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

def _migrate_db():
    """Safely adds missing columns to existing database."""
    with Session(engine) as session:
        # Check/Add 'final_price'
        try:
            session.exec(text("SELECT final_price FROM prediction LIMIT 1"))
        except Exception:
            print("⚠️ Migration: 'final_price' missing. Adding...")
            try:
                session.exec(text("ALTER TABLE prediction ADD COLUMN final_price FLOAT DEFAULT 0.0"))
                session.commit()
                print("✅ Added 'final_price'.")
            except Exception as e:
                print(f"❌ Failed to add 'final_price': {e}")

        # Check/Add 'finalized_date'
        try:
            session.exec(text("SELECT finalized_date FROM prediction LIMIT 1"))
        except Exception:
            print("⚠️ Migration: 'finalized_date' missing. Adding...")
            try:
                session.exec(text("ALTER TABLE prediction ADD COLUMN finalized_date DATE DEFAULT NULL"))
                session.commit()
                print("✅ Added 'finalized_date'.")
            except Exception as e:
                print(f"❌ Failed to add 'finalized_date': {e}")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    _migrate_db()

def get_session():
    with Session(engine) as session:
        yield session