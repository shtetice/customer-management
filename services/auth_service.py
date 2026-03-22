import bcrypt
from sqlalchemy.orm import Session
from database.models import User, UserRole, UserPermission, Feature
from database.db import get_session


class AuthService:
    def __init__(self):
        self._current_user: User | None = None

    # ---------- Authentication ----------

    def login(self, username: str, password: str) -> bool:
        """Verify credentials. Returns True on success."""
        if not username or not password:
            return False
        session = get_session()
        try:
            user = session.query(User).filter_by(username=username, is_active=True).first()
            if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                # Detach from session so we can use it freely
                session.expunge(user)
                self._current_user = user
                return True
            return False
        finally:
            session.close()

    def logout(self):
        self._current_user = None

    @property
    def current_user(self) -> User | None:
        return self._current_user

    @property
    def is_logged_in(self) -> bool:
        return self._current_user is not None

    @property
    def is_manager(self) -> bool:
        return self._current_user is not None and self._current_user.role == UserRole.MANAGER

    # ---------- Permission check ----------

    def has_permission(self, feature_key: str) -> bool:
        """Managers have all permissions. Users are checked against UserPermission table."""
        if not self._current_user:
            return False
        if self.is_manager:
            return True
        session = get_session()
        try:
            feature = session.query(Feature).filter_by(key=feature_key).first()
            if not feature:
                return False
            perm = session.query(UserPermission).filter_by(
                user_id=self._current_user.id,
                feature_id=feature.id
            ).first()
            return perm.allowed if perm else False
        finally:
            session.close()

    # ---------- User management (manager only) ----------

    def create_user(self, username: str, password: str, full_name: str, role: UserRole) -> User:
        if not username or not password:
            raise ValueError("שם משתמש וסיסמה הם שדות חובה")
        session = get_session()
        try:
            existing = session.query(User).filter_by(username=username).first()
            if existing:
                raise ValueError(f"שם המשתמש '{username}' כבר קיים במערכת")
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user = User(username=username, password_hash=hashed, full_name=full_name, role=role)
            session.add(user)
            session.commit()
            session.refresh(user)
            session.expunge(user)
            return user
        finally:
            session.close()

    def set_permission(self, user_id: int, feature_key: str, allowed: bool):
        session = get_session()
        try:
            feature = session.query(Feature).filter_by(key=feature_key).first()
            if not feature:
                raise ValueError(f"תכונה לא קיימת: {feature_key}")
            perm = session.query(UserPermission).filter_by(
                user_id=user_id, feature_id=feature.id
            ).first()
            if perm:
                perm.allowed = allowed
            else:
                session.add(UserPermission(user_id=user_id, feature_id=feature.id, allowed=allowed))
            session.commit()
        finally:
            session.close()

    def ensure_default_manager(self):
        """Create a default manager account if no users exist."""
        session = get_session()
        try:
            if session.query(User).count() == 0:
                self.create_user(
                    username="admin",
                    password="admin123",
                    full_name="מנהל ראשי",
                    role=UserRole.MANAGER
                )
        finally:
            session.close()


# Singleton used across the app
auth_service = AuthService()
