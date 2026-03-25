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


def open_main_window():
    window = MainWindow()
    window.showMaximized()
    return window


def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyleSheet(APP_STYLE)

    init_db()
    auth_service.ensure_default_manager()

    main_window: MainWindow | None = None

    # Try to restore a remembered session
    saved = session_service.load()
    if saved:
        db = get_session()
        try:
            user = db.query(User).filter_by(id=saved["user_id"], is_active=True).first()
            if user:
                db.expunge(user)
                auth_service._current_user = user
                main_window = open_main_window()
                sys.exit(app.exec())
        finally:
            db.close()

    # No valid session — show login screen
    login = LoginScreen()
    login.setFixedSize(480, 430)
    login.setWindowTitle("התחברות - מערכת ניהול לקוחות")

    def on_login():
        nonlocal main_window
        login.close()
        main_window = open_main_window()

    login.login_successful.connect(on_login)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
