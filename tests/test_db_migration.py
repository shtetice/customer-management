"""Integration tests for database migration logic."""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.models import Base
from database import db as db_module


def _column_names(engine, table):
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return [row[1] for row in rows]


@pytest.fixture()
def bare_engine():
    """Engine with a customers table missing the migrated columns."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                surname VARCHAR(100) NOT NULL,
                gender VARCHAR(10),
                phone VARCHAR(30),
                email VARCHAR(150),
                status VARCHAR(20) NOT NULL DEFAULT 'lead',
                notes TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        conn.commit()
    return engine


def test_migrate_adds_missing_columns(bare_engine, monkeypatch):
    monkeypatch.setattr(db_module, "engine", bare_engine)

    db_module._migrate()

    cols = _column_names(bare_engine, "customers")
    assert "phone2" in cols
    assert "phone3" in cols
    assert "address" in cols
    assert "date_of_birth" in cols


def test_migrate_is_idempotent(bare_engine, monkeypatch):
    """Running _migrate() twice must not raise."""
    monkeypatch.setattr(db_module, "engine", bare_engine)

    db_module._migrate()
    db_module._migrate()  # second call — no error expected

    cols = _column_names(bare_engine, "customers")
    assert cols.count("address") == 1
