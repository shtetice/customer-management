from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from services.auth_service import auth_service


class LoginScreen(QWidget):
    login_successful = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QWidget()
        card.setFixedWidth(360)
        card.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("מערכת ניהול לקוחות")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        subtitle = QLabel("התחבר למערכת")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        input_style = """
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: #ffffff;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """

        layout.addWidget(QLabel("שם משתמש"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("הכנס שם משתמש")
        self.username_input.setMinimumHeight(38)
        self.username_input.setStyleSheet(input_style)
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("סיסמה"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("הכנס סיסמה")
        self.password_input.setMinimumHeight(38)
        self.password_input.setStyleSheet(input_style)
        self.password_input.returnPressed.connect(self._on_login)
        layout.addWidget(self.password_input)

        layout.addSpacing(8)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

        btn_login = QPushButton("התחבר")
        btn_login.setFixedHeight(40)
        btn_login.clicked.connect(self._on_login)
        layout.addWidget(btn_login)

        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.error_label.setText("אנא מלא שם משתמש וסיסמה")
            return

        if auth_service.login(username, password):
            self.error_label.setText("")
            self.login_successful.emit()
        else:
            self.error_label.setText("שם משתמש או סיסמה שגויים")
            self.password_input.clear()
            self.password_input.setFocus()
