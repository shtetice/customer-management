from datetime import datetime, timedelta
from database.db import get_session
from database.models import Appointment, AppointmentStatus


class AppointmentController:

    def get_by_week(self, week_start: datetime) -> list[Appointment]:
        week_end = week_start + timedelta(days=7)
        session = get_session()
        try:
            appts = (
                session.query(Appointment)
                .filter(Appointment.date >= week_start, Appointment.date < week_end)
                .order_by(Appointment.date)
                .all()
            )
            for a in appts:
                session.expunge(a)
            return appts
        finally:
            session.close()

    def get_by_id(self, appt_id: int) -> Appointment | None:
        session = get_session()
        try:
            a = session.query(Appointment).filter_by(id=appt_id).first()
            if a:
                session.expunge(a)
            return a
        finally:
            session.close()

    def create(
        self,
        customer_id: int,
        date: datetime,
        duration_minutes: int,
        staff_name: str,
        notes: str,
    ) -> Appointment:
        session = get_session()
        try:
            appt = Appointment(
                customer_id=customer_id,
                date=date,
                duration_minutes=duration_minutes,
                staff_name=staff_name.strip() if staff_name else None,
                notes=notes.strip() if notes else None,
            )
            session.add(appt)
            session.commit()
            session.refresh(appt)
            session.expunge(appt)
            return appt
        finally:
            session.close()

    def update(
        self,
        appt_id: int,
        date: datetime,
        duration_minutes: int,
        staff_name: str,
        notes: str,
        status: AppointmentStatus,
    ) -> Appointment:
        session = get_session()
        try:
            a = session.query(Appointment).filter_by(id=appt_id).first()
            if not a:
                raise ValueError(f"תור עם מזהה {appt_id} לא נמצא")
            a.date = date
            a.duration_minutes = duration_minutes
            a.staff_name = staff_name.strip() if staff_name else None
            a.notes = notes.strip() if notes else None
            a.status = status
            a.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(a)
            session.expunge(a)
            return a
        finally:
            session.close()

    def delete(self, appt_id: int):
        session = get_session()
        try:
            a = session.query(Appointment).filter_by(id=appt_id).first()
            if not a:
                raise ValueError(f"תור עם מזהה {appt_id} לא נמצא")
            session.delete(a)
            session.commit()
        finally:
            session.close()

    def get_pending_reminders(self) -> list[Appointment]:
        """Scheduled appointments within the 24h reminder window not yet notified."""
        now = datetime.utcnow()
        session = get_session()
        try:
            appts = (
                session.query(Appointment)
                .filter(
                    Appointment.date >= now + timedelta(hours=23),
                    Appointment.date < now + timedelta(hours=25),
                    Appointment.reminder_sent == False,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                )
                .all()
            )
            for a in appts:
                session.expunge(a)
            return appts
        finally:
            session.close()

    def get_pending_followups(self) -> list[Appointment]:
        """Completed appointments within the 72h follow-up window not yet notified."""
        now = datetime.utcnow()
        session = get_session()
        try:
            appts = (
                session.query(Appointment)
                .filter(
                    Appointment.date >= now - timedelta(hours=73),
                    Appointment.date < now - timedelta(hours=71),
                    Appointment.followup_sent == False,
                    Appointment.status == AppointmentStatus.COMPLETED,
                )
                .all()
            )
            for a in appts:
                session.expunge(a)
            return appts
        finally:
            session.close()

    def mark_reminder_sent(self, appt_id: int):
        session = get_session()
        try:
            a = session.query(Appointment).filter_by(id=appt_id).first()
            if a:
                a.reminder_sent = True
                session.commit()
        finally:
            session.close()

    def mark_followup_sent(self, appt_id: int):
        session = get_session()
        try:
            a = session.query(Appointment).filter_by(id=appt_id).first()
            if a:
                a.followup_sent = True
                session.commit()
        finally:
            session.close()


appointment_controller = AppointmentController()
