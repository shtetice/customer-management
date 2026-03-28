"""
Background scheduler that sends WhatsApp notifications via Twilio.

- Checks every 5 minutes for due notifications
- Rules are configured in Settings (notification_rules in settings.json)
- Default: reminder 24h before appointment, follow-up 72h after completed appointment
- Tracks sent notifications per rule per appointment in NotificationLog table
- Skips silently if Twilio credentials are not yet configured
"""
from __future__ import annotations
import logging
import threading
from datetime import datetime, timedelta

from database.db import get_session
from database.models import NotificationLog
from controllers.appointment_controller import appointment_controller
from controllers.customer_controller import customer_controller
from services.notification_service import notification_service, get_rules, render_template

logger = logging.getLogger(__name__)

_CHECK_INTERVAL_SECONDS = 5 * 60  # 5 minutes


def _get_sent_appointment_ids(rule_key: str) -> set[int]:
    """Return appointment IDs that already have a log entry for *rule_key*."""
    session = get_session()
    try:
        rows = (
            session.query(NotificationLog.appointment_id)
            .filter(NotificationLog.rule_key == rule_key)
            .all()
        )
        return {r[0] for r in rows}
    finally:
        session.close()


def _log_sent(appointment_id: int, rule_key: str):
    """Record that *rule_key* was sent for *appointment_id*."""
    session = get_session()
    try:
        session.add(NotificationLog(
            appointment_id=appointment_id,
            rule_key=rule_key,
            sent_at=datetime.now(),
        ))
        session.commit()
    finally:
        session.close()


class NotificationScheduler:

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._process_lock = threading.Lock()

    def start(self):
        """Start the background scheduler thread (idempotent)."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="NotificationScheduler",
        )
        self._thread.start()
        logger.info("Notification scheduler started.")

    def stop(self):
        """Signal the scheduler to stop at the next interval."""
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._create_auto_treatments()
            except Exception as e:
                logger.error(f"Auto-treatment error: {e}")
            try:
                self._process()
            except Exception as e:
                logger.error(f"Notification scheduler error: {e}")
            self._stop_event.wait(_CHECK_INTERVAL_SECONDS)

    def _create_auto_treatments(self):
        """For every past SCHEDULED appointment, auto-create a treatment and mark it COMPLETED."""
        from controllers.appointment_controller import appointment_controller
        from controllers.treatment_controller import treatment_controller

        for appt in appointment_controller.get_past_scheduled():
            if treatment_controller.get_by_appointment_id(appt.id):
                continue   # already processed
            treatment_controller.create_from_appointment(appt)
            appointment_controller.mark_completed(appt.id)
            logger.info(f"Auto-created treatment for appointment {appt.id}")

    def _process(self):
        if not self._process_lock.acquire(blocking=False):
            logger.info("Notification scheduler: _process already running, skipping.")
            return
        try:
            self._do_process()
        finally:
            self._process_lock.release()

    def _do_process(self):
        if not notification_service.is_configured():
            return

        now = datetime.now()

        for rule in get_rules():
            rule_key = rule.get("key", "")
            rule_type = rule.get("type", "")
            hours = int(rule.get("hours", 24))
            message_tpl = rule.get("message", "")

            if not rule_key or not rule_type or not message_tpl:
                continue

            if rule_type == "reminder":
                appts = appointment_controller.get_scheduled_in_window(
                    now, now + timedelta(hours=hours)
                )
            elif rule_type == "followup":
                appts = appointment_controller.get_completed_in_window(
                    now - timedelta(hours=hours), now
                )
            else:
                continue

            already_sent = _get_sent_appointment_ids(rule_key)

            for appt in appts:
                if appt.id in already_sent:
                    continue
                customer = customer_controller.get_by_id(appt.customer_id)
                if not customer or not customer.phone:
                    continue
                body = render_template(
                    message_tpl,
                    f"{customer.name} {customer.surname}",
                    appt.date,
                    appt.staff_name or "",
                )
                ok = notification_service.send_message(customer.phone, body)
                if ok:
                    _log_sent(appt.id, rule_key)
                    logger.info(
                        f"Rule '{rule_key}' sent for appointment {appt.id}"
                    )
                else:
                    logger.warning(
                        f"Rule '{rule_key}' failed for appointment {appt.id}"
                    )


notification_scheduler = NotificationScheduler()
