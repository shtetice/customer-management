import os
import shutil
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QFileDialog, QMessageBox, QDialog, QDialogButtonBox,
    QScrollArea, QComboBox, QSpinBox, QTextEdit
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

        # ── Section: WhatsApp / Twilio ─────────────────────────
        wa_section = self._section("הודעות WhatsApp (Twilio)")
        layout.addWidget(wa_section)
        wa_layout = wa_section.layout()

        wa_note = QLabel(
            "הזן את פרטי חשבון Twilio שלך. ההודעות יישלחו מהמספר whatsapp:+12604002399.\n"
            "בסביבת Sandbox יש להצטרף לסביבת הבדיקה לפני קבלת הודעות."
        )
        wa_note.setStyleSheet("color: #666; font-size: 12px; border: none; background: transparent;")
        wa_note.setWordWrap(True)
        wa_layout.addWidget(wa_note)

        field_style = """
            QLineEdit {
                border: 1px solid #ccc; border-radius: 5px;
                padding: 7px 10px; font-size: 13px;
                background: #fafafa; color: #2c3e50;
            }
            QLineEdit:focus { border-color: #3498db; }
        """

        from_row = QHBoxLayout()
        from_row.setSpacing(8)
        from_lbl = QLabel("מספר שולח:")
        from_lbl.setFixedWidth(110)
        from_lbl.setStyleSheet("color: #2c3e50; font-size: 13px; border: none; background: transparent;")
        from_row.addWidget(from_lbl)
        self._from_input = QLineEdit()
        self._from_input.setMinimumHeight(36)
        self._from_input.setStyleSheet(field_style)
        self._from_input.setPlaceholderText("+14155238886")
        self._from_input.setText(settings_service.get("twilio_from_number", ""))
        from_row.addWidget(self._from_input)
        wa_layout.addLayout(from_row)

        sid_row = QHBoxLayout()
        sid_row.setSpacing(8)
        sid_lbl = QLabel("Account SID:")
        sid_lbl.setFixedWidth(110)
        sid_lbl.setStyleSheet("color: #2c3e50; font-size: 13px; border: none; background: transparent;")
        sid_row.addWidget(sid_lbl)
        self._sid_input = QLineEdit()
        self._sid_input.setMinimumHeight(36)
        self._sid_input.setStyleSheet(field_style)
        self._sid_input.setPlaceholderText("ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self._sid_input.setText(settings_service.get_secret("twilio_account_sid"))
        sid_row.addWidget(self._sid_input)
        wa_layout.addLayout(sid_row)

        token_row = QHBoxLayout()
        token_row.setSpacing(8)
        token_lbl = QLabel("Auth Token:")
        token_lbl.setFixedWidth(110)
        token_lbl.setStyleSheet("color: #2c3e50; font-size: 13px; border: none; background: transparent;")
        token_row.addWidget(token_lbl)
        self._token_input = QLineEdit()
        self._token_input.setMinimumHeight(36)
        self._token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._token_input.setStyleSheet(field_style)
        self._token_input.setPlaceholderText("Auth Token")
        self._token_input.setText(settings_service.get_secret("twilio_auth_token"))
        token_row.addWidget(self._token_input)
        wa_layout.addLayout(token_row)

        test_row = QHBoxLayout()
        test_row.setSpacing(8)
        test_lbl = QLabel("טלפון לבדיקה:")
        test_lbl.setFixedWidth(110)
        test_lbl.setStyleSheet("color: #2c3e50; font-size: 13px; border: none; background: transparent;")
        test_row.addWidget(test_lbl)
        self._test_phone_input = QLineEdit()
        self._test_phone_input.setMinimumHeight(36)
        self._test_phone_input.setStyleSheet(field_style)
        self._test_phone_input.setPlaceholderText("+972501234567")
        test_row.addWidget(self._test_phone_input)
        wa_layout.addLayout(test_row)

        btn_row_wa = QHBoxLayout()
        btn_row_wa.addStretch()
        btn_save_wa = QPushButton("שמור פרטי Twilio")
        btn_save_wa.setFixedHeight(36)
        btn_save_wa.setMinimumWidth(140)
        btn_save_wa.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #2980b9; }
        """)
        btn_save_wa.clicked.connect(self._save_twilio)
        btn_row_wa.addWidget(btn_save_wa)
        btn_test_wa = QPushButton("שלח הודעת בדיקה")
        btn_test_wa.setFixedHeight(36)
        btn_test_wa.setMinimumWidth(140)
        btn_test_wa.setStyleSheet("""
            QPushButton { background: #27ae60; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #219a52; }
        """)
        btn_test_wa.clicked.connect(self._test_twilio)
        btn_row_wa.addWidget(btn_test_wa)

        btn_trigger = QPushButton("שלח תזכורות עכשיו")
        btn_trigger.setFixedHeight(36)
        btn_trigger.setMinimumWidth(150)
        btn_trigger.setStyleSheet("""
            QPushButton { background: #8e44ad; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #732d91; }
        """)
        btn_trigger.clicked.connect(self._trigger_scheduler)
        btn_row_wa.addWidget(btn_trigger)
        wa_layout.addLayout(btn_row_wa)

        self._wa_status_label = QLabel("")
        self._wa_status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
        wa_layout.addWidget(self._wa_status_label)

        # ── Section: Google Calendar ───────────────────────────
        gcal_section = self._section("סנכרון Google Calendar")
        layout.addWidget(gcal_section)
        gcal_layout = gcal_section.layout()

        gcal_note = QLabel(
            "סנכרן תורים לחשבון Google Calendar שלך לגיבוי ונגישות מכל מקום.\n"
            "תחילה צור פרטי OAuth 2.0 ב-Google Cloud Console (Desktop App) והורד את credentials.json."
        )
        gcal_note.setWordWrap(True)
        gcal_note.setStyleSheet("color: #666; font-size: 12px; border: none; background: transparent;")
        gcal_layout.addWidget(gcal_note)

        # Credentials file row
        cred_row = QHBoxLayout()
        cred_row.setSpacing(8)
        cred_lbl = QLabel("credentials.json:")
        cred_lbl.setFixedWidth(130)
        cred_lbl.setStyleSheet("color: #2c3e50; font-size: 13px; border: none; background: transparent;")
        cred_row.addWidget(cred_lbl)
        self._gcal_cred_input = QLineEdit()
        self._gcal_cred_input.setMinimumHeight(36)
        self._gcal_cred_input.setReadOnly(True)
        self._gcal_cred_input.setPlaceholderText("בחר קובץ credentials.json...")
        self._gcal_cred_input.setStyleSheet("""
            QLineEdit { border: 1px solid #ccc; border-radius: 5px;
                        padding: 7px 10px; font-size: 13px; background: #fafafa; }
        """)
        cred_row.addWidget(self._gcal_cred_input, stretch=1)
        btn_cred_browse = QPushButton("בחר קובץ")
        btn_cred_browse.setFixedHeight(36)
        btn_cred_browse.setMinimumWidth(100)
        btn_cred_browse.setStyleSheet("""
            QPushButton { background: #7f8c8d; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #636e72; }
        """)
        btn_cred_browse.clicked.connect(self._browse_gcal_credentials)
        cred_row.addWidget(btn_cred_browse)
        gcal_layout.addLayout(cred_row)

        # Calendar ID row
        calid_row = QHBoxLayout()
        calid_row.setSpacing(8)
        calid_lbl = QLabel("מזהה לוח שנה:")
        calid_lbl.setFixedWidth(130)
        calid_lbl.setStyleSheet("color: #2c3e50; font-size: 13px; border: none; background: transparent;")
        calid_row.addWidget(calid_lbl)
        self._gcal_id_input = QLineEdit()
        self._gcal_id_input.setMinimumHeight(36)
        self._gcal_id_input.setPlaceholderText("primary  (ברירת מחדל)")
        self._gcal_id_input.setText(settings_service.get("google_calendar_id", ""))
        self._gcal_id_input.setStyleSheet("""
            QLineEdit { border: 1px solid #ccc; border-radius: 5px;
                        padding: 7px 10px; font-size: 13px; background: #fafafa; }
        """)
        calid_row.addWidget(self._gcal_id_input, stretch=1)
        gcal_layout.addLayout(calid_row)

        # Action buttons row
        gcal_btn_row = QHBoxLayout()
        gcal_btn_row.setSpacing(8)
        gcal_btn_row.addStretch()

        self._btn_gcal_connect = QPushButton("חבר לחשבון Google")
        self._btn_gcal_connect.setFixedHeight(36)
        self._btn_gcal_connect.setMinimumWidth(160)
        self._btn_gcal_connect.setStyleSheet("""
            QPushButton { background: #4285f4; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #3367d6; }
        """)
        self._btn_gcal_connect.clicked.connect(self._gcal_connect)
        gcal_btn_row.addWidget(self._btn_gcal_connect)

        btn_gcal_sync = QPushButton("סנכרן הכל עכשיו")
        btn_gcal_sync.setFixedHeight(36)
        btn_gcal_sync.setMinimumWidth(140)
        btn_gcal_sync.setStyleSheet("""
            QPushButton { background: #27ae60; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #219a52; }
        """)
        btn_gcal_sync.clicked.connect(self._gcal_sync_all)
        gcal_btn_row.addWidget(btn_gcal_sync)

        btn_gcal_disconnect = QPushButton("נתק")
        btn_gcal_disconnect.setFixedHeight(36)
        btn_gcal_disconnect.setMinimumWidth(80)
        btn_gcal_disconnect.setStyleSheet("""
            QPushButton { background: #fdf2f2; color: #e74c3c;
                          border: 1px solid #f5c6c6; border-radius: 5px;
                          font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #fce8e8; border-color: #e74c3c; }
        """)
        btn_gcal_disconnect.clicked.connect(self._gcal_disconnect)
        gcal_btn_row.addWidget(btn_gcal_disconnect)

        gcal_layout.addLayout(gcal_btn_row)

        self._gcal_status_label = QLabel("")
        self._gcal_status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
        gcal_layout.addWidget(self._gcal_status_label)

        self._refresh_gcal_status()

        # ── Section: notification rules ────────────────────────
        rules_section = self._section("הגדרות הודעות אוטומטיות")
        layout.addWidget(rules_section)
        rules_layout = rules_section.layout()

        rules_note = QLabel(
            "הגדר את תוכן ותזמון ההודעות האוטומטיות.\n"
            "תגיות זמינות: {שם}  {תאריך}  {שעה}  {מטפל}"
        )
        rules_note.setStyleSheet("color: #666; font-size: 12px; border: none; background: transparent;")
        rules_note.setWordWrap(True)
        rules_layout.addWidget(rules_note)

        self._rules_container = QWidget()
        self._rules_container.setStyleSheet("QWidget { background: transparent; border: none; }")
        self._rules_container_layout = QVBoxLayout(self._rules_container)
        self._rules_container_layout.setContentsMargins(0, 0, 0, 0)
        self._rules_container_layout.setSpacing(8)
        rules_layout.addWidget(self._rules_container)

        btn_add_rule = QPushButton("+ הוסף חוק הודעה")
        btn_add_rule.setFixedHeight(34)
        btn_add_rule.setStyleSheet("""
            QPushButton { background: #7f8c8d; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #636e72; }
        """)
        btn_add_rule.clicked.connect(self._add_rule)
        rules_layout.addWidget(btn_add_rule)

        btn_save_rules = QPushButton("שמור הגדרות הודעות")
        btn_save_rules.setFixedHeight(36)
        btn_save_rules.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #2980b9; }
        """)
        btn_save_rules.clicked.connect(self._save_rules)
        rules_layout.addWidget(btn_save_rules)

        self._rules_status_label = QLabel("")
        self._rules_status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
        rules_layout.addWidget(self._rules_status_label)

        self._rule_cards: list[_RuleCard] = []
        self._load_rules_ui()

        layout.addStretch()

    def _save_twilio(self):
        from_num = self._from_input.text().strip()
        sid = self._sid_input.text().strip()
        token = self._token_input.text().strip()
        if not from_num or not sid or not token:
            self._wa_status_label.setStyleSheet("color: #e74c3c; font-size: 12px; border: none; background: transparent;")
            self._wa_status_label.setText("יש למלא את כל השדות.")
            return
        settings_service.set("twilio_from_number", from_num)
        settings_service.set_secret("twilio_account_sid", sid)
        settings_service.set_secret("twilio_auth_token", token)
        self._wa_status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
        self._wa_status_label.setText("פרטי Twilio נשמרו בהצלחה.")

    def _trigger_scheduler(self):
        from services.notification_scheduler import notification_scheduler
        try:
            notification_scheduler._process()
            self._wa_status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
            self._wa_status_label.setText("בוצעה בדיקת תזכורות — בדוק את הוואטסאפ.")
        except Exception as e:
            self._wa_status_label.setStyleSheet("color: #e74c3c; font-size: 12px; border: none; background: transparent;")
            self._wa_status_label.setText(f"שגיאה: {e}")

    def _test_twilio(self):
        from services.notification_service import notification_service
        phone = self._test_phone_input.text().strip()
        if not phone:
            self._wa_status_label.setStyleSheet("color: #e74c3c; font-size: 12px; border: none; background: transparent;")
            self._wa_status_label.setText("יש להזין מספר טלפון לבדיקה.")
            return
        if not notification_service.is_configured():
            self._wa_status_label.setStyleSheet("color: #e74c3c; font-size: 12px; border: none; background: transparent;")
            self._wa_status_label.setText("יש לשמור פרטי Twilio לפני הבדיקה.")
            return
        ok, err = notification_service.send_test(phone)
        if ok:
            self._wa_status_label.setStyleSheet("color: #27ae60; font-size: 12px; border: none; background: transparent;")
            self._wa_status_label.setText("הודעת בדיקה נשלחה בהצלחה!")
        else:
            self._wa_status_label.setStyleSheet("color: #e74c3c; font-size: 12px; border: none; background: transparent;")
            self._wa_status_label.setText(f"שגיאה: {err}")

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

    def _load_rules_ui(self):
        from services.notification_service import get_rules
        self._rule_cards = []
        # Clear existing widgets
        while self._rules_container_layout.count():
            item = self._rules_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for rule in get_rules():
            self._append_rule_card(rule)

    def _append_rule_card(self, rule: dict):
        card = _RuleCard(rule, on_delete=self._delete_rule)
        self._rule_cards.append(card)
        self._rules_container_layout.addWidget(card)

    def _add_rule(self):
        new_rule = {
            "key": f"rule_{uuid.uuid4().hex[:8]}",
            "type": "reminder",
            "hours": 24,
            "message": "שלום {שם},\nתזכורת לתורך {תאריך} בשעה {שעה}.",
        }
        self._append_rule_card(new_rule)

    def _delete_rule(self, card: "_RuleCard"):
        self._rule_cards = [c for c in self._rule_cards if c is not card]
        self._rules_container_layout.removeWidget(card)
        card.deleteLater()

    def _save_rules(self):
        from services.settings_service import settings_service
        rules = [c.get_rule() for c in self._rule_cards]
        settings_service.set("notification_rules", rules)
        self._rules_status_label.setStyleSheet(
            "color: #27ae60; font-size: 12px; border: none; background: transparent;"
        )
        self._rules_status_label.setText("הגדרות ההודעות נשמרו בהצלחה.")

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

    # ── Google Calendar handlers ───────────────────────────────

    def _browse_gcal_credentials(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "בחר קובץ credentials.json", os.path.expanduser("~"),
            "JSON files (*.json)"
        )
        if path:
            self._gcal_cred_input.setText(path)

    def _gcal_connect(self):
        cred_path = self._gcal_cred_input.text().strip()
        if not cred_path or not os.path.isfile(cred_path):
            self._gcal_status_label.setStyleSheet(
                "color: #e74c3c; font-size: 12px; border: none; background: transparent;"
            )
            self._gcal_status_label.setText("יש לבחור קובץ credentials.json תחילה.")
            return

        cal_id = self._gcal_id_input.text().strip()
        if cal_id:
            settings_service.set("google_calendar_id", cal_id)

        from services.google_calendar_service import google_calendar_service
        self._gcal_status_label.setStyleSheet(
            "color: #2c3e50; font-size: 12px; border: none; background: transparent;"
        )
        self._gcal_status_label.setText("פותח חלון הרשאה בדפדפן...")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        ok, err = google_calendar_service.authorize(cred_path)
        if ok:
            self._gcal_status_label.setStyleSheet(
                "color: #27ae60; font-size: 12px; border: none; background: transparent;"
            )
            self._gcal_status_label.setText("החיבור ל-Google Calendar הצליח!")
        else:
            self._gcal_status_label.setStyleSheet(
                "color: #e74c3c; font-size: 12px; border: none; background: transparent;"
            )
            self._gcal_status_label.setText(f"שגיאה: {err}")
        self._refresh_gcal_status()

    def _gcal_sync_all(self):
        from services.google_calendar_service import google_calendar_service
        if not google_calendar_service.is_connected():
            self._gcal_status_label.setStyleSheet(
                "color: #e74c3c; font-size: 12px; border: none; background: transparent;"
            )
            self._gcal_status_label.setText("לא מחובר ל-Google Calendar.")
            return

        cal_id = self._gcal_id_input.text().strip()
        if cal_id:
            settings_service.set("google_calendar_id", cal_id)

        self._gcal_status_label.setStyleSheet(
            "color: #2c3e50; font-size: 12px; border: none; background: transparent;"
        )
        self._gcal_status_label.setText("מסנכרן...")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            synced, errors = google_calendar_service.sync_all()
            if errors == 0:
                self._gcal_status_label.setStyleSheet(
                    "color: #27ae60; font-size: 12px; border: none; background: transparent;"
                )
                self._gcal_status_label.setText(f"סונכרנו {synced} תורים בהצלחה.")
            else:
                self._gcal_status_label.setStyleSheet(
                    "color: #e67e22; font-size: 12px; border: none; background: transparent;"
                )
                self._gcal_status_label.setText(f"סונכרנו {synced} תורים, {errors} שגיאות.")
        except Exception as e:
            self._gcal_status_label.setStyleSheet(
                "color: #e74c3c; font-size: 12px; border: none; background: transparent;"
            )
            self._gcal_status_label.setText(f"שגיאה: {e}")

    def _gcal_disconnect(self):
        from services.google_calendar_service import google_calendar_service
        google_calendar_service.disconnect()
        self._gcal_status_label.setStyleSheet(
            "color: #27ae60; font-size: 12px; border: none; background: transparent;"
        )
        self._gcal_status_label.setText("הנתקת מ-Google Calendar.")
        self._refresh_gcal_status()

    def _refresh_gcal_status(self):
        from services.google_calendar_service import google_calendar_service
        connected = google_calendar_service.is_connected()
        if connected:
            self._btn_gcal_connect.setText("מחובר ✓ — חבר מחדש")
            self._btn_gcal_connect.setStyleSheet("""
                QPushButton { background: #27ae60; color: white; border: none;
                              border-radius: 5px; font-size: 13px; padding: 0 12px; }
                QPushButton:hover { background: #219a52; }
            """)
        else:
            self._btn_gcal_connect.setText("חבר לחשבון Google")
            self._btn_gcal_connect.setStyleSheet("""
                QPushButton { background: #4285f4; color: white; border: none;
                              border-radius: 5px; font-size: 13px; padding: 0 12px; }
                QPushButton:hover { background: #3367d6; }
            """)


class _RuleCard(QWidget):
    """A single notification rule card displayed in the settings rules section."""

    _TYPE_OPTIONS = [
        ("תזכורת (לפני התור)", "reminder"),
        ("מעקב (אחרי התור)",  "followup"),
    ]
    _TAGS = ["{שם}", "{תאריך}", "{שעה}", "{מטפל}"]

    def __init__(self, rule: dict, on_delete, parent=None):
        super().__init__(parent)
        self._key = rule.get("key", f"rule_{uuid.uuid4().hex[:8]}")
        self._on_delete = on_delete
        self._build(rule)

    def _build(self, rule: dict):
        self.setStyleSheet("""
            _RuleCard, QWidget#ruleCard {
                background: #f8f9fa;
                border: 1px solid #dde;
                border-radius: 6px;
            }
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(6)

        # Row 1: type selector + hours + delete
        top = QHBoxLayout()
        top.setSpacing(8)

        self._type_combo = QComboBox()
        self._type_combo.setMinimumHeight(32)
        self._type_combo.setStyleSheet("""
            QComboBox { border: 1px solid #ccc; border-radius: 4px;
                        padding: 4px 8px; font-size: 13px; background: white; }
            QComboBox::drop-down { border: none; width: 20px; }
        """)
        for label, value in self._TYPE_OPTIONS:
            self._type_combo.addItem(label, value)
        # Set current
        for i, (_, v) in enumerate(self._TYPE_OPTIONS):
            if v == rule.get("type", "reminder"):
                self._type_combo.setCurrentIndex(i)
                break
        top.addWidget(self._type_combo)

        hours_lbl = QLabel("שעות:")
        hours_lbl.setStyleSheet("font-size: 13px; border: none; background: transparent;")
        top.addWidget(hours_lbl)

        self._hours_spin = QSpinBox()
        self._hours_spin.setRange(1, 720)
        self._hours_spin.setValue(int(rule.get("hours", 24)))
        self._hours_spin.setFixedWidth(70)
        self._hours_spin.setMinimumHeight(32)
        self._hours_spin.setStyleSheet("""
            QSpinBox { border: 1px solid #ccc; border-radius: 4px;
                       padding: 4px 6px; font-size: 13px; background: white; }
        """)
        top.addWidget(self._hours_spin)

        top.addStretch()

        btn_del = QPushButton("מחק")
        btn_del.setFixedHeight(30)
        btn_del.setMinimumWidth(60)
        btn_del.setStyleSheet("""
            QPushButton { background: #fdf2f2; color: #e74c3c;
                          border: 1px solid #f5c6c6; border-radius: 4px;
                          font-size: 12px; padding: 0 8px; }
            QPushButton:hover { background: #fce8e8; border-color: #e74c3c; }
        """)
        btn_del.clicked.connect(lambda: self._on_delete(self))
        top.addWidget(btn_del)

        outer.addLayout(top)

        # Row 2: message label
        msg_lbl = QLabel("תוכן ההודעה:")
        msg_lbl.setStyleSheet("font-size: 12px; color: #555; border: none; background: transparent;")
        outer.addWidget(msg_lbl)

        # Row 3: message textarea
        self._msg_edit = QTextEdit()
        self._msg_edit.setPlainText(rule.get("message", ""))
        self._msg_edit.setFixedHeight(80)
        self._msg_edit.setStyleSheet("""
            QTextEdit { border: 1px solid #ccc; border-radius: 4px;
                        padding: 6px; font-size: 13px; background: white; }
        """)
        outer.addWidget(self._msg_edit)

        # Row 4: tag insertion buttons
        tags_row = QHBoxLayout()
        tags_row.setSpacing(4)
        tag_lbl = QLabel("הכנס תגית:")
        tag_lbl.setStyleSheet("font-size: 12px; color: #555; border: none; background: transparent;")
        tags_row.addWidget(tag_lbl)
        for tag in self._TAGS:
            btn = QPushButton(tag)
            btn.setFixedHeight(26)
            btn.setStyleSheet("""
                QPushButton { background: #ecf0f1; color: #2c3e50;
                              border: 1px solid #bdc3c7; border-radius: 4px;
                              font-size: 12px; padding: 0 8px; }
                QPushButton:hover { background: #d5dbdb; }
            """)
            btn.clicked.connect(
                lambda checked=False, t=tag: self._msg_edit.insertPlainText(t)
            )
            tags_row.addWidget(btn)
        tags_row.addStretch()
        outer.addLayout(tags_row)

    def get_rule(self) -> dict:
        return {
            "key": self._key,
            "type": self._type_combo.currentData(),
            "hours": self._hours_spin.value(),
            "message": self._msg_edit.toPlainText(),
        }


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
