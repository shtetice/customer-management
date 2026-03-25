from datetime import datetime, timedelta

import pytest

from services.activity_service import (
    delete_all_logs,
    get_logs,
    has_activity_since,
    log_action,
    purge_old_logs,
)


def test_log_action_writes_entry():
    log_action("admin", "test action")
    logs = get_logs()
    assert len(logs) == 1
    assert logs[0].username == "admin"
    assert logs[0].action == "test action"


def test_log_action_multiple_entries():
    log_action("admin", "action 1")
    log_action("user1", "action 2")
    logs = get_logs()
    assert len(logs) == 2
    # Ordered newest-first
    assert logs[0].action == "action 2"
    assert logs[1].action == "action 1"


def test_log_action_silent_on_bad_input():
    # Should not raise — bad data silently fails
    log_action(None, None)  # type: ignore


def test_get_logs_respects_limit():
    for i in range(10):
        log_action("admin", f"action {i}")
    logs = get_logs(limit=5)
    assert len(logs) == 5


def test_delete_all_logs_clears_table():
    log_action("admin", "will be deleted")
    delete_all_logs()
    assert get_logs() == []


def test_has_activity_since_true():
    before = datetime.utcnow() - timedelta(seconds=1)
    log_action("admin", "recent action")
    assert has_activity_since(before) is True


def test_has_activity_since_false():
    log_action("admin", "old action")
    future = datetime.utcnow() + timedelta(seconds=10)
    assert has_activity_since(future) is False


def test_has_activity_since_empty_log():
    after = datetime.utcnow() - timedelta(hours=1)
    assert has_activity_since(after) is False


def test_purge_old_logs_removes_old_entries(monkeypatch):
    from services import activity_service
    from database.db import get_session
    from database.models import ActivityLog

    # Insert an entry with a timestamp well in the past
    session = get_session()
    try:
        old_entry = ActivityLog(
            username="admin",
            action="old action",
            timestamp=datetime.utcnow() - timedelta(days=200),
        )
        session.add(old_entry)
        session.commit()
    finally:
        session.close()

    # Also insert a recent entry
    log_action("admin", "recent action")

    monkeypatch.setattr(
        "services.settings_service.settings_service.get",
        lambda key, default=None: 90 if key == "log_retention_days" else default,
    )

    purge_old_logs()

    logs = get_logs()
    assert len(logs) == 1
    assert logs[0].action == "recent action"


def test_purge_old_logs_keeps_entries_within_retention(monkeypatch):
    log_action("admin", "recent action")

    monkeypatch.setattr(
        "services.settings_service.settings_service.get",
        lambda key, default=None: 90 if key == "log_retention_days" else default,
    )

    purge_old_logs()
    assert len(get_logs()) == 1
