import pytest
from datetime import date
from controllers.customer_controller import CustomerController
from database.models import CustomerStatus, Gender


@pytest.fixture
def ctrl():
    return CustomerController()


def _create(ctrl, name="יוסי", surname="כהן", gender=Gender.MALE,
            phone="050-1234567", phone2="", phone3="",
            email="yossi@test.com", status=CustomerStatus.LEAD, notes=""):
    return ctrl.create(name, surname, gender, phone, phone2, phone3, email, status, notes)


def test_create_customer_success(ctrl):
    c = _create(ctrl)
    assert c.id is not None
    assert c.name == "יוסי"
    assert c.surname == "כהן"
    assert c.status == CustomerStatus.LEAD


def test_create_customer_multiple_phones(ctrl):
    c = ctrl.create("אנה", "לוי", None, "050-1111111", "052-2222222", "054-3333333",
                    "", CustomerStatus.LEAD, "")
    assert c.phone == "050-1111111"
    assert c.phone2 == "052-2222222"
    assert c.phone3 == "054-3333333"


def test_create_customer_missing_name_raises(ctrl):
    with pytest.raises(ValueError, match="שם"):
        ctrl.create("", "כהן", None, "", "", "", "", CustomerStatus.LEAD, "")


def test_create_customer_missing_surname_raises(ctrl):
    with pytest.raises(ValueError, match="שם משפחה"):
        ctrl.create("יוסי", "", None, "", "", "", "", CustomerStatus.LEAD, "")


def test_create_customer_invalid_email_raises(ctrl):
    with pytest.raises(ValueError, match="אימייל"):
        ctrl.create("יוסי", "כהן", None, "", "", "", "not-an-email", CustomerStatus.LEAD, "")


def test_get_all_returns_customers(ctrl):
    _create(ctrl, name="אנה", surname="לוי", gender=Gender.FEMALE, status=CustomerStatus.CUSTOMER)
    _create(ctrl, name="דני", surname="מזרחי", gender=Gender.MALE, status=CustomerStatus.VIP)
    assert len(ctrl.get_all()) == 2


def test_get_all_filtered_by_status(ctrl):
    _create(ctrl, name="אנה", surname="לוי", status=CustomerStatus.LEAD)
    _create(ctrl, name="דני", surname="מזרחי", status=CustomerStatus.VIP)
    leads = ctrl.get_all(status=CustomerStatus.LEAD)
    assert len(leads) == 1
    assert leads[0].name == "אנה"


def test_search_by_name(ctrl):
    _create(ctrl, name="אנה", surname="לוי", status=CustomerStatus.LEAD)
    _create(ctrl, name="דני", surname="מזרחי", status=CustomerStatus.CUSTOMER)
    results = ctrl.search("אנה")
    assert len(results) == 1
    assert results[0].name == "אנה"


def test_search_by_phone(ctrl):
    ctrl.create("אנה", "לוי", None, "054-9999999", "", "", "", CustomerStatus.LEAD, "")
    assert len(ctrl.search("054-9999")) == 1


def test_search_by_phone2(ctrl):
    ctrl.create("אנה", "לוי", None, "050-1111111", "052-8888888", "", "", CustomerStatus.LEAD, "")
    assert len(ctrl.search("052-8888")) == 1


def test_update_customer(ctrl):
    c = _create(ctrl, name="אנה", surname="לוי", status=CustomerStatus.LEAD)
    updated = ctrl.update(c.id, "אנה", "לוי", None, "050-000", "052-111", "",
                          "", CustomerStatus.CUSTOMER, "הערה")
    assert updated.phone == "050-000"
    assert updated.phone2 == "052-111"
    assert updated.status == CustomerStatus.CUSTOMER


def test_update_nonexistent_customer_raises(ctrl):
    with pytest.raises(ValueError, match="לא נמצא"):
        ctrl.update(9999, "א", "ב", None, "", "", "", "", CustomerStatus.LEAD, "")


def test_delete_customer(ctrl):
    c = _create(ctrl)
    ctrl.delete(c.id)
    assert ctrl.get_by_id(c.id) is None


def test_delete_nonexistent_raises(ctrl):
    with pytest.raises(ValueError, match="לא נמצא"):
        ctrl.delete(9999)


def test_create_with_address_and_dob(ctrl):
    dob = date(1990, 5, 15)
    c = ctrl.create("רחל", "כץ", Gender.FEMALE, "050-1234567", "", "",
                    "", CustomerStatus.LEAD, "", address="רחוב הרצל 1, תל אביב", date_of_birth=dob)
    assert c.address == "רחוב הרצל 1, תל אביב"
    assert c.date_of_birth == dob


def test_create_without_address_and_dob(ctrl):
    c = _create(ctrl)
    assert c.address is None
    assert c.date_of_birth is None


def test_update_sets_address_and_dob(ctrl):
    c = _create(ctrl)
    dob = date(1985, 3, 20)
    updated = ctrl.update(c.id, c.name, c.surname, None, "", "", "",
                          "", CustomerStatus.LEAD, "", address="שדרות בן גוריון 5", date_of_birth=dob)
    assert updated.address == "שדרות בן גוריון 5"
    assert updated.date_of_birth == dob


def test_update_clears_dob(ctrl):
    dob = date(1990, 1, 1)
    c = ctrl.create("משה", "לוי", None, "", "", "", "", CustomerStatus.LEAD, "",
                    date_of_birth=dob)
    updated = ctrl.update(c.id, c.name, c.surname, None, "", "", "",
                          "", CustomerStatus.LEAD, "", date_of_birth=None)
    assert updated.date_of_birth is None
