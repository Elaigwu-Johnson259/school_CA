"""
Shared pytest fixtures.

Every test gets its own fresh in-memory SQLite database. Using an
in-memory DB (rather than the real school_results.db) keeps tests fast
and completely isolated from your local dev data.
"""
import os

# Settings are read from the environment at import time (see
# app/core/config.py). Setting sensible test defaults here means `pytest`
# works out of the box even if you haven't created a .env file yet, and
# never touches your real school_results.db either way.
os.environ.setdefault("DATABASE_URL", "sqlite:///./school_results.db")
os.environ.setdefault("JWT_SECRET", "test-only-secret-not-for-production")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base

# Importing app.models registers every model class on Base.metadata,
# which is what lets Base.metadata.create_all(engine) below create every
# table below, not just the ones we happen to import directly in a test.
import app.models  # noqa: F401


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    """
    A TestClient wired to use the same in-memory `db_session` as the app's
    `get_db` dependency, so API tests (login, /me, /refresh, ...) read and
    write the exact same data a test sets up directly via db_session.
    """
    from app.core.database import get_db
    from app.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
