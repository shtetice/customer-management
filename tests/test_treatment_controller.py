import pytest
from datetime import datetime
from controllers.treatment_controller import TreatmentController
from controllers.customer_controller import CustomerController
from database.models import CustomerStatus


@pytest.fixture
def customer():
    ctrl = CustomerController()
    return ctrl.create("אנה", "לוי", None, "", "", "", "", CustomerStatus.CUSTOMER, "")


@pytest.fixture
def ctrl():
    return TreatmentController()


def test_create_treatment(ctrl, customer):
    t = ctrl.create(customer.id, datetime(2026, 3, 1), "ניקוי פנים", "שרה", "הערה")
    assert t.id is not None
    assert t.description == "ניקוי פנים"
    assert t.performed_by == "שרה"


def test_create_treatment_missing_description_raises(ctrl, customer):
    with pytest.raises(ValueError, match="תיאור"):
        ctrl.create(customer.id, datetime(2026, 3, 1), "", "", "")


def test_get_by_customer_ordered_desc(ctrl, customer):
    ctrl.create(customer.id, datetime(2026, 1, 1), "טיפול א", "", "")
    ctrl.create(customer.id, datetime(2026, 3, 1), "טיפול ב", "", "")
    treatments = ctrl.get_by_customer(customer.id)
    assert len(treatments) == 2
    assert treatments[0].description == "טיפול ב"  # newest first


def test_update_treatment(ctrl, customer):
    t = ctrl.create(customer.id, datetime(2026, 3, 1), "ניקוי פנים", "", "")
    updated = ctrl.update(t.id, datetime(2026, 3, 2), "עיסוי", "דני", "נהדר")
    assert updated.description == "עיסוי"
    assert updated.performed_by == "דני"


def test_delete_treatment(ctrl, customer):
    t = ctrl.create(customer.id, datetime(2026, 3, 1), "ניקוי פנים", "", "")
    ctrl.delete(t.id)
    assert ctrl.get_by_id(t.id) is None


def test_delete_nonexistent_raises(ctrl):
    with pytest.raises(ValueError, match="לא נמצא"):
        ctrl.delete(9999)
