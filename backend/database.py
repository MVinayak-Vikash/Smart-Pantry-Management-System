import os
from pathlib import Path
from sqlalchemy import create_engine
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


def init_db():
    """
    Initialize database tables and seed the 4 initial pantry items if they do not exist.
    """
    from backend import models, crud
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        crud.seed_initial_items(db)
    finally:
        db.close()
