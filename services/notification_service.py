"""
Notification service — WhatsApp via Twilio.

Credentials are stored encrypted in settings:
  twilio_account_sid  — Twilio Account SID
  twilio_auth_token   — Twilio Auth Token

From number (sandbox): whatsapp:+12604002399
"""
from __future__ import annotations
import re
from datetime import datetime

from services.settings_service import settings_service


DEFAULT_RULES = [
    {
        "key": "reminder_24h",
        "type": "reminder",
        "hours": 24,
        "message": (
            "שלום {שם},\n"
            "תזכורת לתורך מחר {תאריך} בשעה {שעה}.\n"
            "נשמח לראותך! לשינוי או ביטול אנא צור/י קשר."
        ),
    },
    {
        "key": "followup_72h",
        "type": "followup",
        "hours": 72,
        "message": (
            "שלום {שם},\n"
            "תודה שביקרת אצלנו! נשמח לשמוע את דעתך ולראותך שוב בקרוב."
        ),
    },
]


def get_rules() -> list[dict]:
    """Return the active notification rules from settings, or the built-in defaults."""
    rules = settings_service.get("notification_rules", None)
    if rules is None:
        return DEFAULT_RULES
    return rules


def render_template(
    message: str,
    customer_name: str,
    appt_dt: datetime,
    staff_name: str = "",
) -> str:
    """Replace template tags in *message* with real values."""
    date_str = appt_dt.strftime("%d/%m/%Y")
    time_str = appt_dt.strftime("%H:%M")
    return (
        message
        .replace("{שם}", customer_name)
        .replace("{תאריך}", date_str)
        .replace("{שעה}", time_str)
        .replace("{מטפל}", staff_name or "")
    )


def _twilio_from() -> str:
    number = settings_service.get("twilio_from_number", "")
    if not number:
        raise RuntimeError("Twilio from-number is not configured in settings.")
    return f"whatsapp:{number}" if not number.startswith("whatsapp:") else number


def _normalize_phone(phone: str) -> str | None:
    """
    Normalize a stored phone number to E.164 with whatsapp: prefix.
    Handles Israeli local format (05X...) and international (+XXX...).
    Returns None if the number cannot be normalized.
    """
    if not phone:
        return None
    stripped = phone.strip()
    digits = re.sub(r'\D', '', stripped)
    if stripped.startswith('+'):
        return f"whatsapp:+{digits}" if digits else None
    if digits.startswith('972') and len(digits) >= 12:
        return f"whatsapp:+{digits}"
    if digits.startswith('0') and len(digits) >= 9:
        return f"whatsapp:+972{digits[1:]}"
    return None


class NotificationService:

    def is_configured(self) -> bool:
        """Return True if Twilio credentials are saved in settings."""
        return bool(
            settings_service.get("twilio_from_number")
            and settings_service.get_secret("twilio_account_sid")
            and settings_service.get_secret("twilio_auth_token")
        )

    def _client(self):
        from twilio.rest import Client
        sid = settings_service.get_secret("twilio_account_sid")
        token = settings_service.get_secret("twilio_auth_token")
        if not sid or not token:
            raise RuntimeError("Twilio credentials are not configured in settings.")
        return Client(sid, token)

    def send_message(self, phone: str, body: str) -> bool:
        """Send *body* to *phone* via WhatsApp. Returns True on success."""
        to = _normalize_phone(phone)
        if not to:
            return False
        try:
            self._client().messages.create(from_=_twilio_from(), to=to, body=body)
            return True
        except Exception:
            return False

    def send_test(self, phone: str) -> tuple[bool, str]:
        """
        Send a test message. Returns (success, error_message).
        Used by the Settings screen to verify credentials.
        """
        to = _normalize_phone(phone)
        if not to:
            return False, f"מספר טלפון לא תקין: {phone}"
        try:
            self._client().messages.create(
                from_=_twilio_from(),
                to=to,
                body="הודעת בדיקה ממערכת ניהול הלקוחות. הכל תקין!",
            )
            return True, ""
        except Exception as e:
            return False, str(e)


notification_service = NotificationService()
