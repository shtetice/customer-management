import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from database.db import init_db
from services.auth_service import auth_service
from ui.screens.login_screen import LoginScreen
from ui.main_window import MainWindow
from ui.styles import APP_STYLE


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyleSheet(APP_STYLE)

    # Initialise DB and seed default data
    init_db()
    auth_service.ensure_default_manager()

    # Show login, then main window on success
    login = LoginScreen()
    login.setFixedSize(480, 400)
    login.setWindowTitle("התחברות - מערכת ניהול לקוחות")

    main_window: MainWindow | None = None

    def on_login():
        nonlocal main_window
        login.close()
        main_window = MainWindow()
        main_window.show()

    login.login_successful.connect(on_login)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
