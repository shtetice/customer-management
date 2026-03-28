from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton, QMessageBox
)
from ui.confirm_dialog import confirm
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.activity_service import get_logs, delete_all_logs


class ActivityLogScreen(QWidget):
    COLUMNS = ["תאריך ושעה", "משתמש", "פעולה"]

    def __init__(self):
        super().__init__()
        self.setObjectName("activityLogScreen")
        self.setStyleSheet("#activityLogScreen { background-color: #f0f2f5; }")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("יומן פעילות")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        btn_refresh = QPushButton("רענן")
        btn_refresh.setFixedHeight(34)
        btn_refresh.clicked.connect(self._refresh)
        header.addWidget(btn_refresh)

        btn_delete = QPushButton("מחק יומן")
        btn_delete.setFixedHeight(34)
        btn_delete.setObjectName("btn_danger")
        btn_delete.clicked.connect(self._delete_all)
        header.addWidget(btn_delete)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.table)

        self._refresh()

    def _refresh(self):
        self.table.setRowCount(0)
        logs = get_logs()
        for row_idx, entry in enumerate(logs):
            self.table.insertRow(row_idx)
            ts = entry.timestamp.strftime("%d/%m/%Y %H:%M:%S") if entry.timestamp else ""
            self.table.setItem(row_idx, 0, self._cell(ts))
            self.table.setItem(row_idx, 1, self._cell(entry.username))
            self.table.setItem(row_idx, 2, self._cell(entry.action))

    def _delete_all(self):
        if confirm(self, "מחיקת יומן", "האם אתה בטוח שברצונך למחוק את כל הרשומות ביומן הפעילות?", danger=True):
            delete_all_logs()
            self._refresh()

    def _cell(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter
        )
        return item
