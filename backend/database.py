import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default to SQLite, configurable via environment for future PostgreSQL / Supabase
DEFAULT_SQLITE_PATH = DATA_DIR / "pantry.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")

# For SQLite, check_same_thread=False allows multi-threaded FastAPI execution
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Columns to auto-migrate if existing SQLite database lacks newly added fields
NEW_ITEM_COLUMNS = [
    ("household_id", "INTEGER DEFAULT 1"),
    ("category", "VARCHAR DEFAULT 'General'"),
    ("serving_size_g", "FLOAT DEFAULT 50.0"),
    ("calories_per_100g", "FLOAT DEFAULT 0.0"),
    ("carbohydrates_per_100g", "FLOAT DEFAULT 0.0"),
    ("protein_per_100g", "FLOAT DEFAULT 0.0"),
    ("fat_per_100g", "FLOAT DEFAULT 0.0"),
    ("sugar_per_100g", "FLOAT DEFAULT 0.0"),
    ("sodium_mg_per_100g", "FLOAT DEFAULT 0.0"),
    ("fiber_per_100g", "FLOAT DEFAULT 0.0"),
    ("expiry_date", "DATETIME"),
    ("storage_location", "VARCHAR DEFAULT 'Pantry Shelf'"),
    ("is_perishable", "BOOLEAN DEFAULT 0"),
    ("active", "BOOLEAN DEFAULT 1"),
]


def auto_migrate_sqlite(target_engine=None):
    """
    Check existing SQLite tables and dynamically add newly added columns
    to preserve existing data and avoid schema mismatches without full migrations.
    """
    eng = target_engine or engine
    try:
        with eng.connect() as conn:
            inspector = inspect(eng)
            tables = inspector.get_table_names()
            if "items" in tables:
                existing_cols = {c["name"] for c in inspector.get_columns("items")}
                for col_name, col_type in NEW_ITEM_COLUMNS:
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE items ADD COLUMN {col_name} {col_type}"))
                conn.commit()
    except Exception as e:
        # Non-critical if in-memory or fresh DB
        pass


def get_db():
    """
    FastAPI dependency yielding a database session per request.
    Closes the session cleanly after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None):
    """
    Initialize database tables, run auto-migration for existing SQLite files,
    and seed default household, initial pantry items, and recipes.
    """
    from backend import models, crud
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)
    auto_migrate_sqlite(eng)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    db = Session()
    try:
        crud.seed_default_household(db)
        crud.seed_initial_items(db)
        crud.seed_initial_recipes(db)
    finally:
        db.close()
