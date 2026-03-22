import json
import os
from datetime import datetime, timedelta
from pathlib import Path

SESSION_FILE = Path.home() / ".customer_mgmt_session.json"
SESSION_TTL_HOURS = 24


class SessionService:

    def save(self, user_id: int, username: str):
        """Persist a remembered session to disk."""
        data = {
            "user_id": user_id,
            "username": username,
            "login_time": datetime.now().isoformat(),
        }
        SESSION_FILE.write_text(json.dumps(data), encoding="utf-8")

    def load(self) -> dict | None:
        """
        Return saved session dict if it exists and is under 24 hours old.
        Returns None otherwise.
        """
        if not SESSION_FILE.exists():
            return None
        try:
            data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            login_time = datetime.fromisoformat(data["login_time"])
            if datetime.now() - login_time < timedelta(hours=SESSION_TTL_HOURS):
                return data
        except Exception:
            pass
        self.clear()
        return None

    def clear(self):
        """Remove the saved session file."""
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()


session_service = SessionService()
