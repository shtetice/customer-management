import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from database import db as db_module


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    """Replace the real SQLite DB with an in-memory DB for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", TestSession)

    # Seed features
    from database.db import _seed_features
    _seed_features()

    yield
