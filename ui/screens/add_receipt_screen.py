from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QDateEdit, QComboBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from controllers.receipt_controller import receipt_controller
from controllers.treatment_controller import treatment_controller

FIELD_STYLE = """
    QLineEdit, QTextEdit, QDateEdit, QComboBox {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 7px 10px;
        font-size: 13px;
        background: white;
        color: #2c3e50;
    }
    QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QComboBox:focus { border-color: #3498db; }
    QComboBox QAbstractItemView {
        background: white; color: #2c3e50;
        border: 1px solid #b0b8c1;
        selection-background-color: #3498db;
        selection-color: white;
    }
    QComboBox QAbstractItemView::item { padding: 4px 8px; min-height: 22px; }
"""
LABEL_STYLE = "font-size: 13px; color: #555; margin-bottom: 2px;"


class AddReceiptDialog(QDialog):
    saved = pyqtSignal()

    def __init__(self, customer_id: int, receipt_id: int | None = None,
                 preselect_treatment_id: int | None = None, parent=None):
        super().__init__(parent)
        self._customer_id = customer_id
        self._receipt_id = receipt_id
        self._preselect_treatment_id = preselect_treatment_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("עריכת קבלה" if receipt_id else "הוספת קבלה")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build_ui()
        if receipt_id:
            self._load(receipt_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("עריכת קבלה" if self._receipt_id else "הוספת קבלה")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Date
        layout.addWidget(self._lbl("תאריך"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setMinimumHeight(36)
        self.date_edit.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.date_edit)

        # Amount
        layout.addWidget(self._lbl("סכום *"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("לדוגמה: ₪250")
        self.amount_input.setMinimumHeight(36)
        self.amount_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.amount_input)

        # Description
        layout.addWidget(self._lbl("תיאור"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("פירוט השירות...")
        self.description_input.setFixedHeight(70)
        self.description_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.description_input)

        # Linked treatment
        layout.addWidget(self._lbl("טיפול מקושר (אופציונלי)"))
        self.treatment_combo = QComboBox()
        self.treatment_combo.setMinimumHeight(36)
        self.treatment_combo.setStyleSheet(FIELD_STYLE)
        self.treatment_combo.addItem("ללא קישור לטיפול", None)
        treatments = treatment_controller.get_by_customer(self._customer_id)
        for t in treatments:
            label = f"{t.date.strftime('%d/%m/%Y')} — {t.description}"
            self.treatment_combo.addItem(label, t.id)
        if self._preselect_treatment_id:
            for i in range(self.treatment_combo.count()):
                if self.treatment_combo.itemData(i) == self._preselect_treatment_id:
                    self.treatment_combo.setCurrentIndex(i)
                    break
        layout.addWidget(self.treatment_combo)

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

        btn_save = QPushButton("שמור קבלה")
        btn_save.setFixedHeight(34)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(LABEL_STYLE)
        return l

    def _load(self, receipt_id: int):
        r = receipt_controller.get_by_id(receipt_id)
        if not r:
            self.reject()
            return
        self.date_edit.setDate(QDate(r.date.year, r.date.month, r.date.day))
        self.amount_input.setText(r.amount or "")
        self.description_input.setPlainText(r.description or "")
        for i in range(self.treatment_combo.count()):
            if self.treatment_combo.itemData(i) == r.treatment_id:
                self.treatment_combo.setCurrentIndex(i)
                break

    def _save(self):
        qdate = self.date_edit.date()
        date = datetime(qdate.year(), qdate.month(), qdate.day())
        amount = self.amount_input.text().strip()
        description = self.description_input.toPlainText().strip()
        treatment_id = self.treatment_combo.currentData()
        try:
            if self._receipt_id:
                receipt_controller.update(self._receipt_id, date, amount, description, treatment_id)
            else:
                receipt_controller.create(self._customer_id, date, amount, description, treatment_id)
            self.saved.emit()
            self.accept()
        except ValueError as e:
            self.error_label.setText(str(e))
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", str(e))
