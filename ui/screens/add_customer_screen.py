from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QMessageBox, QScrollArea, QFrame,
    QDialog, QCalendarWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from database.models import CustomerStatus, Gender
from controllers.customer_controller import customer_controller
from ui.styles import STATUS_LABELS


GENDER_LABELS = {
    Gender.MALE:   "זכר",
    Gender.FEMALE: "נקבה",
    Gender.OTHER:  "אחר",
}

FIELD_STYLE = """
    QLineEdit, QTextEdit {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 7px 10px;
        font-size: 13px;
        background: white;
        color: #2c3e50;
    }
    QLineEdit:focus, QTextEdit:focus {
        border-color: #3498db;
    }
"""

COMBO_STYLE = """
    QComboBox {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 7px 10px;
        font-size: 13px;
        background: white;
        color: #2c3e50;
    }
    QComboBox:focus {
        border-color: #3498db;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: left center;
        width: 24px;
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #b0b8c1;
        outline: none;
        selection-background-color: #3498db;
        selection-color: #ffffff;
        font-size: 13px;
    }
    QComboBox QAbstractItemView::item {
        padding: 4px 8px;
        min-height: 22px;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #3498db;
        color: white;
    }
"""

LABEL_STYLE = "font-size: 13px; color: #555; margin-bottom: 2px;"


