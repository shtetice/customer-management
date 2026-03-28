from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QMessageBox, QScrollArea, QFrame,
    QDialog, QCalendarWidget, QApplication
)
from PyQt6.QtCore import Qt, QDate, QPoint, QTimer, QObject, QEvent, pyqtSignal
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

    def __init__(self, min_date=None, max_date=None, parent=None):
        super().__init__("לא צוין", parent)
        self._date = None
        self._min_date = min_date  # date | None
        self._max_date = max_date  # date | None
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
        if getattr(self, '_calendar_open', False):
            return
        self._calendar_open = True

        _state = {"nav_changed": False, "day_clicked": False}

        # Tool + FramelessWindowHint: floats above the parent without stealing
        # focus or triggering macOS window-activation flash.
        # show() (non-blocking) keeps the event loop free; an app-level event
        # filter handles clicks outside the dialog.
        dlg = QDialog(self.window())
        dlg.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint
        )
        dlg.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        dlg.setStyleSheet("QDialog { border: 1px solid #ccc; background: white; }")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)

        current_year = QDate.currentDate().year()
        if self._date:
            default = QDate(self._date.year, self._date.month, self._date.day)
        elif self._min_date:
            default = QDate(self._min_date.year, self._min_date.month, self._min_date.day)
        else:
            default = QDate(current_year - 30, 1, 1)

        # ── Custom nav bar ──────────────────────────────────────────────
        MONTHS = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"]

        nav = QWidget()
        nav.setStyleSheet("background: #f5f7fa; border-bottom: 1px solid #e0e0e0;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(6, 4, 6, 4)
        nav_layout.setSpacing(4)

        btn_prev = QPushButton("◀")
        btn_next = QPushButton("▶")
        for btn in (btn_prev, btn_next):
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("""
                QPushButton { background: transparent; border: none;
                              font-size: 12px; color: #2c3e50; }
                QPushButton:hover { color: #3498db; }
            """)

        combo_style = """
            QComboBox {
                border: 1px solid #ccc; border-radius: 3px;
                padding: 1px 4px; font-size: 13px; font-weight: bold;
                background: white; color: #2c3e50;
            }
            QComboBox::drop-down { border: none; width: 14px; }
            QComboBox QAbstractItemView {
                background: white; color: #2c3e50;
                selection-background-color: #3498db; selection-color: white;
                font-size: 13px;
            }
        """

        month_combo = QComboBox()
        month_combo.setFixedHeight(24)
        month_combo.setEditable(False)
        month_combo.setStyleSheet(combo_style)
        for m in MONTHS:
            month_combo.addItem(m)
        month_combo.setCurrentIndex(default.month() - 1)

        year_combo = QComboBox()
        year_combo.setMaxVisibleItems(10)
        year_combo.setFixedHeight(24)
        year_combo.setEditable(False)
        year_combo.setStyleSheet(combo_style)
        for y in range(current_year, 1919, -1):
            year_combo.addItem(str(y), y)
        year_combo.setCurrentText(str(default.year()))

        nav_layout.addWidget(btn_prev)
        nav_layout.addWidget(month_combo, 1)
        nav_layout.addWidget(year_combo)
        nav_layout.addWidget(btn_next)
        layout.addWidget(nav)

        # ── Calendar ────────────────────────────────────────────────────
        cal = QCalendarWidget()
        cal.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        cal.setGridVisible(False)
        cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        cal.setNavigationBarVisible(False)
        min_qdate = QDate(self._min_date.year, self._min_date.month, self._min_date.day) if self._min_date else QDate(1920, 1, 1)
        max_qdate = QDate(self._max_date.year, self._max_date.month, self._max_date.day) if self._max_date else QDate(2100, 12, 31)
        cal.setMinimumDate(min_qdate)
        cal.setMaximumDate(max_qdate)
        cal.setSelectedDate(default)
        cal.setStyleSheet("""
            QCalendarWidget QWidget { font-size: 13px; }
            QCalendarWidget QAbstractItemView:enabled {
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        layout.addWidget(cal)

        # ── Sync combos ↔ calendar page ──────────────────────────────────
        def update_combos(year, month):
            month_combo.blockSignals(True)
            year_combo.blockSignals(True)
            month_combo.setCurrentIndex(month - 1)
            year_combo.setCurrentText(str(year))
            month_combo.blockSignals(False)
            year_combo.blockSignals(False)

        cal.currentPageChanged.connect(update_combos)

        def prev_month():
            _state["nav_changed"] = True
            cal.showPreviousMonth()

        def next_month():
            _state["nav_changed"] = True
            cal.showNextMonth()

        btn_prev.clicked.connect(prev_month)
        btn_next.clicked.connect(next_month)

        def on_month_changed(idx):
            _state["nav_changed"] = True
            cal.setCurrentPage(cal.yearShown(), idx + 1)
        month_combo.currentIndexChanged.connect(on_month_changed)

        def on_year_changed(idx):
            _state["nav_changed"] = True
            cal.setCurrentPage(year_combo.itemData(idx), cal.monthShown())
        year_combo.currentIndexChanged.connect(on_year_changed)

        def on_day_clicked(qdate: QDate):
            _state["day_clicked"] = True
            self.set_date(date(qdate.year(), qdate.month(), qdate.day()))
            self.date_changed.emit(self._date)
            _close_calendar()

        cal.clicked.connect(on_day_clicked)

        # ── Outside-click detection ──────────────────────────────────────
        class _OutsideFilter(QObject):
            def eventFilter(self_f, obj, event):
                if event.type() != QEvent.Type.MouseButtonPress:
                    return False
                if not dlg.isVisible():
                    return False
                # Skip while a combo dropdown (or any Qt popup) is open
                if QApplication.activePopupWidget() is not None:
                    return False
                try:
                    gpos = event.globalPosition().toPoint()
                except AttributeError:
                    gpos = event.globalPos()
                if not dlg.geometry().contains(gpos):
                    _close_calendar()
                return False  # let the click reach its target

        efilter = _OutsideFilter(dlg)

        def _close_calendar():
            if not dlg.isVisible():
                return
            QApplication.instance().removeEventFilter(efilter)
            dlg.hide()
            dlg.deleteLater()
            # Small delay so a click on this button that triggered the close
            # doesn't immediately reopen the calendar
            QTimer.singleShot(200, _on_closed)

        def _on_closed():
            self._calendar_open = False
            if _state["nav_changed"] and not _state["day_clicked"]:
                warn = QDialog(self.window())
                warn.setWindowTitle("יציאה ללא בחירת תאריך")
                warn.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                warn.setMinimumWidth(300)
                wl = QVBoxLayout(warn)
                wl.setContentsMargins(20, 18, 20, 16)
                wl.setSpacing(14)
                lbl = QLabel(
                    "<div dir='rtl' style='font-size:13px;'>"
                    "ניווטת בלוח השנה אך לא בחרת יום.<br>"
                    "התאריך <b>לא יישמר</b>."
                    "</div>"
                )
                lbl.setWordWrap(True)
                wl.addWidget(lbl)
                br = QHBoxLayout()
                btn_ok = QPushButton("הבנתי")
                btn_ok.setFixedHeight(32)
                btn_ok.setStyleSheet(
                    "background:#3498db; color:white; border:none;"
                    "border-radius:4px; padding:0 14px;"
                )
                btn_ok.clicked.connect(warn.accept)
                br.addStretch()
                br.addWidget(btn_ok)
                wl.addLayout(br)
                warn.exec()

        # ── Position and show (non-blocking) ────────────────────────────
        dlg.adjustSize()
        pos = self.mapToGlobal(self.rect().bottomLeft())
        screen = QApplication.primaryScreen().availableGeometry()
        x = min(pos.x(), screen.right() - dlg.width())
        y = min(pos.y(), screen.bottom() - dlg.height())
        dlg.move(QPoint(max(x, screen.left()), max(y, screen.top())))

        QApplication.instance().installEventFilter(efilter)
        dlg.show()
        dlg.raise_()


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

        # Row 4: כתובת + עיר side by side
        row4 = QHBoxLayout()
        row4.setSpacing(16)

        address_col = QVBoxLayout()
        address_col.setSpacing(4)
        address_col.addWidget(self._label("כתובת"))
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("רחוב, מספר")
        self.address_input.setMinimumHeight(36)
        self.address_input.setStyleSheet(FIELD_STYLE)
        address_col.addWidget(self.address_input)
        row4.addLayout(address_col)

        city_col = QVBoxLayout()
        city_col.setSpacing(4)
        city_col.addWidget(self._label("עיר"))
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("תל אביב")
        self.city_input.setMinimumHeight(36)
        self.city_input.setStyleSheet(FIELD_STYLE)
        city_col.addWidget(self.city_input)
        row4.addLayout(city_col)

        form_layout.addLayout(row4)

        # Row 5: תאריך לידה (half width)
        row5 = QHBoxLayout()
        row5.setSpacing(16)

        dob_col = QVBoxLayout()
        dob_col.setSpacing(4)
        dob_col.addWidget(self._label("תאריך לידה"))
        self.dob_input = _DatePickerButton()
        dob_col.addWidget(self.dob_input)
        row5.addLayout(dob_col)
        row5.addStretch()

        form_layout.addLayout(row5)

        # Preferred treatments (checkboxes, full width)
        from PyQt6.QtWidgets import QCheckBox
        treat_col = QVBoxLayout()
        treat_col.setSpacing(6)
        treat_col.addWidget(self._label("טיפולים מועדפים"))
        treat_row = QHBoxLayout()
        treat_row.setSpacing(16)
        self._treatment_checks = {}
        for t in ["הזרקות", "לייזר", "שיזוף בהתזה", "שיזוף מקלחון"]:
            cb = QCheckBox(t)
            cb.setStyleSheet("font-size: 13px; color: #2c3e50;")
            treat_row.addWidget(cb)
            self._treatment_checks[t] = cb
        treat_row.addStretch()
        treat_col.addLayout(treat_row)
        form_layout.addLayout(treat_col)

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
        try:
            customer = customer_controller.get_by_id(customer_id)
            if not customer:
                QMessageBox.critical(self, "שגיאה", "הלקוח לא נמצא")
                self.cancelled.emit()
                return

            self.name_input.setText(customer.name or "")
            self.surname_input.setText(customer.surname or "")
            self.phone_inputs[0].setText(customer.phone or "")
            for extra in [customer.phone2, customer.phone3]:
                if extra:
                    self._add_phone_field()
                    self.phone_inputs[-1].setText(extra)
            self.email_input.setText(customer.email or "")
            self.address_input.setText(customer.address or "")
            self.city_input.setText(customer.city or "")
            if customer.date_of_birth:
                self.dob_input.set_date(customer.date_of_birth)
            self.notes_input.setPlainText(customer.notes or "")

            import json
            selected = []
            if customer.preferred_treatments:
                try:
                    selected = json.loads(customer.preferred_treatments)
                except Exception:
                    pass
            for t, cb in self._treatment_checks.items():
                cb.setChecked(t in selected)

            for i in range(self.gender_combo.count()):
                if self.gender_combo.itemData(i) == customer.gender:
                    self.gender_combo.setCurrentIndex(i)
                    break

            for i in range(self.status_combo.count()):
                if self.status_combo.itemData(i) == customer.status:
                    self.status_combo.setCurrentIndex(i)
                    break
        except Exception as e:
            QMessageBox.critical(self, "שגיאה בטעינת לקוח", str(e))

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
        city = self.city_input.text().strip()
        dob = self.dob_input.get_date()
        import json
        preferred = json.dumps(
            [t for t, cb in self._treatment_checks.items() if cb.isChecked()],
            ensure_ascii=False,
        )

        try:
            if self._customer_id:
                customer_controller.update(
                    self._customer_id, name, surname, gender,
                    phone, phone2, phone3, email, status, notes,
                    address=address, city=city, date_of_birth=dob,
                    preferred_treatments=preferred,
                )
            else:
                customer_controller.create(
                    name, surname, gender, phone, phone2, phone3, email, status, notes,
                    address=address, city=city, date_of_birth=dob,
                    preferred_treatments=preferred,
                )

            self.error_label.setText("")
            self.customer_saved.emit()
        except ValueError as e:
            self.error_label.setText(str(e))
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", f"אירעה שגיאה: {str(e)}")
