from datetime import datetime, timedelta

from database.db import get_session
from database.models import ActivityLog

LOG_RETENTION_DAYS = 90


def log_action(username: str, action: str):
    """Write a single audit entry. Fails silently so it never breaks the calling flow."""
    try:
        session = get_session()
        try:
            session.add(ActivityLog(username=username, action=action))
            session.commit()
        finally:
            session.close()
    except Exception:
        pass


def get_logs(limit: int = 500) -> list[ActivityLog]:
    session = get_session()
    try:
        logs = (
            session.query(ActivityLog)
            .order_by(ActivityLog.timestamp.desc())
            .limit(limit)
            .all()
        )
        for entry in logs:
            session.expunge(entry)
        return logs
    finally:
        session.close()


def delete_all_logs():
    session = get_session()
    try:
        session.query(ActivityLog).delete()
        session.commit()
    finally:
        session.close()


def has_activity_since(since: datetime) -> bool:
    """Return True if any log entry exists after `since`."""
    session = get_session()
    try:
        return session.query(ActivityLog).filter(ActivityLog.timestamp > since).first() is not None
    finally:
        session.close()


def purge_old_logs():
    """Delete logs older than the configured retention period. Called on app startup."""
    from services.settings_service import settings_service
    days = settings_service.get("log_retention_days", LOG_RETENTION_DAYS)
    cutoff = datetime.utcnow() - timedelta(days=int(days))
    session = get_session()
    try:
        session.query(ActivityLog).filter(ActivityLog.timestamp < cutoff).delete()
        session.commit()
    finally:
        session.close()