class _DatePickerButton(QPushButton):
    """Button that opens a LTR calendar popup and emits date_changed."""
    date_changed = pyqtSignal(object)   # date | None

    def __init__(self, parent=None):
        super().__init__("לא צוין", parent)
        self._date = None
        self.setMinimumHeight(36)
        self._apply_style(False)
        self.clicked.connect(self._open_calendar)

    def _apply_style(self, selected: bool):
        color = "#2c3e50" if selected else "#aaa"
        self.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 7px 10px;
                font-size: 13px;
                background: white;
                color: {color};
                text-align: right;
            }}
            QPushButton:hover {{ border-color: #3498db; }}
            QPushButton:focus {{ border-color: #3498db; outline: none; }}
        """)

    def get_date(self) -> date | None:
        return self._date

    def set_date(self, d: date | None):
        self._date = d
        if d:
            self.setText(f"{d.day:02d}/{d.month:02d}/{d.year}")
            self._apply_style(True)
        else:
            self.setText("לא צוין")
            self._apply_style(False)

    def _open_calendar(self):
        dlg = QDialog(self.window())
        dlg.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        dlg.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        dlg.setStyleSheet("QDialog { border: 1px solid #ccc; border-radius: 6px; }")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(4, 4, 4, 4)

        cal = QCalendarWidget()
        cal.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        cal.setGridVisible(False)
        cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        cal.setMinimumDate(QDate(1920, 1, 1))
        cal.setMaximumDate(QDate.currentDate())
        cal.setSelectedDate(
            QDate(self._date.year, self._date.month, self._date.day)
            if self._date else QDate.currentDate()
        )
        cal.setStyleSheet("""
            QCalendarWidget QWidget { font-size: 13px; }
            QCalendarWidget QAbstractItemView:enabled {
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QCalendarWidget QToolButton {
                color: #2c3e50; font-size: 13px; font-weight: bold;
                background: transparent; border: none; padding: 4px 8px;
            }
            QCalendarWidget QToolButton:hover { color: #3498db; }
            QCalendarWidget QToolButton::menu-indicator { image: none; }
            QCalendarWidget #qt_calendar_navigationbar {
                background: #f5f7fa;
                border-bottom: 1px solid #e0e0e0;
                padding: 4px;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #ccc;
                font-size: 13px;
            }
            QCalendarWidget QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
            QCalendarWidget QSpinBox {
                color: #2c3e50;
                background: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 13px;
            }
        """)
        layout.addWidget(cal)

        pos = self.mapToGlobal(self.rect().bottomLeft())
        dlg.move(pos)

        def on_clicked(qdate: QDate):
            self.set_date(date(qdate.year(), qdate.month(), qdate.day()))
            self.date_changed.emit(self._date)
            dlg.accept()

        cal.clicked.connect(on_clicked)
        dlg.exec()


class AddCustomerScreen(QWidget):
    customer_saved = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, customer_id: int | None = None):
        super().__init__()
        self._customer_id = customer_id
        self._build_ui()
        if customer_id:
            self._load_customer(customer_id)

    def _build_ui(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(0)

        # Title
        title_text = "עריכת לקוח" if self._customer_id else "הוספת לקוח חדש"
        title = QLabel(title_text)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 16px;")
        outer.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        form_widget = QWidget()
        form_widget.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(14)
        form_layout.setContentsMargins(0, 0, 12, 0)

        # Row 1: שם + שם משפחה side by side
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        name_col.addWidget(self._label("שם פרטי *"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("הכנס שם פרטי")
        self.name_input.setMinimumHeight(36)
        self.name_input.setStyleSheet(FIELD_STYLE)
        name_col.addWidget(self.name_input)
        row1.addLayout(name_col)

        surname_col = QVBoxLayout()
        surname_col.setSpacing(4)
        surname_col.addWidget(self._label("שם משפחה *"))
        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("הכנס שם משפחה")
        self.surname_input.setMinimumHeight(36)
        self.surname_input.setStyleSheet(FIELD_STYLE)
        surname_col.addWidget(self.surname_input)
        row1.addLayout(surname_col)

        form_layout.addLayout(row1)

        # Row 2: phones + email side by side — both top-aligned via QWidget wrappers
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        row2.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Phone column widget
        phones_widget = QWidget()
        phones_widget.setStyleSheet("background: transparent;")
        phones_col = QVBoxLayout(phones_widget)
        phones_col.setSpacing(4)
        phones_col.setContentsMargins(0, 0, 0, 0)
        phones_col.addWidget(self._label("טלפון"))

        self.phone_inputs = []
        self._phones_container = QVBoxLayout()
        self._phones_container.setSpacing(4)
        self.phone_input = self._make_phone_input("050-0000000")
        self._phones_container.addWidget(self.phone_input)
        self.phone_inputs.append(self.phone_input)
        phones_col.addLayout(self._phones_container)

        self._btn_add_phone = QPushButton("+ הוסף מספר טלפון")
        self._btn_add_phone.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #3498db;
                border: none;
                font-size: 12px;
                padding: 0;
            }
            QPushButton:hover { color: #2980b9; }
        """)
        self._btn_add_phone.setFixedHeight(18)
        self._btn_add_phone.clicked.connect(self._add_phone_field)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 1, 0, 0)
        btn_row.addWidget(self._btn_add_phone)
        btn_row.addStretch()
        phones_col.addLayout(btn_row)

        row2.addWidget(phones_widget, alignment=Qt.AlignmentFlag.AlignTop)

        # Email column widget
        email_widget = QWidget()
        email_widget.setStyleSheet("background: transparent;")
        email_col = QVBoxLayout(email_widget)
        email_col.setSpacing(4)
        email_col.setContentsMargins(0, 0, 0, 0)
        email_col.addWidget(self._label("אימייל"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("example@email.com")
        self.email_input.setMinimumHeight(36)
        self.email_input.setStyleSheet(FIELD_STYLE)
        email_col.addWidget(self.email_input)

        row2.addWidget(email_widget, alignment=Qt.AlignmentFlag.AlignTop)

        form_layout.addLayout(row2)

        # Row 3: מגדר + סטטוס side by side
        row3 = QHBoxLayout()
        row3.setSpacing(16)

        gender_col = QVBoxLayout()
        gender_col.setSpacing(4)
        gender_col.addWidget(self._label("מגדר"))
        self.gender_combo = QComboBox()
        self.gender_combo.setMinimumHeight(36)
        self.gender_combo.setStyleSheet(COMBO_STYLE)
        self.gender_combo.addItem("לא צוין", None)
        for g, label in GENDER_LABELS.items():
            self.gender_combo.addItem(label, g)
        gender_col.addWidget(self.gender_combo)
        row3.addLayout(gender_col)

        status_col = QVBoxLayout()
        status_col.setSpacing(4)
        status_col.addWidget(self._label("סטטוס *"))
        self.status_combo = QComboBox()
        self.status_combo.setMinimumHeight(36)
        self.status_combo.setStyleSheet(COMBO_STYLE)
        for s in CustomerStatus:
            self.status_combo.addItem(STATUS_LABELS[s.value], s)
        status_col.addWidget(self.status_combo)
        row3.addLayout(status_col)

        form_layout.addLayout(row3)

        # Row 4: כתובת + תאריך לידה side by side
        row4 = QHBoxLayout()
        row4.setSpacing(16)

        address_col = QVBoxLayout()
        address_col.setSpacing(4)
        address_col.addWidget(self._label("כתובת"))
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("רחוב, עיר")
        self.address_input.setMinimumHeight(36)
        self.address_input.setStyleSheet(FIELD_STYLE)
        address_col.addWidget(self.address_input)
        row4.addLayout(address_col)

        dob_col = QVBoxLayout()
        dob_col.setSpacing(4)
        dob_col.addWidget(self._label("תאריך לידה"))
        self.dob_input = _DatePickerButton()
        dob_col.addWidget(self.dob_input)
        row4.addLayout(dob_col)

        form_layout.addLayout(row4)

        # Notes (full width)
        notes_col = QVBoxLayout()
        notes_col.setSpacing(4)
        notes_col.addWidget(self._label("הערות"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("הערות על הלקוח...")
        self.notes_input.setFixedHeight(110)
        self.notes_input.setStyleSheet(FIELD_STYLE)
        notes_col.addWidget(self.notes_input)
        form_layout.addLayout(notes_col)

        form_layout.addStretch()
        scroll.setWidget(form_widget)
        outer.addWidget(scroll)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 12px; margin-top: 6px;")
        outer.addWidget(self.error_label)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #eee; margin: 10px 0;")
        outer.addWidget(divider)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("ביטול")
        btn_cancel.setFixedHeight(36)
        btn_cancel.setMinimumWidth(90)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #ecf0f1; color: #555;
                border: 1px solid #ccc; border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background: #dde; }
        """)
        btn_cancel.clicked.connect(self.cancelled.emit)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("שמור לקוח")
        btn_save.setFixedHeight(36)
        btn_save.setMinimumWidth(110)
        btn_save.setStyleSheet("""
            QPushButton {
                background: #3498db; color: white;
                border: none; border-radius: 5px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)

        outer.addLayout(btn_row)

    def _make_phone_input(self, placeholder: str = "050-0000000") -> QLineEdit:
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setMinimumHeight(36)
        inp.setStyleSheet(FIELD_STYLE)
        return inp

    def _add_phone_field(self):
        if len(self.phone_inputs) >= 3:
            return
        inp = self._make_phone_input()
        self._phones_container.addWidget(inp)
        self.phone_inputs.append(inp)
        if len(self.phone_inputs) >= 3:
            self._btn_add_phone.setVisible(False)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(LABEL_STYLE)
        return lbl

    def _load_customer(self, customer_id: int):
        customer = customer_controller.get_by_id(customer_id)
        if not customer:
            QMessageBox.critical(self, "שגיאה", "הלקוח לא נמצא")
            self.cancelled.emit()
            return

        self.name_input.setText(customer.name)
        self.surname_input.setText(customer.surname)
        self.phone_inputs[0].setText(customer.phone or "")
        for extra in [customer.phone2, customer.phone3]:
            if extra:
                self._add_phone_field()
                self.phone_inputs[-1].setText(extra)
        self.email_input.setText(customer.email or "")
        self.address_input.setText(customer.address or "")
        if customer.date_of_birth:
            self.dob_input.set_date(customer.date_of_birth)
        self.notes_input.setPlainText(customer.notes or "")

        for i in range(self.gender_combo.count()):
            if self.gender_combo.itemData(i) == customer.gender:
                self.gender_combo.setCurrentIndex(i)
                break

        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == customer.status:
                self.status_combo.setCurrentIndex(i)
                break

    def _on_save(self):
        name = self.name_input.text().strip()
        surname = self.surname_input.text().strip()
        phones = [inp.text().strip() for inp in self.phone_inputs]
        phone  = phones[0] if len(phones) > 0 else ""
        phone2 = phones[1] if len(phones) > 1 else ""
        phone3 = phones[2] if len(phones) > 2 else ""
        email = self.email_input.text().strip()
        gender = self.gender_combo.currentData()
        status = self.status_combo.currentData()
        notes = self.notes_input.toPlainText().strip()
        address = self.address_input.text().strip()
        dob = self.dob_input.get_date()

        try:
            if self._customer_id:
                customer_controller.update(
                    self._customer_id, name, surname, gender,
                    phone, phone2, phone3, email, status, notes,
                    address=address, date_of_birth=dob
                )
            else:
                customer_controller.create(
                    name, surname, gender, phone, phone2, phone3, email, status, notes,
                    address=address, date_of_birth=dob
                )

            self.error_label.setText("")
            self.customer_saved.emit()
        except ValueError as e:
            self.error_label.setText(str(e))
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", f"אירעה שגיאה: {str(e)}")
