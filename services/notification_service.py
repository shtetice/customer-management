"""
Notification service — WhatsApp Business Cloud API (Meta).

Currently a stub: methods raise NotImplementedError until API credentials
are configured via settings.  Wire in 'whatsapp_token' and
'whatsapp_phone_id' (from Meta Business Manager) when ready.

Usage once live:
    notification_service.send_reminder(phone, customer_name, appointment_dt)
    notification_service.send_followup(phone, customer_name)
"""
from datetime import datetime


class NotificationService:

    def send_reminder(self, phone: str, customer_name: str, appointment_dt: datetime) -> bool:
        """Send a 24-hour appointment reminder via WhatsApp. Returns True on success."""
        raise NotImplementedError(
            "WhatsApp Business Cloud API not configured. "
            "Set 'whatsapp_token' and 'whatsapp_phone_id' in settings."
        )

    def send_followup(self, phone: str, customer_name: str) -> bool:
        """Send a 72-hour post-appointment follow-up via WhatsApp. Returns True on success."""
        raise NotImplementedError(
            "WhatsApp Business Cloud API not configured. "
            "Set 'whatsapp_token' and 'whatsapp_phone_id' in settings."
        )


notification_service = NotificationService()
