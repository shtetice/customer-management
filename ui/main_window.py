from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.screens.customer_list_screen import CustomerListScreen
from ui.screens.add_customer_screen import AddCustomerScreen
from ui.screens.customer_detail_screen import CustomerDetailScreen
from ui.screens.settings_screen import SettingsScreen
from ui.styles import APP_STYLE
from services.auth_service import auth_service


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("מערכת ניהול לקוחות")
        self.setMinimumSize(1024, 680)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        app_title = QLabel("ניהול לקוחות")
        app_title.setObjectName("app_title")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(app_title)

        # Nav buttons
        self._nav_buttons = {}
        self._add_nav_button(sidebar_layout, "customers", "👥  לקוחות", "customers.view")
        self._add_nav_button(sidebar_layout, "settings", "⚙️  הגדרות", "settings.view")
        sidebar_layout.addStretch()

        # User info + logout at bottom
        user_label = QLabel(f"משתמש: {auth_service.current_user.username}")
        user_label.setStyleSheet("color: #bdc3c7; padding: 8px 16px; font-size: 12px;")
        sidebar_layout.addWidget(user_label)

        btn_logout = QPushButton("התנתק")
        btn_logout.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e74c3c;
                border: none;
                padding: 10px 16px;
                text-align: right;
            }
            QPushButton:hover { background: #2c3e50; }
        """)
        btn_logout.clicked.connect(self._logout)
        sidebar_layout.addWidget(btn_logout)

        root_layout.addWidget(sidebar)

        # Main content (stacked)
        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")
        root_layout.addWidget(self.stack, stretch=1)

        self._show_customer_list()

    def _add_nav_button(self, layout, key: str, label: str, permission_key: str):
        if not auth_service.has_permission(permission_key):
            return
        btn = QPushButton(label)
        btn.setProperty("active", "false")
        btn.clicked.connect(lambda: self._navigate(key))
        layout.addWidget(btn)
        self._nav_buttons[key] = btn

    def _navigate(self, key: str):
        # Update active state on buttons
        for k, btn in self._nav_buttons.items():
            btn.setProperty("active", "true" if k == key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if key == "customers":
            self._show_customer_list()
        elif key == "settings":
            self._show_settings()

    def _show_customer_list(self):
        self._clear_stack()
        screen = CustomerListScreen()
        screen.request_add_customer.connect(self._show_add_customer)
        screen.request_edit_customer.connect(self._show_edit_customer)
        screen.request_view_customer.connect(self._show_customer_detail)
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)
        self._set_nav_active("customers")

    def _show_add_customer(self):
        self._clear_stack()
        screen = AddCustomerScreen()
        screen.customer_saved.connect(self._show_customer_list)
        screen.cancelled.connect(self._show_customer_list)
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)

    def _show_customer_detail(self, customer_id: int):
        self._clear_stack()
        screen = CustomerDetailScreen(customer_id)
        screen.back_requested.connect(self._show_customer_list)
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)

    def _show_edit_customer(self, customer_id: int):
        self._clear_stack()
        screen = AddCustomerScreen(customer_id=customer_id)
        screen.customer_saved.connect(self._show_customer_list)
        screen.cancelled.connect(self._show_customer_list)
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)

    def _show_settings(self):
        self._clear_stack()
        screen = SettingsScreen()
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)
        self._set_nav_active("settings")

    def _clear_stack(self):
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

    def _set_nav_active(self, key: str):
        for k, btn in self._nav_buttons.items():
            btn.setProperty("active", "true" if k == key else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _logout(self):
        from services.session_service import session_service
        session_service.clear()
        auth_service.logout()
        self.close()
