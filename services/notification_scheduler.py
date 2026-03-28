"""
Background scheduler that sends WhatsApp reminders and follow-ups via Twilio.

- Checks every 5 minutes for due notifications
- Reminder: sent ~24h before a SCHEDULED appointment
- Follow-up: sent ~72h after a COMPLETED appointment
- Skips silently if Twilio credentials are not yet configured
"""
from __future__ import annotations
import logging
import threading

from controllers.appointment_controller import appointment_controller
from controllers.customer_controller import customer_controller
from services.notification_service import notification_service

logger = logging.getLogger(__name__)

_CHECK_INTERVAL_SECONDS = 5 * 60  # 5 minutes


class NotificationScheduler:

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

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
                self._process()
            except Exception as e:
                logger.error(f"Notification scheduler error: {e}")
            self._stop_event.wait(_CHECK_INTERVAL_SECONDS)

    def _process(self):
        if not notification_service.is_configured():
            return

        for appt in appointment_controller.get_pending_reminders():
            customer = customer_controller.get_by_id(appt.customer_id)
            if customer and customer.phone:
                ok = notification_service.send_reminder(
                    customer.phone,
                    f"{customer.name} {customer.surname}",
                    appt.date,
                )
                if ok:
                    appointment_controller.mark_reminder_sent(appt.id)
                    logger.info(f"Reminder sent for appointment {appt.id}")
                else:
                    logger.warning(f"Reminder failed for appointment {appt.id}")

        for appt in appointment_controller.get_pending_followups():
            customer = customer_controller.get_by_id(appt.customer_id)
            if customer and customer.phone:
                ok = notification_service.send_followup(
                    customer.phone,
                    f"{customer.name} {customer.surname}",
                )
                if ok:
                    appointment_controller.mark_followup_sent(appt.id)
                    logger.info(f"Follow-up sent for appointment {appt.id}")
                else:
                    logger.warning(f"Follow-up failed for appointment {appt.id}")


notification_scheduler = NotificationScheduler()
