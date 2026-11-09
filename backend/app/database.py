"""
SQLAlchemy Database Configuration and Session Management.

Supports SQLite for local development and PostgreSQL (e.g. Supabase)
for production deployment.
"""

from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.config import get_settings, BASE_DIR
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

database_url = settings.DATABASE_URL

# Handle SQLite directory creation automatically
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    # Ensure data directory exists
    db_relative = database_url.replace("sqlite:///", "").replace("sqlite://", "")
    db_path = BASE_DIR / db_relative.lstrip("./")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(database_url, connect_args=connect_args)
else:
    # Production PostgreSQL (Supabase)
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request,
    ensuring proper closure and cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Verify whether the configured database is reachable.
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

