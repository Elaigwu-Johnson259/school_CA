"""
Database session setup.

`SessionLocal` is a factory for database sessions. FastAPI endpoints get a
fresh session per request via the `get_db` dependency, and the session is
always closed afterwards, even if the request raised an error.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# SQLite needs check_same_thread=False to be used across FastAPI's request
# threads, and foreign key enforcement (including ON DELETE CASCADE) is
# OFF by default per-connection unless we turn it on ourselves.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
