from __future__ import annotations
from datetime import datetime, timedelta
from unittest.mock import patch
import pytest

from controllers.campaign_controller import CampaignController
from controllers.customer_controller import CustomerController
from database.models import CustomerStatus, Gender


@pytest.fixture
def ctrl():
    return CampaignController()


@pytest.fixture
def customer_ctrl():
    return CustomerController()


def _make_customer(customer_ctrl, name="רחל", surname="לוי", phone="050-1111111"):
    return customer_ctrl.create(
        name, surname, Gender.FEMALE, phone, "", "", "", CustomerStatus.CUSTOMER, ""
    )


# ── send_campaign ─────────────────────────────────────────────────────────────

def test_send_campaign_creates_campaign_row(ctrl, customer_ctrl):
    c = _make_customer(customer_ctrl)
    with patch("services.notification_service.notification_service.send_message", return_value=True):
        camp_id, sent, failed, skipped = ctrl.send_campaign(
            "הודעת בדיקה", [c], name="קמפיין בדיקה"
        )
    assert camp_id is not None
    assert sent == 1
    assert failed == 0
    assert skipped == 0


def test_send_campaign_stores_name(ctrl, customer_ctrl):
    c = _make_customer(customer_ctrl)
    with patch("services.notification_service.notification_service.send_message", return_value=True):
        camp_id, *_ = ctrl.send_campaign("בדיקה", [c], name="שם קמפיין")
    camps = ctrl.get_all()
    assert camps[0].name == "שם קמפיין"


def test_send_campaign_name_not_shadowed_by_customer_name(ctrl, customer_ctrl):
    """Regression: campaign name must not be overwritten by customer full_name in the loop."""
    c1 = _make_customer(customer_ctrl, name="יוסי", surname="כהן")
    c2 = _make_customer(customer_ctrl, name="מיכל", surname="לוי", phone="050-2222222")
    with patch("services.notification_service.notification_service.send_message", return_value=True):
        camp_id, *_ = ctrl.send_campaign("בדיקה", [c1, c2], name="קמפיין ראשון")
    assert ctrl.get_all()[0].name == "קמפיין ראשון"


def test_send_campaign_skips_ids(ctrl, customer_ctrl):
    c = _make_customer(customer_ctrl)
    with patch("services.notification_service.notification_service.send_message", return_value=True):
        camp_id, sent, failed, skipped = ctrl.send_campaign(
            "בדיקה", [c], skip_ids={c.id}, name="קמפיין"
        )
    assert sent == 0
    assert skipped == 1


def test_send_campaign_records_failed_when_no_phone(ctrl, customer_ctrl):
    c = _make_customer(customer_ctrl, phone="")
    with patch("services.notification_service.notification_service.send_message", return_value=False):
        camp_id, sent, failed, skipped = ctrl.send_campaign("בדיקה", [c], name="קמפיין")
    assert failed == 1
    assert sent == 0


def test_send_campaign_records_failed_when_send_fails(ctrl, customer_ctrl):
    c = _make_customer(customer_ctrl)
    with patch("services.notification_service.notification_service.send_message", return_value=False):
        camp_id, sent, failed, skipped = ctrl.send_campaign("בדיקה", [c], name="קמפיין")
    assert failed == 1
    assert sent == 0


# ── count_recipients ──────────────────────────────────────────────────────────

def test_count_recipients_correct(ctrl, customer_ctrl):
    c1 = _make_customer(customer_ctrl, phone="050-1111111")
    c2 = _make_customer(customer_ctrl, phone="050-2222222")
    c3 = _make_customer(customer_ctrl, phone="050-3333333")

    def fake_send(phone, msg):
        return phone == "050-1111111"  # only c1 succeeds

    with patch("services.notification_service.notification_service.send_message", side_effect=fake_send):
        camp_id, *_ = ctrl.send_campaign(
            "בדיקה", [c1, c2, c3], skip_ids={c3.id}, name="קמפיין"
        )

    counts = ctrl.count_recipients(camp_id)
    assert counts["sent"] == 1
    assert counts["failed"] == 1
    assert counts["skipped"] == 1


# ── get_recent_recipient_ids ──────────────────────────────────────────────────

def test_get_recent_recipient_ids_includes_recent(ctrl, customer_ctrl):
    c = _make_customer(customer_ctrl)
    with patch("services.notification_service.notification_service.send_message", return_value=True):
        ctrl.send_campaign("בדיקה", [c], name="קמפיין")
    ids = ctrl.get_recent_recipient_ids(days=7)
    assert c.id in ids


def test_get_recent_recipient_ids_excludes_old(ctrl, customer_ctrl):
    from database.db import get_session
    from database.models import Campaign, CampaignRecipient

    c = _make_customer(customer_ctrl)
    # Manually insert a campaign with a sent_at older than 7 days
    session = get_session()
    old_time = datetime.now() - timedelta(days=10)
    camp = Campaign(name="ישן", message="ישן", sent_at=old_time)
    session.add(camp)
    session.flush()
    session.add(CampaignRecipient(
        campaign_id=camp.id, customer_id=c.id,
        customer_name=f"{c.name} {c.surname}", phone=c.phone, status="sent"
    ))
    session.commit()
    session.close()

    ids = ctrl.get_recent_recipient_ids(days=7)
    assert c.id not in ids


def test_get_recent_recipient_ids_excludes_failed(ctrl, customer_ctrl):
    c = _make_customer(customer_ctrl)
    with patch("services.notification_service.notification_service.send_message", return_value=False):
        ctrl.send_campaign("בדיקה", [c], name="קמפיין")
    ids = ctrl.get_recent_recipient_ids(days=7)
    assert c.id not in ids


# ── get_all_with_counts ───────────────────────────────────────────────────────

def test_get_all_with_counts_returns_correct_totals(ctrl, customer_ctrl):
    c1 = _make_customer(customer_ctrl, phone="050-1111111")
    c2 = _make_customer(customer_ctrl, phone="050-2222222")

    with patch("services.notification_service.notification_service.send_message", return_value=True):
        ctrl.send_campaign("בדיקה", [c1, c2], name="קמפיין א")

    rows = ctrl.get_all_with_counts()
    assert len(rows) == 1
    camp, sent, failed, skipped = rows[0]
    assert camp.name == "קמפיין א"
    assert sent == 2
    assert failed == 0
    assert skipped == 0


def test_get_all_with_counts_empty(ctrl):
    assert ctrl.get_all_with_counts() == []
