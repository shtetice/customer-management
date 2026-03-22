import pytest
from datetime import datetime
from controllers.receipt_controller import ReceiptController
from controllers.customer_controller import CustomerController
from controllers.treatment_controller import TreatmentController
from database.models import CustomerStatus


@pytest.fixture
def customer():
    return CustomerController().create("אנה", "לוי", None, "", "", "", "", CustomerStatus.CUSTOMER, "")


@pytest.fixture
def treatment(customer):
    return TreatmentController().create(customer.id, datetime(2026, 3, 1), "ניקוי פנים", "", "")


@pytest.fixture
def ctrl():
    return ReceiptController()


def test_create_receipt(ctrl, customer):
    r = ctrl.create(customer.id, datetime(2026, 3, 1), "₪250", "ניקוי פנים")
    assert r.id is not None
    assert r.amount == "₪250"


def test_create_receipt_linked_to_treatment(ctrl, customer, treatment):
    r = ctrl.create(customer.id, datetime(2026, 3, 1), "₪300", "", treatment.id)
    assert r.treatment_id == treatment.id


def test_create_receipt_missing_amount_raises(ctrl, customer):
    with pytest.raises(ValueError, match="סכום"):
        ctrl.create(customer.id, datetime(2026, 3, 1), "", "")


def test_get_by_customer(ctrl, customer):
    ctrl.create(customer.id, datetime(2026, 3, 1), "₪100", "")
    ctrl.create(customer.id, datetime(2026, 3, 2), "₪200", "")
    receipts = ctrl.get_by_customer(customer.id)
    assert len(receipts) == 2


def test_update_receipt(ctrl, customer):
    r = ctrl.create(customer.id, datetime(2026, 3, 1), "₪100", "")
    updated = ctrl.update(r.id, datetime(2026, 3, 2), "₪500", "עיסוי")
    assert updated.amount == "₪500"
    assert updated.description == "עיסוי"


def test_delete_receipt(ctrl, customer):
    r = ctrl.create(customer.id, datetime(2026, 3, 1), "₪100", "")
    ctrl.delete(r.id)
    assert ctrl.get_by_id(r.id) is None


def test_delete_nonexistent_raises(ctrl):
    with pytest.raises(ValueError, match="לא נמצאה"):
        ctrl.delete(9999)
