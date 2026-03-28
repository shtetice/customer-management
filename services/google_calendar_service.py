"""
Google Calendar sync service — one-way push (app → Google Calendar).

Setup flow:
  1. User creates a Google Cloud project, enables Calendar API, downloads
     credentials.json (OAuth 2.0 Desktop client).
  2. In Settings → Google Calendar, user picks credentials.json and clicks
     "חבר לחשבון Google".  The browser opens for OAuth consent.
  3. Token is saved to google_token.json next to the app.
  4. All subsequent syncs use the saved refresh token automatically.
"""
from __future__ import annotations
import logging
import os
from datetime import timedelta

logger = logging.getLogger(__name__)

_SCOPES      = ["https://www.googleapis.com/auth/calendar"]
_TOKEN_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "google_token.json")
_TOKEN_PATH  = os.path.normpath(_TOKEN_PATH)
_TZ          = "Asia/Jerusalem"


class GoogleCalendarService:

    # ── Auth ──────────────────────────────────────────────────

    def is_connected(self) -> bool:
        """True when a valid (or refreshable) token exists."""
        if not os.path.exists(_TOKEN_PATH):
            return False
        try:
            self._credentials()
            return True
        except Exception:
            return False

    def authorize(self, client_secret_path: str) -> tuple[bool, str]:
        """
        Run the OAuth2 browser flow with the supplied credentials.json.
        Returns (success, error_message).
        """
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, _SCOPES)
            creds = flow.run_local_server(port=0)
            with open(_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
            return True, ""
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        """Remove the saved token (revoke local access)."""
        if os.path.exists(_TOKEN_PATH):
            os.remove(_TOKEN_PATH)

    def _credentials(self):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        if not os.path.exists(_TOKEN_PATH):
            raise RuntimeError("לא מחובר לחשבון Google.")
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, _SCOPES)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(_TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())
            else:
                raise RuntimeError("פג תוקף החיבור ל-Google. יש להתחבר מחדש.")
        return creds

    def _service(self):
        from googleapiclient.discovery import build
        return build("calendar", "v3", credentials=self._credentials())

    def _cal_id(self) -> str:
        from services.settings_service import settings_service
        return settings_service.get("google_calendar_id", "primary") or "primary"

    # ── Push a single appointment ─────────────────────────────

    def push_appointment(self, appt, customer_name: str) -> str:
        """
        Create or update a Google Calendar event for *appt*.
        Returns the Google event ID.
        """
        end_dt = appt.date + timedelta(minutes=max(appt.duration_minutes or 60, 1))
        description_parts = []
        if appt.staff_name:
            description_parts.append(f"מטפל: {appt.staff_name}")
        if appt.notes:
            description_parts.append(appt.notes)

        body = {
            "summary":     f"תור: {customer_name}",
            "description": "\n".join(description_parts),
            "start":       {"dateTime": appt.date.isoformat(), "timeZone": _TZ},
            "end":         {"dateTime": end_dt.isoformat(),    "timeZone": _TZ},
        }

        svc    = self._service()
        cal_id = self._cal_id()

        if appt.google_event_id:
            try:
                event = svc.events().update(
                    calendarId=cal_id, eventId=appt.google_event_id, body=body
                ).execute()
                return event["id"]
            except Exception:
                pass   # event may have been deleted on Google's side → create fresh

        event = svc.events().insert(calendarId=cal_id, body=body).execute()
        return event["id"]

    # ── Delete a single event ─────────────────────────────────

    def delete_event(self, google_event_id: str):
        """Delete the Google Calendar event. Silently ignores missing events."""
        try:
            self._service().events().delete(
                calendarId=self._cal_id(), eventId=google_event_id
            ).execute()
        except Exception:
            pass

    # ── Full sync ─────────────────────────────────────────────

    def sync_all(self) -> tuple[int, int]:
        """
        Push every appointment to Google Calendar.
        Returns (synced_count, error_count).
        """
        from controllers.appointment_controller import appointment_controller
        from controllers.customer_controller   import customer_controller
        from datetime import datetime

        start = datetime(datetime.now().year - 1, 1, 1)
        end   = datetime(datetime.now().year + 2, 1, 1)
        appointments   = appointment_controller.get_by_date_range(start, end)
        customer_names = {
            c.id: f"{c.name} {c.surname}"
            for cid in {a.customer_id for a in appointments}
            if (c := customer_controller.get_by_id(cid))
        }

        synced = errors = 0
        for appt in appointments:
            name = customer_names.get(appt.customer_id, "לקוח")
            try:
                event_id = self.push_appointment(appt, name)
                if event_id != appt.google_event_id:
                    appointment_controller.set_google_event_id(appt.id, event_id)
                synced += 1
            except Exception as e:
                logger.warning(f"Google sync failed for appointment {appt.id}: {e}")
                errors += 1

        return synced, errors


google_calendar_service = GoogleCalendarService()
