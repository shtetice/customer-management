from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import or_
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

    def search_appointments(
        self,
        customer_ids: list[int],
        text_query: str,
        start: datetime | None,
        end: datetime | None,
    ) -> list[Appointment]:
        """Return appointments whose customer is in customer_ids OR whose staff_name/notes
        contain text_query, filtered by the optional date range."""
        session = get_session()
        try:
            like = f"%{text_query}%"
            conditions = []
            if customer_ids:
                conditions.append(Appointment.customer_id.in_(customer_ids))
            conditions.append(Appointment.staff_name.ilike(like))
            conditions.append(Appointment.notes.ilike(like))
            q = session.query(Appointment).filter(or_(*conditions))
            if start is not None:
                q = q.filter(Appointment.date >= start)
            if end is not None:
                q = q.filter(Appointment.date < end)
            appts = q.order_by(Appointment.date).all()
            for a in appts:
                session.expunge(a)
            return appts
        finally:
            session.close()

    def get_by_customer_ids_and_range(
        self,
        customer_ids: list[int],
        start: datetime | None,
        end: datetime | None,
    ) -> list[Appointment]:
        session = get_session()
        try:
            q = session.query(Appointment).filter(Appointment.customer_id.in_(customer_ids))
            if start is not None:
                q = q.filter(Appointment.date >= start)
            if end is not None:
                q = q.filter(Appointment.date < end)
            appts = q.order_by(Appointment.date).all()
            for a in appts:
                session.expunge(a)
            return appts
        finally:
            session.close()

    def get_by_date_range(self, start: datetime, end: datetime) -> list[Appointment]:
        session = get_session()
        try:
            appts = (
                session.query(Appointment)
                .filter(Appointment.date >= start, Appointment.date < end)
                .order_by(Appointment.date)
                .all()
            )
            for a in appts:
                session.expunge(a)
            return appts
        finally:
            session.close()

    def get_pending_reminders(self) -> list[Appointment]:
        """Scheduled appointments within the next 24h not yet reminded."""
        now = datetime.now()
        session = get_session()
        try:
            appts = (
                session.query(Appointment)
                .filter(
                    Appointment.date > now,
                    Appointment.date <= now + timedelta(hours=24),
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
        """Completed appointments in the past 72h not yet followed up."""
        now = datetime.now()
        session = get_session()
        try:
            appts = (
                session.query(Appointment)
                .filter(
                    Appointment.date >= now - timedelta(hours=72),
                    Appointment.date < now,
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

    def get_overlapping(
        self,
        date: datetime,
        duration_minutes: int,
        exclude_id: int | None = None,
    ) -> list[Appointment]:
        """Return SCHEDULED appointments whose time range overlaps [date, date+duration)."""
        our_end = date + timedelta(minutes=max(duration_minutes, 1))
        session = get_session()
        try:
            q = (
                session.query(Appointment)
                .filter(
                    Appointment.status == AppointmentStatus.SCHEDULED,
                    Appointment.date < our_end,
                )
            )
            if exclude_id is not None:
                q = q.filter(Appointment.id != exclude_id)
            appts = q.all()
            # Second filter: their end must be after our start
            result = []
            for a in appts:
                their_end = a.date + timedelta(minutes=max(a.duration_minutes, 1))
                if their_end > date:
                    result.append(a)
            for a in result:
                session.expunge(a)
            return result
        finally:
            session.close()


    def get_scheduled_in_window(self, start: datetime, end: datetime) -> list[Appointment]:
        """Return SCHEDULED appointments whose date falls in (start, end]."""
        session = get_session()
        try:
            appts = (
                session.query(Appointment)
                .filter(
                    Appointment.status == AppointmentStatus.SCHEDULED,
                    Appointment.date > start,
                    Appointment.date <= end,
                )
                .order_by(Appointment.date)
                .all()
            )
            for a in appts:
                session.expunge(a)
            return appts
        finally:
            session.close()

    def get_completed_in_window(self, start: datetime, end: datetime) -> list[Appointment]:
        """Return COMPLETED appointments whose date falls in [start, end)."""
        session = get_session()
        try:
            appts = (
                session.query(Appointment)
                .filter(
                    Appointment.status == AppointmentStatus.COMPLETED,
                    Appointment.date >= start,
                    Appointment.date < end,
                )
                .order_by(Appointment.date)
                .all()
            )
            for a in appts:
                session.expunge(a)
            return appts
        finally:
            session.close()


appointment_controller = AppointmentController()
