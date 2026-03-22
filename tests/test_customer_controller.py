import pytest
from controllers.customer_controller import CustomerController
from database.models import CustomerStatus, Gender


@pytest.fixture
def ctrl():
    return CustomerController()


def test_create_customer_success(ctrl):
    c = ctrl.create("יוסי", "כהן", Gender.MALE, "050-1234567", "yossi@test.com", CustomerStatus.LEAD, "")
    assert c.id is not None
    assert c.name == "יוסי"
    assert c.surname == "כהן"
    assert c.status == CustomerStatus.LEAD


def test_create_customer_missing_name_raises(ctrl):
    with pytest.raises(ValueError, match="שם"):
        ctrl.create("", "כהן", None, "", "", CustomerStatus.LEAD, "")


def test_create_customer_missing_surname_raises(ctrl):
    with pytest.raises(ValueError, match="שם משפחה"):
        ctrl.create("יוסי", "", None, "", "", CustomerStatus.LEAD, "")


def test_create_customer_invalid_email_raises(ctrl):
    with pytest.raises(ValueError, match="אימייל"):
        ctrl.create("יוסי", "כהן", None, "", "not-an-email", CustomerStatus.LEAD, "")


def test_get_all_returns_customers(ctrl):
    ctrl.create("אנה", "לוי", Gender.FEMALE, "", "", CustomerStatus.CUSTOMER, "")
    ctrl.create("דני", "מזרחי", Gender.MALE, "", "", CustomerStatus.VIP, "")
    all_customers = ctrl.get_all()
    assert len(all_customers) == 2


def test_get_all_filtered_by_status(ctrl):
    ctrl.create("אנה", "לוי", None, "", "", CustomerStatus.LEAD, "")
    ctrl.create("דני", "מזרחי", None, "", "", CustomerStatus.VIP, "")
    leads = ctrl.get_all(status=CustomerStatus.LEAD)
    assert len(leads) == 1
    assert leads[0].name == "אנה"


def test_search_by_name(ctrl):
    ctrl.create("אנה", "לוי", None, "", "", CustomerStatus.LEAD, "")
    ctrl.create("דני", "מזרחי", None, "", "", CustomerStatus.CUSTOMER, "")
    results = ctrl.search("אנה")
    assert len(results) == 1
    assert results[0].name == "אנה"


def test_search_by_phone(ctrl):
    ctrl.create("אנה", "לוי", None, "054-9999999", "", CustomerStatus.LEAD, "")
    results = ctrl.search("054-9999")
    assert len(results) == 1


def test_update_customer(ctrl):
    c = ctrl.create("אנה", "לוי", None, "", "", CustomerStatus.LEAD, "")
    updated = ctrl.update(c.id, "אנה", "לוי", None, "050-000", "", CustomerStatus.CUSTOMER, "הערה")
    assert updated.phone == "050-000"
    assert updated.status == CustomerStatus.CUSTOMER


def test_update_nonexistent_customer_raises(ctrl):
    with pytest.raises(ValueError, match="לא נמצא"):
        ctrl.update(9999, "א", "ב", None, "", "", CustomerStatus.LEAD, "")


def test_delete_customer(ctrl):
    c = ctrl.create("אנה", "לוי", None, "", "", CustomerStatus.LEAD, "")
    ctrl.delete(c.id)
    assert ctrl.get_by_id(c.id) is None


def test_delete_nonexistent_raises(ctrl):
    with pytest.raises(ValueError, match="לא נמצא"):
        ctrl.delete(9999)
