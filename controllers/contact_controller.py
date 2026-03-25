from datetime import datetime
from database.db import get_session
from database.models import ContactLog


class ContactController:

    def get_by_customer(self, customer_id: int) -> list[ContactLog]:
        session = get_session()
        try:
            logs = (
                session.query(ContactLog)
                .filter_by(customer_id=customer_id)
                .order_by(ContactLog.date.desc())
                .all()
            )
            for log in logs:
                session.expunge(log)
            return logs
        finally:
            session.close()

    def get_by_id(self, log_id: int) -> ContactLog | None:
        session = get_session()
        try:
            log = session.query(ContactLog).filter_by(id=log_id).first()
            if log:
                session.expunge(log)
            return log
        finally:
            session.close()

    def create(self, customer_id: int, date: datetime, subject: str, content: str) -> ContactLog:
        if not subject or not subject.strip():
            raise ValueError("נושא הפנייה הוא שדה חובה")
        session = get_session()
        try:
            log = ContactLog(
                customer_id=customer_id,
                date=date,
                subject=subject.strip(),
                content=content.strip() if content else None,
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            session.expunge(log)
            return log
        finally:
            session.close()

    def update(self, log_id: int, date: datetime, subject: str, content: str) -> ContactLog:
        if not subject or not subject.strip():
            raise ValueError("נושא הפנייה הוא שדה חובה")
        session = get_session()
        try:
            log = session.query(ContactLog).filter_by(id=log_id).first()
            if not log:
                raise ValueError(f"רשומת קשר עם מזהה {log_id} לא נמצאה")
            log.date = date
            log.subject = subject.strip()
            log.content = content.strip() if content else None
            session.commit()
            session.refresh(log)
            session.expunge(log)
            return log
        finally:
            session.close()

    def delete(self, log_id: int):
        session = get_session()
        try:
            log = session.query(ContactLog).filter_by(id=log_id).first()
            if not log:
                raise ValueError(f"רשומת קשר עם מזהה {log_id} לא נמצאה")
            session.delete(log)
            session.commit()
        finally:
            session.close()


contact_controller = ContactController()
