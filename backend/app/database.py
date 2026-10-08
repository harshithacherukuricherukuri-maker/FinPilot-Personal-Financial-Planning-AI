import sys
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Ensure backend directory is in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.config import settings

_root_dir = _backend_dir.parent

# Engine configuration
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Ensure proper driver specification if generic postgresql:// is provided
if db_url.startswith("postgresql://"):
    try:
        import psycopg2  # noqa: F401
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        # Attempt quick connection to ensure Postgres is actually running
        test_engine = create_engine(db_url, connect_args={"connect_timeout": 2})
        with test_engine.connect():
            pass
        test_engine.dispose()
    except Exception as e:
        default_sqlite = _root_dir / "finpilot.db"
        print(f"Notice: PostgreSQL connection unavailable ({e}). Falling back to SQLite at {default_sqlite}")
        db_url = f"sqlite:///{default_sqlite.as_posix()}"

if db_url.startswith("sqlite:///./") or db_url == "sqlite:///finpilot.db":
    db_path = _root_dir / "finpilot.db"
    db_url = f"sqlite:///{db_path.as_posix()}"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all registered database tables safely."""
    # Import models here to ensure they are registered with Base metadata
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
