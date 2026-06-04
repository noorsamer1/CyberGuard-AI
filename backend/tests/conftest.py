"""Pytest fixtures — SQLite in-memory database for backend tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401 — register all models with Base.metadata


@pytest.fixture(autouse=True)
def disable_ai_detection(monkeypatch):
    """Prevent Celery/Redis AI queue calls from slowing or hanging tests."""
    monkeypatch.setattr(settings, "ai_detection_enabled", False)

ROOT = Path(__file__).resolve().parents[2]
RANGE_TARGET_DIR = ROOT / "range-target"
if str(RANGE_TARGET_DIR) not in sys.path:
    sys.path.insert(0, str(RANGE_TARGET_DIR))


@pytest.fixture()
def db_session():
    """Provide an isolated in-memory SQLite session per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
