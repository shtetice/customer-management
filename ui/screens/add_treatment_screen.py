from datetime import datetime, date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from controllers.treatment_controller import treatment_controller
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


class AddTreatmentDialog(QDialog):
    saved = pyqtSignal()

    def __init__(self, customer_id: int, treatment_id: int | None = None, parent=None):
        super().__init__(parent)
        self._customer_id = customer_id
        self._treatment_id = treatment_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("עריכת טיפול" if treatment_id else "הוספת טיפול")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build_ui()
        if treatment_id:
            self._load(treatment_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("עריכת טיפול" if self._treatment_id else "הוספת טיפול")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Date
        layout.addWidget(self._lbl("תאריך טיפול"))
        self.date_picker = _DatePickerButton()
        self.date_picker.set_date(date.today())
        layout.addWidget(self.date_picker)

        # Description
        layout.addWidget(self._lbl("תיאור הטיפול *"))
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("לדוגמה: ניקוי פנים, עיסוי, ...")
        self.description_input.setMinimumHeight(36)
        self.description_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.description_input)

        # Performed by
        layout.addWidget(self._lbl("בוצע על ידי"))
        self.performed_by_input = QLineEdit()
        self.performed_by_input.setPlaceholderText("שם המטפל/ת")
        self.performed_by_input.setMinimumHeight(36)
        self.performed_by_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.performed_by_input)

        # Notes
        layout.addWidget(self._lbl("הערות"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("הערות נוספות...")
        self.notes_input.setFixedHeight(80)
        self.notes_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.notes_input)

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

        btn_save = QPushButton("שמור טיפול")
        btn_save.setFixedHeight(34)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(LABEL_STYLE)
        return l

    def _load(self, treatment_id: int):
        t = treatment_controller.get_by_id(treatment_id)
        if not t:
            self.reject()
            return
        self.date_picker.set_date(t.date.date())
        self.description_input.setText(t.description or "")
        self.performed_by_input.setText(t.performed_by or "")
        self.notes_input.setPlainText(t.notes or "")

    def _save(self):
        d = self.date_picker.get_date()
        if not d:
            self.error_label.setText("יש לבחור תאריך טיפול")
            return
        treatment_date = datetime(d.year, d.month, d.day)
        description = self.description_input.text().strip()
        performed_by = self.performed_by_input.text().strip()
        notes = self.notes_input.toPlainText().strip()
        try:
            if self._treatment_id:
                treatment_controller.update(self._treatment_id, treatment_date, description, performed_by, notes)
            else:
                treatment_controller.create(self._customer_id, treatment_date, description, performed_by, notes)
            self.saved.emit()
            self.accept()
        except ValueError as e:
            self.error_label.setText(str(e))
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", str(e))
