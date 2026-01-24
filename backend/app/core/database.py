import os
from sqlmodel import SQLModel, create_engine, Session, text

# --- Connection Logic ---
# 1. Load the DB URL (defaults to local SQLite if not set)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./watchlist.db")

# 2. Create the Engine
# We handle SQLite specifically because it needs a special argument for multithreading
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)


def _migrate_db():
    """
    Manually checks for missing columns and adds them.
    This runs after table creation to handle schema updates on existing tables.
    """
    try:
        # Use a direct connection for DDL (Data Definition Language)
        with engine.connect() as conn:
            # AUTOCOMMIT is required for ALTER TABLE in some drivers/setups
            conn.execution_options(isolation_level="AUTOCOMMIT")

            # Check if 'finalized_date' column exists in the 'prediction' table
            check_col = text("""
                             SELECT column_name
                             FROM information_schema.columns
                             WHERE table_name = 'prediction'
                               AND column_name = 'finalized_date';
                             """)

            # Execute check
            result = conn.execute(check_col).fetchone()

            if not result:
                print("⚠️ Migration: 'finalized_date' missing. Adding...")
                conn.execute(text("ALTER TABLE prediction ADD COLUMN finalized_date DATE DEFAULT NULL"))
                print("✅ Migration: 'finalized_date' added.")
            else:
                # Optional: Comment out to reduce log noise
                print("✅ Migration: 'finalized_date' already exists.")

    except Exception as e:
        # We catch errors here so the app startup doesn't crash if migration fails
        # (e.g., if using SQLite where information_schema doesn't exist)
        print(f"ℹ️ Migration check skipped/failed (Safe to ignore on SQLite): {e}")


def create_db_and_tables():
    """
    Initializes the database schema and runs migrations.
    """
    # Import models here to ensure they are registered with SQLModel
    # and to avoid circular imports at the top level.
    from app.models import Prediction

    # Create tables if they don't exist
    SQLModel.metadata.create_all(engine)

    # Run manual migrations (alterations)
    _migrate_db()


def get_session():
    """
    Dependency to provide a database session.
    """
    with Session(engine) as session:
        yield session