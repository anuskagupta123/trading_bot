import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:1234@localhost:5432/trading_db",
)

import pytest
from fastapi.testclient import TestClient
from app.database.database import Base, engine
from app.database import models  # noqa: F401
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create all tables before test session and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    # optional teardown: drop tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Provide TestClient for FastAPI tests."""
    return TestClient(app)


def pytest_configure(config):
    """Ensure DB tables exist before pytest collects tests (pre-import hooks)."""
    Base.metadata.create_all(bind=engine)
