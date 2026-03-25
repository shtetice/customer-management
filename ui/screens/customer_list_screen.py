import csv
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QAbstractItemView, QFileDialog
)
from PyQt6.QtGui import QColor, QFont, QBrush
from PyQt6.QtCore import Qt, pyqtSignal

from database.models import CustomerStatus, Gender
from controllers.customer_controller import customer_controller
from services.auth_service import auth_service
from ui.styles import STATUS_COLORS, STATUS_BG_COLORS, STATUS_LABELS


class CustomerListScreen(QWidget):
    request_add_customer = pyqtSignal()
    request_edit_customer = pyqtSignal(int)   # customer_id
    request_view_customer = pyqtSignal(int)   # customer_id

    COLUMNS = ["שם", "שם משפחה", "טלפון", "אימייל", "סטטוס", "פעולות"]

    _COMBO_STYLE = """
        QComboBox {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 13px;
            background: white;
            color: #2c3e50;
        }
        QComboBox:focus { border-color: #3498db; }
        QComboBox::drop-down { border: none; width: 24px; }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #2c3e50;
            border: 1px solid #b0b8c1;
            outline: none;
            selection-background-color: #3498db;
            selection-color: #ffffff;
            font-size: 13px;
        }
        QComboBox QAbstractItemView::item { padding: 4px 8px; min-height: 22px; }
        QComboBox QAbstractItemView::item:hover { background-color: #3498db; color: white; }
    """

    _HEBREW_MONTHS = [
        "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
        "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"
    ]

    def __init__(self):
        super().__init__()
        self._current_customers = []
        self._build_ui()

    def _build_ui(self):
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header row
        header_row = QHBoxLayout()
        title = QLabel("ניהול לקוחות")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header_row.addWidget(title)
        header_row.addStretch()

        btn_csv = QPushButton("ייצא CSV")
        btn_csv.setFixedHeight(34)
        btn_csv.setStyleSheet("""
            QPushButton { background:#27ae60; color:white; border:none; border-radius:4px;
                          font-size:13px; padding: 0 12px; }
            QPushButton:hover { background:#219a52; }
        """)
        btn_csv.clicked.connect(self._export_csv)
        header_row.addWidget(btn_csv)

        if auth_service.has_permission("customers.add"):
            btn_add = QPushButton("+ הוסף לקוח")
            btn_add.setFixedHeight(34)
            btn_add.clicked.connect(self.request_add_customer.emit)
            header_row.addWidget(btn_add)

        layout.addLayout(header_row)

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(12)

        search_label = QLabel("🔍  חיפוש:")
        search_label.setStyleSheet("color: #555; font-size: 13px;")
        search_row.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("שם, טלפון או אימייל...")
        self.search_input.setMinimumHeight(34)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus { border-color: #3498db; }
        """)
        self.search_input.textChanged.connect(self._refresh)
        search_row.addWidget(self.search_input, stretch=1)

        status_label = QLabel("סטטוס:")
        status_label.setStyleSheet("color: #555; font-size: 13px;")
        search_row.addWidget(status_label)

        self.status_filter = QComboBox()
        self.status_filter.setMinimumHeight(34)
        self.status_filter.setStyleSheet(self._COMBO_STYLE + "QComboBox { min-width: 120px; }")
        self.status_filter.addItem("כל הסטטוסים", None)
        for s in CustomerStatus:
            self.status_filter.addItem(STATUS_LABELS[s.value], s)
        self.status_filter.currentIndexChanged.connect(self._refresh)
        search_row.addWidget(self.status_filter)

        layout.addLayout(search_row)

        # Filter row: birth month + birth year + city + gender
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        month_label = QLabel("חודש לידה:")
        month_label.setStyleSheet("color: #555; font-size: 13px;")
        filter_row.addWidget(month_label)

        self.month_filter = QComboBox()
        self.month_filter.setMinimumHeight(34)
        self.month_filter.setStyleSheet(self._COMBO_STYLE + "QComboBox { min-width: 100px; }")
        self.month_filter.addItem("כל החודשים", None)
        for i, name in enumerate(self._HEBREW_MONTHS, start=1):
            self.month_filter.addItem(name, i)
        self.month_filter.currentIndexChanged.connect(self._refresh)
        filter_row.addWidget(self.month_filter)

        year_label = QLabel("שנת לידה:")
        year_label.setStyleSheet("color: #555; font-size: 13px;")
        filter_row.addWidget(year_label)

        self.year_filter = QComboBox()
        self.year_filter.setMinimumHeight(34)
        self.year_filter.setStyleSheet(self._COMBO_STYLE + "QComboBox { min-width: 90px; }")
        self.year_filter.addItem("כל השנים", None)
        self.year_filter.currentIndexChanged.connect(self._refresh)
        filter_row.addWidget(self.year_filter)

        city_label = QLabel("עיר:")
        city_label.setStyleSheet("color: #555; font-size: 13px;")
        filter_row.addWidget(city_label)

        self.city_filter = QComboBox()
        self.city_filter.setMinimumHeight(34)
        self.city_filter.setStyleSheet(self._COMBO_STYLE + "QComboBox { min-width: 110px; }")
        self.city_filter.addItem("כל הערים", None)
        self.city_filter.currentIndexChanged.connect(self._refresh)
        filter_row.addWidget(self.city_filter)

        gender_label = QLabel("מגדר:")
        gender_label.setStyleSheet("color: #555; font-size: 13px;")
        filter_row.addWidget(gender_label)

        self.gender_filter = QComboBox()
        self.gender_filter.setMinimumHeight(34)
        self.gender_filter.setStyleSheet(self._COMBO_STYLE + "QComboBox { min-width: 90px; }")
        self.gender_filter.addItem("הכל", None)
        self.gender_filter.addItem("זכר", Gender.MALE)
        self.gender_filter.addItem("נקבה", Gender.FEMALE)
        self.gender_filter.addItem("אחר", Gender.OTHER)
        self.gender_filter.currentIndexChanged.connect(self._refresh)
        filter_row.addWidget(self.gender_filter)

        filter_row.addStretch()

        layout.addLayout(filter_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 110)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(46)
        layout.addWidget(self.table)

        self._refresh()

    def _populate_year_city_filters(self):
        """Reload year and city dropdowns from DB (preserves current selection if still valid)."""
        cur_year = self.year_filter.currentData()
        cur_city = self.city_filter.currentData()

        self.year_filter.blockSignals(True)
        self.city_filter.blockSignals(True)

        self.year_filter.clear()
        self.year_filter.addItem("כל השנים", None)
        for y in customer_controller.get_distinct_birth_years():
            self.year_filter.addItem(str(y), y)

        self.city_filter.clear()
        self.city_filter.addItem("כל הערים", None)
        for c in customer_controller.get_distinct_cities():
            self.city_filter.addItem(c, c)

        # Restore previous selections if still available
        for i in range(self.year_filter.count()):
            if self.year_filter.itemData(i) == cur_year:
                self.year_filter.setCurrentIndex(i)
                break
        for i in range(self.city_filter.count()):
            if self.city_filter.itemData(i) == cur_city:
                self.city_filter.setCurrentIndex(i)
                break

        self.year_filter.blockSignals(False)
        self.city_filter.blockSignals(False)

    def _refresh(self):
        self._populate_year_city_filters()

        query = self.search_input.text().strip()
        status = self.status_filter.currentData()
        birth_month = self.month_filter.currentData()
        birth_year = self.year_filter.currentData()
        city = self.city_filter.currentData()
        gender = self.gender_filter.currentData()

        if query:
            customers = customer_controller.search(
                query, birth_month=birth_month, birth_year=birth_year, city=city, gender=gender
            )
            if status:
                customers = [c for c in customers if c.status == status]
        else:
            customers = customer_controller.get_all(
                status=status, birth_month=birth_month, birth_year=birth_year, city=city, gender=gender
            )

        self._current_customers = customers

        self.table.setRowCount(0)
        for row_idx, customer in enumerate(customers):
            self.table.insertRow(row_idx)

            self.table.setItem(row_idx, 0, self._cell(customer.name))
            self.table.setItem(row_idx, 1, self._cell(customer.surname))
            phones = [p for p in [customer.phone, customer.phone2, customer.phone3] if p]
            self.table.setItem(row_idx, 2, self._cell(" | ".join(phones)))
            self.table.setItem(row_idx, 3, self._cell(customer.email or ""))

            # Status badge cell
            status_text = "● " + STATUS_LABELS.get(customer.status.value, customer.status.value)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            color_hex = STATUS_COLORS.get(customer.status.value, "#999")
            bg_hex = STATUS_BG_COLORS.get(customer.status.value, "#f5f5f5")
            status_item.setForeground(QBrush(QColor(color_hex)))
            status_item.setBackground(QBrush(QColor(bg_hex)))
            font = QFont()
            font.setBold(True)
            status_item.setFont(font)
            self.table.setItem(row_idx, 4, status_item)

            # Details button
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(8, 4, 8, 4)
            actions_layout.addStretch()

            btn_details = QPushButton("👁  פרטים")
            btn_details.setFixedHeight(28)
            btn_details.setMinimumWidth(80)
            btn_details.setStyleSheet("""
                QPushButton {
                    background: #f0f4f8; color: #2c3e50;
                    border: 1px solid #bdc3c7; border-radius: 5px;
                    font-size: 12px; padding: 0 8px;
                }
                QPushButton:hover { background: #d6eaf8; border-color: #3498db; color: #2980b9; }
            """)
            btn_details.clicked.connect(lambda checked=False, cid=customer.id: self.request_view_customer.emit(cid))
            actions_layout.addWidget(btn_details)

            self.table.setCellWidget(row_idx, 5, actions_widget)
            self.table.setRowHeight(row_idx, 46)

    def _cell(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text or "")
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter)
        item.setForeground(QBrush(QColor("#2c3e50")))
        return item

    def _export_csv(self):
        if not self._current_customers:
            QMessageBox.information(self, "ייצוא CSV", "אין לקוחות לייצוא לפי הפילטרים הנוכחיים.")
            return

        default_name = f"customers_{datetime.now().strftime('%Y%m%d')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "שמור קובץ CSV", default_name, "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["שם", "שם משפחה", "טלפון", "אימייל", "עיר", "כתובת", "סטטוס", "תאריך לידה"])
                for c in self._current_customers:
                    phones = " | ".join(p for p in [c.phone, c.phone2, c.phone3] if p)
                    dob = c.date_of_birth.strftime("%d/%m/%Y") if c.date_of_birth else ""
                    status = STATUS_LABELS.get(c.status.value, c.status.value)
                    writer.writerow([c.name, c.surname, phones, c.email or "", c.city or "", c.address or "", status, dob])
            QMessageBox.information(self, "ייצוא CSV", f"הקובץ נשמר בהצלחה:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", f"לא ניתן לשמור את הקובץ:\n{str(e)}")

    def _confirm_delete(self, customer_id: int):
        customer = customer_controller.get_by_id(customer_id)
        if not customer:
            return
        reply = QMessageBox.question(
            self,
            "אישור מחיקה",
            f"האם אתה בטוח שברצונך למחוק את {customer.name} {customer.surname}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                customer_controller.delete(customer_id)
                self._refresh()
            except Exception as e:
                QMessageBox.critical(self, "שגיאה", str(e))
