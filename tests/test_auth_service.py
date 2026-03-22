import pytest
from services.auth_service import AuthService
from database.models import UserRole


@pytest.fixture
def auth():
    svc = AuthService()
    svc.ensure_default_manager()
    return svc


def test_default_manager_created(auth):
    assert auth.login("admin", "admin123")
    assert auth.is_logged_in
    assert auth.is_manager


def test_login_wrong_password_fails(auth):
    assert not auth.login("admin", "wrongpassword")
    assert not auth.is_logged_in


def test_login_unknown_user_fails(auth):
    assert not auth.login("nobody", "pass")


def test_logout(auth):
    auth.login("admin", "admin123")
    auth.logout()
    assert not auth.is_logged_in
    assert auth.current_user is None


def test_manager_has_all_permissions(auth):
    auth.login("admin", "admin123")
    assert auth.has_permission("customers.view")
    assert auth.has_permission("customers.delete")
    assert auth.has_permission("users.manage")


def test_create_user_and_set_permission(auth):
    auth.login("admin", "admin123")
    user = auth.create_user("staff1", "pass123", "עובד ראשון", UserRole.USER)
    assert user.id is not None

    # Grant permission
    auth.set_permission(user.id, "customers.view", True)

    # Login as new user and check permission
    user_auth = AuthService()
    assert user_auth.login("staff1", "pass123")
    assert user_auth.has_permission("customers.view")
    assert not user_auth.has_permission("customers.delete")


def test_create_duplicate_user_raises(auth):
    auth.login("admin", "admin123")
    auth.create_user("user2", "pass", "משתמש", UserRole.USER)
    with pytest.raises(ValueError, match="כבר קיים"):
        auth.create_user("user2", "pass", "משתמש", UserRole.USER)


def test_unauthenticated_has_no_permissions(auth):
    assert not auth.has_permission("customers.view")
