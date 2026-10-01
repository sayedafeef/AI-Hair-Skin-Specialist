import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_URL = f"sqlite:///{BASE_DIR / 'app.db'}"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)

# SQLite needs this flag when accessed from multiple threads (FastAPI's default
# thread pool for sync endpoints). Any other DB URL (e.g. Postgres) ignores it.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
