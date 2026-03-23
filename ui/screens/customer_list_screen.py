from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QBrush

from database.models import CustomerStatus
from controllers.customer_controller import customer_controller
from services.auth_service import auth_service
from ui.styles import STATUS_COLORS, STATUS_LABELS


class CustomerListScreen(QWidget):
    request_add_customer = pyqtSignal()
    request_edit_customer = pyqtSignal(int)   # customer_id
    request_view_customer = pyqtSignal(int)   # customer_id

    COLUMNS = ["שם", "שם משפחה", "טלפון", "אימייל", "סטטוס", "פעולות"]

    def __init__(self):
        super().__init__()
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

        if auth_service.has_permission("customers.add"):
            btn_add = QPushButton("+ הוסף לקוח")
            btn_add.clicked.connect(self.request_add_customer.emit)
            header_row.addWidget(btn_add)

        layout.addLayout(header_row)

        # Filter bar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        # Search field with label
        search_label = QLabel("🔍  חיפוש:")
        search_label.setStyleSheet("color: #555; font-size: 13px;")
        filter_row.addWidget(search_label)

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
        filter_row.addWidget(self.search_input, stretch=3)

        # Status filter with label
        status_label = QLabel("סטטוס:")
        status_label.setStyleSheet("color: #555; font-size: 13px;")
        filter_row.addWidget(status_label)

        self.status_filter = QComboBox()
        self.status_filter.setMinimumHeight(34)
        self.status_filter.setStyleSheet("""
            QComboBox {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 13px;
                background: white;
                min-width: 140px;
            }
            QComboBox:focus { border-color: #3498db; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow { width: 12px; height: 12px; }
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
        """)
        self.status_filter.addItem("כל הסטטוסים", None)
        for s in CustomerStatus:
            self.status_filter.addItem(STATUS_LABELS[s.value], s)
        self.status_filter.currentIndexChanged.connect(self._refresh)
        filter_row.addWidget(self.status_filter, stretch=1)

        layout.addLayout(filter_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 210)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self._refresh()

    def _refresh(self):
        query = self.search_input.text().strip()
        status = self.status_filter.currentData()

        if query:
            customers = customer_controller.search(query)
            if status:
                customers = [c for c in customers if c.status == status]
        else:
            customers = customer_controller.get_all(status=status)

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
            status_item.setForeground(QBrush(QColor(color_hex)))
            font = QFont()
            font.setBold(True)
            status_item.setFont(font)
            self.table.setItem(row_idx, 4, status_item)

            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            btn_view = QPushButton("פרטים")
            btn_view.setFixedWidth(65)
            btn_view.setStyleSheet("""
                QPushButton { background:#8e44ad; color:white; border:none; border-radius:4px; font-size:12px; }
                QPushButton:hover { background:#7d3c98; }
            """)
            btn_view.clicked.connect(lambda _, cid=customer.id: self.request_view_customer.emit(cid))
            actions_layout.addWidget(btn_view)

            if auth_service.has_permission("customers.edit"):
                btn_edit = QPushButton("עריכה")
                btn_edit.setFixedWidth(65)
                btn_edit.clicked.connect(lambda _, cid=customer.id: self.request_edit_customer.emit(cid))
                actions_layout.addWidget(btn_edit)

            if auth_service.has_permission("customers.delete"):
                btn_del = QPushButton("מחק")
                btn_del.setObjectName("btn_danger")
                btn_del.setFixedWidth(65)
                btn_del.clicked.connect(lambda _, cid=customer.id: self._confirm_delete(cid))
                actions_layout.addWidget(btn_del)

            self.table.setCellWidget(row_idx, 5, actions_widget)
            self.table.setRowHeight(row_idx, 44)

    def _cell(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text or "")
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        item.setForeground(QBrush(QColor("#2c3e50")))
        return item

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
