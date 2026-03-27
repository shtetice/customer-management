from datetime import datetime, date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QMessageBox, QFrame,
    QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from controllers.appointment_controller import appointment_controller
from controllers.customer_controller import customer_controller
from database.models import AppointmentStatus
from ui.screens.add_customer_screen import _DatePickerButton

FIELD_STYLE = """
    QLineEdit, QTextEdit, QComboBox {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 7px 10px;
        font-size: 13px;
        background: white;
        color: #2c3e50;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border-color: #3498db; }
    QComboBox QAbstractItemView {
        background: white; color: #2c3e50;
        border: 1px solid #b0b8c1;
        selection-background-color: #3498db;
        selection-color: white;
    }
    QComboBox QAbstractItemView::item { padding: 4px 8px; min-height: 22px; }
"""
LABEL_STYLE = "font-size: 13px; color: #555; margin-bottom: 2px;"


class AddAppointmentDialog(QDialog):
    saved = pyqtSignal()

    def __init__(
        self,
        appointment_id: int | None = None,
        prefill_dt: datetime | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._appointment_id = appointment_id
        self._prefill_dt = prefill_dt
        self._selected_customer_id: int | None = None
        self._all_customers = customer_controller.get_all()

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("עריכת תור" if appointment_id else "הוספת תור")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        if appointment_id:
            self._load(appointment_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("עריכת תור" if self._appointment_id else "הוספת תור חדש")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # ── Customer search ──────────────────────────────────
        layout.addWidget(self._lbl("לקוח *"))
        self._customer_search = QLineEdit()
        self._customer_search.setPlaceholderText("חפש לקוח לפי שם או טלפון...")
        self._customer_search.setMinimumHeight(36)
        self._customer_search.setStyleSheet(FIELD_STYLE)
        self._customer_search.textChanged.connect(self._filter_customers)
        layout.addWidget(self._customer_search)

        self._customer_list = QListWidget()
        self._customer_list.setMaximumHeight(120)
        self._customer_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc; border-radius: 5px;
                background: white; font-size: 13px;
            }
            QListWidget::item { padding: 5px 10px; }
            QListWidget::item:selected { background: #3498db; color: white; }
        """)
        self._customer_list.setVisible(False)
        self._customer_list.itemClicked.connect(self._select_customer)
        layout.addWidget(self._customer_list)

        # ── Date ─────────────────────────────────────────────
        layout.addWidget(self._lbl("תאריך *"))
        self.date_picker = _DatePickerButton()
        if self._prefill_dt:
            self.date_picker.set_date(self._prefill_dt.date())
        else:
            self.date_picker.set_date(date.today())
        layout.addWidget(self.date_picker)

        # ── Time ─────────────────────────────────────────────
        layout.addWidget(self._lbl("שעה *"))
        self.time_combo = QComboBox()
        self.time_combo.setMinimumHeight(36)
        self.time_combo.setStyleSheet(FIELD_STYLE)
        for h in range(7, 22):
            for m in (0, 30):
                self.time_combo.addItem(f"{h:02d}:{m:02d}", (h, m))
        if self._prefill_dt:
            for i in range(self.time_combo.count()):
                h, m = self.time_combo.itemData(i)
                if h == self._prefill_dt.hour and m == self._prefill_dt.minute:
                    self.time_combo.setCurrentIndex(i)
                    break
        layout.addWidget(self.time_combo)

        # ── Duration ─────────────────────────────────────────
        layout.addWidget(self._lbl("משך הטיפול"))
        self.duration_combo = QComboBox()
        self.duration_combo.setMinimumHeight(36)
        self.duration_combo.setStyleSheet(FIELD_STYLE)
        for label, val in [
            ("30 דקות", 30), ("45 דקות", 45), ("60 דקות", 60),
            ("90 דקות", 90), ("120 דקות", 120),
        ]:
            self.duration_combo.addItem(label, val)
        self.duration_combo.setCurrentIndex(2)  # default 60 min
        layout.addWidget(self.duration_combo)

        # ── Staff ─────────────────────────────────────────────
        layout.addWidget(self._lbl("מטפל/ת (אופציונלי)"))
        self.staff_input = QLineEdit()
        self.staff_input.setPlaceholderText("שם המטפל/ת...")
        self.staff_input.setMinimumHeight(36)
        self.staff_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.staff_input)

        # ── Status (edit only) ────────────────────────────────
        if self._appointment_id:
            layout.addWidget(self._lbl("סטטוס"))
            self.status_combo = QComboBox()
            self.status_combo.setMinimumHeight(36)
            self.status_combo.setStyleSheet(FIELD_STYLE)
            for label, val in [
                ("מתוכנן", AppointmentStatus.SCHEDULED),
                ("הושלם", AppointmentStatus.COMPLETED),
                ("בוטל", AppointmentStatus.CANCELLED),
                ("לא הגיע/ה", AppointmentStatus.NO_SHOW),
            ]:
                self.status_combo.addItem(label, val)
            layout.addWidget(self.status_combo)
        else:
            self.status_combo = None

        # ── Notes ─────────────────────────────────────────────
        layout.addWidget(self._lbl("הערות"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("הערות נוספות...")
        self.notes_input.setFixedHeight(60)
        self.notes_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.notes_input)

        # ── Error ─────────────────────────────────────────────
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        layout.addWidget(self.error_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #eee;")
        layout.addWidget(line)

        # ── Buttons ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        if self._appointment_id:
            btn_delete = QPushButton("מחק תור")
            btn_delete.setFixedHeight(34)
            btn_delete.setStyleSheet(
                "background:#fdf2f2;color:#e74c3c;"
                "border:1px solid #f5c6c6;border-radius:4px;padding:0 10px;"
            )
            btn_delete.clicked.connect(self._delete)
            btn_row.addWidget(btn_delete)

        btn_cancel = QPushButton("ביטול")
        btn_cancel.setFixedHeight(34)
        btn_cancel.setStyleSheet(
            "background:#ecf0f1;color:#555;border:1px solid #ccc;border-radius:4px;padding:0 10px;"
        )
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("שמור תור")
        btn_save.setFixedHeight(34)
        btn_save.setStyleSheet("""
            QPushButton { background:#3498db; color:white; border:none;
                          border-radius:4px; font-size:13px; padding:0 14px; }
            QPushButton:hover { background:#2980b9; }
        """)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(LABEL_STYLE)
        return l

    def _filter_customers(self, text: str):
        text = text.strip().lower()
        if not text:
            self._customer_list.setVisible(False)
            return
        matches = [
            c for c in self._all_customers
            if text in f"{c.name} {c.surname}".lower()
            or (c.phone and text in c.phone)
        ][:10]
        self._customer_list.clear()
        for c in matches:
            phone_part = f"  |  {c.phone}" if c.phone else ""
            item = QListWidgetItem(f"{c.name} {c.surname}{phone_part}")
            item.setData(Qt.ItemDataRole.UserRole, c.id)
            self._customer_list.addItem(item)
        self._customer_list.setVisible(bool(matches))

    def _select_customer(self, item: QListWidgetItem):
        self._selected_customer_id = item.data(Qt.ItemDataRole.UserRole)
        display = item.text().split("  |  ")[0]
        self._customer_search.blockSignals(True)
        self._customer_search.setText(display)
        self._customer_search.blockSignals(False)
        self._customer_list.setVisible(False)

    def _load(self, appt_id: int):
        try:
            a = appointment_controller.get_by_id(appt_id)
            if not a:
                self.reject()
                return
            self._selected_customer_id = a.customer_id
            c = customer_controller.get_by_id(a.customer_id)
            if c:
                self._customer_search.setText(f"{c.name} {c.surname}")
            self.date_picker.set_date(a.date.date())
            for i in range(self.time_combo.count()):
                h, m = self.time_combo.itemData(i)
                if h == a.date.hour and m == a.date.minute:
                    self.time_combo.setCurrentIndex(i)
                    break
            for i in range(self.duration_combo.count()):
                if self.duration_combo.itemData(i) == a.duration_minutes:
                    self.duration_combo.setCurrentIndex(i)
                    break
            if a.staff_name:
                self.staff_input.setText(a.staff_name)
            if self.status_combo:
                for i in range(self.status_combo.count()):
                    if self.status_combo.itemData(i) == a.status:
                        self.status_combo.setCurrentIndex(i)
                        break
            if a.notes:
                self.notes_input.setPlainText(a.notes)
        except Exception as e:
            QMessageBox.critical(self, "שגיאה בטעינת תור", str(e))

    def _save(self):
        if not self._selected_customer_id:
            self.error_label.setText("יש לבחור לקוח")
            return
        d = self.date_picker.get_date()
        if not d:
            self.error_label.setText("יש לבחור תאריך")
            return
        h, m = self.time_combo.currentData()
        appt_dt = datetime(d.year, d.month, d.day, h, m)
        if appt_dt < datetime.now():
            reply = QMessageBox.question(
                self, "תור בעבר",
                f"התאריך שנבחר ({appt_dt.strftime('%d/%m/%Y %H:%M')}) הוא בעבר.\nהאם להמשיך בשמירה?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        duration = self.duration_combo.currentData()
        staff = self.staff_input.text().strip()
        notes = self.notes_input.toPlainText().strip()
        try:
            if self._appointment_id:
                status = self.status_combo.currentData()
                appointment_controller.update(
                    self._appointment_id, appt_dt, duration, staff, notes, status
                )
            else:
                appointment_controller.create(
                    self._selected_customer_id, appt_dt, duration, staff, notes
                )
            self.saved.emit()
            self.accept()
        except ValueError as e:
            self.error_label.setText(str(e))
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", str(e))

    def _delete(self):
        reply = QMessageBox.question(
            self, "מחיקת תור", "האם למחוק את התור לצמיתות?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                appointment_controller.delete(self._appointment_id)
                self.saved.emit()
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "שגיאה", str(e))
