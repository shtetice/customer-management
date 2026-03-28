import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QSizePolicy, QMessageBox,
    QGraphicsOpacityEffect
)
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPainterPath

from ui.screens.customer_list_screen import CustomerListScreen
from ui.screens.add_customer_screen import AddCustomerScreen
from ui.screens.customer_detail_screen import CustomerDetailScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.user_management_screen import UserManagementScreen
from ui.screens.activity_log_screen import ActivityLogScreen
from ui.screens.calendar_screen import CalendarScreen
from ui.screens.marketing_screen import MarketingScreen
from ui.styles import APP_STYLE
from services.auth_service import auth_service
from services.settings_service import settings_service


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("מערכת ניהול לקוחות")
        self.setMinimumSize(1126, 748)
        self.resize(1126, 748)
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

        # Clock / date at top of sidebar
        clock_widget = QWidget()
        clock_widget.setStyleSheet("background: transparent; border: none;")
        clock_layout = QVBoxLayout(clock_widget)
        clock_layout.setContentsMargins(0, 10, 0, 6)
        clock_layout.setSpacing(2)

        self._clock_time_label = QLabel()
        self._clock_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clock_time_label.setStyleSheet(
            "color: #ecf0f1; font-size: 22px; font-weight: bold;"
            " background: transparent; border: none; letter-spacing: 1px;"
        )
        clock_layout.addWidget(self._clock_time_label)

        self._clock_date_label = QLabel()
        self._clock_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clock_date_label.setStyleSheet(
            "color: #95a5a6; font-size: 11px; background: transparent; border: none;"
        )
        clock_layout.addWidget(self._clock_date_label)

        sidebar_layout.addWidget(clock_widget)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # Nav buttons
        self._nav_buttons = {}
        self._add_nav_button(sidebar_layout, "customers", "👥  לקוחות", "customers.view")
        self._add_nav_button(sidebar_layout, "calendar", "📅  לוח תורים", "calendar.view")
        self._add_nav_button(sidebar_layout, "marketing", "📢  שיווק", "customers.view")
        self._add_nav_button(sidebar_layout, "users", "👤  משתמשים", "users.manage")
        self._add_nav_button(sidebar_layout, "logs", "📋  יומן פעילות", "logs.view")
        self._add_nav_button(sidebar_layout, "settings", "⚙️  הגדרות", "settings.view")
        sidebar_layout.addStretch()

        # Clinic logo at bottom of sidebar (50% opacity)
        logo_path = settings_service.get("clinic_logo_path", "")
        if logo_path and os.path.isfile(logo_path):
            logo_label = QLabel()
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            size = 140
            src = QPixmap(logo_path).scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            if not src.isNull():
                bg_color = src.toImage().pixelColor(0, 0)
                circle = QPixmap(size, size)
                circle.fill(Qt.GlobalColor.transparent)
                painter = QPainter(circle)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, size, size)
                painter.setClipPath(path)
                painter.fillPath(path, bg_color)
                x_off = (size - src.width()) // 2
                y_off = (size - src.height()) // 2
                painter.drawPixmap(x_off, y_off, src)
                painter.end()
                logo_label.setPixmap(circle)
                logo_label.setStyleSheet("background: transparent; border: none; padding: 8px 0;")
                opacity = QGraphicsOpacityEffect()
                opacity.setOpacity(0.5)
                logo_label.setGraphicsEffect(opacity)
                sidebar_layout.addWidget(logo_label)

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
        elif key == "calendar":
            self._show_calendar()
        elif key == "marketing":
            self._show_marketing([])
        elif key == "users":
            self._show_user_management()
        elif key == "logs":
            self._show_activity_log()
        elif key == "settings":
            self._show_settings()

    def _show_customer_list(self):
        self._clear_stack()
        screen = CustomerListScreen()
        screen.request_add_customer.connect(self._show_add_customer)
        screen.request_edit_customer.connect(self._show_edit_customer)
        screen.request_view_customer.connect(self._show_customer_detail)
        screen.request_campaign.connect(self._show_marketing)
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
        screen.edit_requested.connect(self._show_edit_customer)
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)

    def _show_edit_customer(self, customer_id: int):
        self._clear_stack()
        screen = AddCustomerScreen(customer_id=customer_id)
        screen.customer_saved.connect(lambda: self._show_customer_detail(customer_id))
        screen.cancelled.connect(lambda: self._show_customer_detail(customer_id))
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)

    def _show_calendar(self):
        self._clear_stack()
        screen = CalendarScreen()
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)
        self._set_nav_active("calendar")

    def _show_marketing(self, customers: list):
        self._clear_stack()
        screen = MarketingScreen(customers)
        screen.back_requested.connect(self._show_customer_list)
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)
        self._set_nav_active("marketing")

    def _show_user_management(self):
        self._clear_stack()
        screen = UserManagementScreen()
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)
        self._set_nav_active("users")

    def _show_activity_log(self):
        self._clear_stack()
        screen = ActivityLogScreen()
        self.stack.addWidget(screen)
        self.stack.setCurrentWidget(screen)
        self._set_nav_active("logs")

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

    def closeEvent(self, event):
        self._run_autobackup()
        event.accept()
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()

    def _run_autobackup(self):
        backup_folder = settings_service.get("backup_folder", "")
        backup_password = settings_service.get_secret("backup_password")
        if not backup_folder or not backup_password:
            return

        # Skip backup if nothing has changed since the last one
        from services.activity_service import has_activity_since
        from datetime import datetime
        last_backup_str = settings_service.get("last_backup_time", "")
        if last_backup_str:
            try:
                last_backup_dt = datetime.fromisoformat(last_backup_str)
                if not has_activity_since(last_backup_dt):
                    return
            except ValueError:
                pass  # malformed timestamp — proceed with backup

        try:
            from services.backup_service import run_backup
            run_backup(backup_folder, backup_password)
            settings_service.set("last_backup_time", datetime.utcnow().isoformat())
        except Exception as e:
            QMessageBox.warning(
                self, "שגיאת גיבוי",
                f"הגיבוי האוטומטי נכשל:\n{e}"
            )

    _HEB_DAYS = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]

    def _update_clock(self):
        now = datetime.now()
        self._clock_time_label.setText(now.strftime("%H:%M:%S"))
        day_name = f"יום {self._HEB_DAYS[now.weekday()]}"
        self._clock_date_label.setText(f"{day_name}, {now.strftime('%d.%m.%Y')}")

    def _logout(self):
        from services.session_service import session_service
        session_service.clear()
        auth_service.logout()
        self.close()
