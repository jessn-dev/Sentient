from sqlmodel import SQLModel, Field, create_engine, Session, text
from datetime import date
import os

# --- Database Model ---
class Prediction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    symbol: str
    initial_price: float = Field(default=0.0)
    target_price: float = Field(default=0.0)
    final_price: float = Field(default=0.0) # <--- NEW: Locks the price 7 days later
    end_date: date
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
        # Check for 'final_price'
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

        # (Keep your existing checks for initial_price/target_price here if needed)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    _migrate_db()

def get_session():
    with Session(engine) as session:
        yield session