import sys
from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtCore import Qt

from database.db import init_db, get_session
from database.models import User
from services.auth_service import auth_service
from services.session_service import session_service
from ui.screens.login_screen import LoginScreen
from ui.main_window import MainWindow
from ui.styles import APP_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyleSheet(APP_STYLE)
    app.setQuitOnLastWindowClosed(False)
    init_db()
    auth_service.ensure_default_manager()
    from services.activity_service import purge_old_logs
    purge_old_logs()

    main_window: MainWindow | None = None

    def show_login():
        login = LoginScreen()
        login.setFixedSize(480, 430)
        login.setWindowTitle("התחברות - מערכת ניהול לקוחות")
        login.login_successful.connect(lambda: on_login(login))
        login.show()

    def on_login(login: LoginScreen):
        nonlocal main_window
        login.close()
        main_window = MainWindow()
        main_window.show()

    # Try to restore a remembered session
    saved = session_service.load()
    if saved:
        db = get_session()
        try:
            user = db.query(User).filter_by(id=saved["user_id"], is_active=True).first()
            if user:
                db.expunge(user)
                auth_service._current_user = user
                main_window = MainWindow()
                main_window.show()
                sys.exit(app.exec())
        except Exception:
            pass
        finally:
            db.close()

    # No valid session — show login screen
    show_login()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
