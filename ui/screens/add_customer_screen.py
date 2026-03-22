from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QMessageBox, QFormLayout, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from database.models import CustomerStatus, Gender
from controllers.customer_controller import customer_controller
from ui.styles import STATUS_LABELS


GENDER_LABELS = {
    Gender.MALE:   "זכר",
    Gender.FEMALE: "נקבה",
    Gender.OTHER:  "אחר",
}


class AddCustomerScreen(QWidget):
    customer_saved = pyqtSignal()   # emitted after successful save
    cancelled = pyqtSignal()

    def __init__(self, customer_id: int | None = None):
        """Pass customer_id to edit an existing customer, None to add new."""
        super().__init__()
        self._customer_id = customer_id
        self._build_ui()
        if customer_id:
            self._load_customer(customer_id)

    def _build_ui(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        # Title
        title_text = "עריכת לקוח" if self._customer_id else "הוספת לקוח חדש"
        title = QLabel(title_text)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        outer.addWidget(title)

        # Scroll area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setSpacing(12)
        form.setContentsMargins(0, 0, 0, 0)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("שם פרטי")
        form.addRow("שם *", self.name_input)

        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("שם משפחה")
        form.addRow("שם משפחה *", self.surname_input)

        self.gender_combo = QComboBox()
        self.gender_combo.addItem("לא צוין", None)
        for g, label in GENDER_LABELS.items():
            self.gender_combo.addItem(label, g)
        form.addRow("מגדר", self.gender_combo)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("מספר טלפון")
        form.addRow("טלפון", self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("כתובת אימייל")
        form.addRow("אימייל", self.email_input)

        self.status_combo = QComboBox()
        for s in CustomerStatus:
            self.status_combo.addItem(STATUS_LABELS[s.value], s)
        form.addRow("סטטוס *", self.status_combo)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("הערות...")
        self.notes_input.setFixedHeight(100)
        form.addRow("הערות", self.notes_input)

        scroll.setWidget(form_widget)
        outer.addWidget(scroll)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c;")
        outer.addWidget(self.error_label)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("ביטול")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.cancelled.emit)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("שמור")
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)

        outer.addLayout(btn_row)

    def _load_customer(self, customer_id: int):
        customer = customer_controller.get_by_id(customer_id)
        if not customer:
            QMessageBox.critical(self, "שגיאה", "הלקוח לא נמצא")
            self.cancelled.emit()
            return

        self.name_input.setText(customer.name)
        self.surname_input.setText(customer.surname)
        self.phone_input.setText(customer.phone or "")
        self.email_input.setText(customer.email or "")
        self.notes_input.setPlainText(customer.notes or "")

        # Set gender combo
        for i in range(self.gender_combo.count()):
            if self.gender_combo.itemData(i) == customer.gender:
                self.gender_combo.setCurrentIndex(i)
                break

        # Set status combo
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == customer.status:
                self.status_combo.setCurrentIndex(i)
                break

    def _on_save(self):
        name = self.name_input.text().strip()
        surname = self.surname_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        gender = self.gender_combo.currentData()
        status = self.status_combo.currentData()
        notes = self.notes_input.toPlainText().strip()

        try:
            if self._customer_id:
                customer_controller.update(
                    self._customer_id, name, surname, gender, phone, email, status, notes
                )
            else:
                customer_controller.create(name, surname, gender, phone, email, status, notes)

            self.error_label.setText("")
            self.customer_saved.emit()
        except ValueError as e:
            self.error_label.setText(str(e))
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", f"אירעה שגיאה: {str(e)}")
