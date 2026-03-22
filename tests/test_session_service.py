import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from services.session_service import SessionService


@pytest.fixture
def svc(tmp_path):
    s = SessionService()
    s_file = tmp_path / "test_session.json"
    import services.session_service as mod
    original = mod.SESSION_FILE
    mod.SESSION_FILE = s_file
    s.__class__.__init__(s)
    # patch the module-level constant on the instance via module
    yield s, s_file
    mod.SESSION_FILE = original


def _make_svc(tmp_path):
    import services.session_service as mod
    svc = SessionService()
    mod.SESSION_FILE = tmp_path / "session.json"
    return svc


def test_save_and_load(tmp_path):
    import services.session_service as mod
    mod.SESSION_FILE = tmp_path / "session.json"
    svc = SessionService()
    svc.save(1, "admin")
    result = svc.load()
    assert result is not None
    assert result["user_id"] == 1
    assert result["username"] == "admin"


def test_load_returns_none_when_no_file(tmp_path):
    import services.session_service as mod
    mod.SESSION_FILE = tmp_path / "session.json"
    svc = SessionService()
    assert svc.load() is None


def test_load_returns_none_after_24_hours(tmp_path):
    import services.session_service as mod
    mod.SESSION_FILE = tmp_path / "session.json"
    svc = SessionService()
    svc.save(1, "admin")

    old_time = datetime.now() - timedelta(hours=25)
    with patch("services.session_service.datetime") as mock_dt:
        mock_dt.now.return_value = datetime.now()
        mock_dt.fromisoformat = datetime.fromisoformat
        # Simulate the saved login_time being 25 hours ago
        import json
        data = json.loads(mod.SESSION_FILE.read_text())
        data["login_time"] = old_time.isoformat()
        mod.SESSION_FILE.write_text(json.dumps(data))

    assert svc.load() is None


def test_clear_removes_file(tmp_path):
    import services.session_service as mod
    mod.SESSION_FILE = tmp_path / "session.json"
    svc = SessionService()
    svc.save(1, "admin")
    assert mod.SESSION_FILE.exists()
    svc.clear()
    assert not mod.SESSION_FILE.exists()


def test_clear_on_missing_file_does_not_raise(tmp_path):
    import services.session_service as mod
    mod.SESSION_FILE = tmp_path / "session.json"
    svc = SessionService()
    svc.clear()  # should not raise
