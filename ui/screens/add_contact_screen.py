from datetime import datetime, date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from controllers.contact_controller import contact_controller
from ui.screens.add_customer_screen import _DatePickerButton

FIELD_STYLE = """
    QLineEdit, QTextEdit {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 7px 10px;
        font-size: 13px;
        background: white;
        color: #2c3e50;
    }
    QLineEdit:focus, QTextEdit:focus { border-color: #3498db; }
"""
LABEL_STYLE = "font-size: 13px; color: #555; margin-bottom: 2px;"


class AddContactDialog(QDialog):
    saved = pyqtSignal()

    def __init__(self, customer_id: int, log_id: int | None = None, parent=None):
        super().__init__(parent)
        self._customer_id = customer_id
        self._log_id = log_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("עריכת יצירת קשר" if log_id else "הוספת יצירת קשר")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build_ui()
        if log_id:
            self._load(log_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("עריכת יצירת קשר" if self._log_id else "הוספת יצירת קשר")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Date
        layout.addWidget(self._lbl("תאריך"))
        self.date_picker = _DatePickerButton()
        self.date_picker.set_date(date.today())
        layout.addWidget(self.date_picker)

        # Subject
        layout.addWidget(self._lbl("נושא *"))
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("לדוגמה: שיחת טלפון, פגישה, ...")
        self.subject_input.setMinimumHeight(36)
        self.subject_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.subject_input)

        # Content
        layout.addWidget(self._lbl("תוכן"))
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("פירוט השיחה / הפנייה...")
        self.content_input.setFixedHeight(120)
        self.content_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.content_input)

        # Error
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        layout.addWidget(self.error_label)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #eee;")
        layout.addWidget(line)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("ביטול")
        btn_cancel.setFixedHeight(34)
        btn_cancel.setStyleSheet("background:#ecf0f1;color:#555;border:1px solid #ccc;border-radius:4px;")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("שמור")
        btn_save.setFixedHeight(34)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(LABEL_STYLE)
        return l

    def _load(self, log_id: int):
        try:
            log = contact_controller.get_by_id(log_id)
            if not log:
                self.reject()
                return
            self.date_picker.set_date(log.date.date() if hasattr(log.date, 'date') else log.date)
            self.subject_input.setText(log.subject or "")
            self.content_input.setPlainText(log.content or "")
        except Exception as e:
            QMessageBox.critical(self, "שגיאה בטעינת רשומה", str(e))

    def _save(self):
        d = self.date_picker.get_date()
        if not d:
            self.error_label.setText("יש לבחור תאריך")
            return
        contact_date = datetime(d.year, d.month, d.day)
        subject = self.subject_input.text().strip()
        content = self.content_input.toPlainText().strip()
        try:
            if self._log_id:
                contact_controller.update(self._log_id, contact_date, subject, content)
            else:
                contact_controller.create(self._customer_id, contact_date, subject, content)
            self.saved.emit()
            self.accept()
        except ValueError as e:
            self.error_label.setText(str(e))
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", str(e))
