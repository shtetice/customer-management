import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QFileDialog, QMessageBox, QDialog, QDialogButtonBox,
    QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

from services.settings_service import settings_service
from services.auth_service import auth_service

_APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGO_DIR = os.path.join(_APP_ROOT, "uploads", "logo")


class SettingsScreen(QWidget):

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        # Outer layout holds just the scroll area
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        # Inner container is the actual settings content
        container = QWidget()
        container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(24)

        title = QLabel("הגדרות")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # ── Section: receipts ──────────────────────────────────
        section = self._section("שמירת קבלות")
        layout.addWidget(section)
        sec_layout = section.layout()

        # Folder path row
        row = QHBoxLayout()
        row.setSpacing(8)

        self._folder_input = QLineEdit()
        self._folder_input.setPlaceholderText("בחר תיקיית שמירה...")
        self._folder_input.setMinimumHeight(36)
        self._folder_input.setReadOnly(True)
        self._folder_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc; border-radius: 5px;
                padding: 7px 10px; font-size: 13px;
                background: #fafafa; color: #2c3e50;
            }
        """)
        saved = settings_service.get("receipts_folder", "")
        if saved:
            self._folder_input.setText(saved)
        row.addWidget(self._folder_input, stretch=1)

        btn_browse = QPushButton("בחר תיקייה")
        btn_browse.setFixedHeight(36)
        btn_browse.setMinimumWidth(110)
        btn_browse.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #2980b9; }
        """)
        btn_browse.clicked.connect(self._browse)
        row.addWidget(btn_browse)

        sec_layout.addLayout(row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
        sec_layout.addWidget(self._status_label)

        # ── Section: clinic logo ───────────────────────────────
        logo_section = self._section("לוגו קליניקה לקבלות")
        layout.addWidget(logo_section)
        logo_layout = logo_section.layout()

        logo_note = QLabel("הלוגו יופיע בפינה השמאלית-עליונה של כל קבלה שתופק.")
        logo_note.setStyleSheet("color: #666; font-size: 12px; border: none; background: transparent;")
        logo_note.setWordWrap(True)
        logo_layout.addWidget(logo_note)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(8)

        # Preview box — fixed size, right side in RTL
        self._logo_preview = QLabel()
        self._logo_preview.setFixedSize(120, 44)
        self._logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_preview.setStyleSheet(
            "border: 1px dashed #bbb; border-radius: 4px; background: #fafafa;"
        )
        self._logo_preview.setText("אין לוגו")
        logo_row.addWidget(self._logo_preview)

        logo_row.addStretch()

        btn_pick_logo = QPushButton("בחר תמונה")
        btn_pick_logo.setFixedHeight(34)
        btn_pick_logo.setMinimumWidth(110)
        btn_pick_logo.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #2980b9; }
        """)
        btn_pick_logo.clicked.connect(self._pick_logo)
        logo_row.addWidget(btn_pick_logo)

        self._btn_clear_logo = QPushButton("הסר לוגו")
        self._btn_clear_logo.setFixedHeight(34)
        self._btn_clear_logo.setMinimumWidth(110)
        self._btn_clear_logo.setStyleSheet("""
            QPushButton { background: #fdf2f2; color: #e74c3c;
                          border: 1px solid #f5c6c6; border-radius: 5px;
                          font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #fce8e8; border-color: #e74c3c; }
        """)
        self._btn_clear_logo.clicked.connect(self._clear_logo)
        logo_row.addWidget(self._btn_clear_logo)

        logo_layout.addLayout(logo_row)

        self._logo_status_label = QLabel("")
        self._logo_status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
        logo_layout.addWidget(self._logo_status_label)

        # Load existing logo preview
        self._refresh_logo_preview()

        # ── Section: autobackup ────────────────────────────────
        backup_section = self._section("גיבוי אוטומטי")
        layout.addWidget(backup_section)
        backup_layout = backup_section.layout()

        backup_note = QLabel("גיבוי מאובטח בסיסמה יוצר אוטומטית בכל סגירת האפליקציה.")
        backup_note.setStyleSheet("color: #666; font-size: 12px; border: none; background: transparent;")
        backup_layout.addWidget(backup_note)

        # Backup folder row
        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)

        self._backup_folder_input = QLineEdit()
        self._backup_folder_input.setPlaceholderText("בחר תיקיית גיבוי...")
        self._backup_folder_input.setMinimumHeight(36)
        self._backup_folder_input.setReadOnly(True)
        self._backup_folder_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc; border-radius: 5px;
                padding: 7px 10px; font-size: 13px;
                background: #fafafa; color: #2c3e50;
            }
        """)
        saved_backup_folder = settings_service.get("backup_folder", "")
        if saved_backup_folder:
            self._backup_folder_input.setText(saved_backup_folder)
        folder_row.addWidget(self._backup_folder_input, stretch=1)

        btn_browse_backup = QPushButton("בחר תיקייה")
        btn_browse_backup.setFixedHeight(36)
        btn_browse_backup.setMinimumWidth(110)
        btn_browse_backup.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #2980b9; }
        """)
        btn_browse_backup.clicked.connect(self._browse_backup)
        folder_row.addWidget(btn_browse_backup)
        backup_layout.addLayout(folder_row)

        # Password row
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(8)

        pwd_label = QLabel("סיסמת גיבוי:")
        pwd_label.setStyleSheet("color: #2c3e50; font-size: 13px; border: none; background: transparent;")
        pwd_label.setFixedWidth(90)
        pwd_row.addWidget(pwd_label)

        self._backup_password_input = QLineEdit()
        self._backup_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._backup_password_input.setPlaceholderText("הקלד סיסמה לקובץ הגיבוי...")
        self._backup_password_input.setMinimumHeight(36)
        self._backup_password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc; border-radius: 5px;
                padding: 7px 10px; font-size: 13px;
                background: #fafafa; color: #2c3e50;
            }
        """)
        saved_backup_pwd = settings_service.get_secret("backup_password")
        if saved_backup_pwd:
            self._backup_password_input.setText(saved_backup_pwd)
        pwd_row.addWidget(self._backup_password_input, stretch=1)

        btn_save_pwd = QPushButton("שמור סיסמה")
        btn_save_pwd.setFixedHeight(36)
        btn_save_pwd.setMinimumWidth(110)
        btn_save_pwd.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #2980b9; }
        """)
        btn_save_pwd.clicked.connect(self._save_backup_password)
        pwd_row.addWidget(btn_save_pwd)

        btn_show_pwd = QPushButton("הצג סיסמה")
        btn_show_pwd.setFixedHeight(36)
        btn_show_pwd.setMinimumWidth(110)
        btn_show_pwd.setStyleSheet("""
            QPushButton { background: #7f8c8d; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #636e72; }
        """)
        btn_show_pwd.clicked.connect(self._reveal_backup_password)
        pwd_row.addWidget(btn_show_pwd)
        backup_layout.addLayout(pwd_row)

        self._backup_status_label = QLabel("")
        self._backup_status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
        backup_layout.addWidget(self._backup_status_label)

        # ── Section: logs ──────────────────────────────────────
        logs_section = self._section("יומן פעילות")
        layout.addWidget(logs_section)
        logs_layout = logs_section.layout()

        retention_row = QHBoxLayout()
        retention_row.setSpacing(8)

        retention_label = QLabel("שמור רשומות יומן למשך:")
        retention_label.setStyleSheet("color: #2c3e50; font-size: 13px; border: none; background: transparent;")
        retention_row.addWidget(retention_label)

        self._retention_input = QLineEdit()
        self._retention_input.setFixedWidth(70)
        self._retention_input.setMinimumHeight(36)
        self._retention_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc; border-radius: 5px;
                padding: 7px 10px; font-size: 13px;
                background: #fafafa; color: #2c3e50;
            }
        """)
        self._retention_input.setText(str(settings_service.get("log_retention_days", 90)))
        retention_row.addWidget(self._retention_input)

        retention_row.addWidget(QLabel("ימים"))
        retention_row.addStretch()

        btn_save_retention = QPushButton("שמור")
        btn_save_retention.setFixedHeight(36)
        btn_save_retention.setMinimumWidth(80)
        btn_save_retention.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #2980b9; }
        """)
        btn_save_retention.clicked.connect(self._save_retention)
        retention_row.addWidget(btn_save_retention)
        logs_layout.addLayout(retention_row)

        self._logs_status_label = QLabel("")
        self._logs_status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
        logs_layout.addWidget(self._logs_status_label)

        layout.addStretch()

    def _pick_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "בחר תמונת לוגו", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not path:
            return
        os.makedirs(_LOGO_DIR, exist_ok=True)
        ext = os.path.splitext(path)[1].lower()
        dest = os.path.join(_LOGO_DIR, f"clinic_logo{ext}")
        shutil.copy2(path, dest)
        settings_service.set("clinic_logo_path", dest)
        self._refresh_logo_preview()
        self._logo_status_label.setText("הלוגו נשמר בהצלחה")

    def _clear_logo(self):
        settings_service.set("clinic_logo_path", "")
        self._logo_status_label.setText("הלוגו הוסר")
        self._refresh_logo_preview()

    def _refresh_logo_preview(self):
        logo_path = settings_service.get("clinic_logo_path", "")
        if logo_path and os.path.isfile(logo_path):
            px = QPixmap(logo_path).scaled(
                120, 44,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._logo_preview.setPixmap(px)
            self._logo_preview.setText("")
        else:
            self._logo_preview.setPixmap(QPixmap())
            self._logo_preview.setText("אין לוגו")

    def _section(self, title: str) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        lbl = QLabel(title)
        lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #2c3e50; border: none; background: transparent;")
        layout.addWidget(lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #eee; border: none; background: #eee;")
        line.setFixedHeight(1)
        layout.addWidget(line)

        return widget

    def _browse(self):
        current = self._folder_input.text() or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self, "בחר תיקיית שמירה", current)
        if folder:
            settings_service.set("receipts_folder", folder)
            self._folder_input.setText(folder)
            self._status_label.setText("נשמר בהצלחה")

    def _browse_backup(self):
        current = self._backup_folder_input.text() or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self, "בחר תיקיית גיבוי", current)
        if folder:
            settings_service.set("backup_folder", folder)
            self._backup_folder_input.setText(folder)
            self._backup_status_label.setText("תיקיית הגיבוי נשמרה")

    def _save_retention(self):
        val = self._retention_input.text().strip()
        if not val.isdigit() or int(val) < 1:
            QMessageBox.warning(self, "שגיאה", "יש להזין מספר ימים חיובי")
            return
        settings_service.set("log_retention_days", int(val))
        self._logs_status_label.setText("נשמר בהצלחה")

    def _save_backup_password(self):
        pwd = self._backup_password_input.text()
        if not pwd:
            QMessageBox.warning(self, "שגיאה", "יש להקליד סיסמה")
            return
        settings_service.set_secret("backup_password", pwd)
        self._backup_status_label.setText("הסיסמה נשמרה")

    def _reveal_backup_password(self):
        backup_pwd = settings_service.get_secret("backup_password")
        if not backup_pwd:
            QMessageBox.information(self, "סיסמת גיבוי", "לא הוגדרה סיסמת גיבוי עדיין.")
            return

        dlg = _ConfirmPasswordDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        entered = dlg.password()
        user = auth_service.current_user
        if not user or not auth_service.login(user.username, entered):
            QMessageBox.warning(self, "שגיאה", "הסיסמה שהוזנה שגויה.")
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("סיסמת גיבוי")
        msg.setText(f"סיסמת קובץ הגיבוי היא:\n\n<b>{backup_pwd}</b>")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()


class _ConfirmPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("אימות זהות")
        self.setFixedWidth(340)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("הזן את סיסמת הכניסה שלך כדי לצפות בסיסמת הגיבוי:")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self._pwd_input = QLineEdit()
        self._pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._pwd_input.setPlaceholderText("סיסמת כניסה...")
        self._pwd_input.setMinimumHeight(36)
        layout.addWidget(self._pwd_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def password(self) -> str:
        return self._pwd_input.text()
