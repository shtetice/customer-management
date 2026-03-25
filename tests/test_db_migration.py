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
    """Engine simulating a pre-migration DB — all tables exist but missing the added columns."""
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
        conn.execute(text("""
            CREATE TABLE receipts (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                amount VARCHAR(20) NOT NULL,
                date DATETIME NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                created_at DATETIME
            )
        """))
        conn.commit()
    return engine


def test_migrate_adds_missing_columns(bare_engine, monkeypatch):
    monkeypatch.setattr(db_module, "engine", bare_engine)

    db_module._migrate()

    customer_cols = _column_names(bare_engine, "customers")
    assert "phone2" in customer_cols
    assert "phone3" in customer_cols
    assert "address" in customer_cols
    assert "date_of_birth" in customer_cols
    assert "profile_photo_path" in customer_cols

    receipt_cols = _column_names(bare_engine, "receipts")
    assert "pdf_path" in receipt_cols

    user_cols = _column_names(bare_engine, "users")
    assert "is_active" in user_cols


def test_migrate_is_idempotent(bare_engine, monkeypatch):
    """Running _migrate() twice must not raise."""
    monkeypatch.setattr(db_module, "engine", bare_engine)

    db_module._migrate()
    db_module._migrate()  # second call — no error expected

    cols = _column_names(bare_engine, "customers")
    assert cols.count("address") == 1
