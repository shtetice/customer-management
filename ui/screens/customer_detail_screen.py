from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QFrame, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QBrush, QColor, QCursor

from controllers.customer_controller import customer_controller
from controllers.treatment_controller import treatment_controller
from controllers.receipt_controller import receipt_controller
from services.auth_service import auth_service
from ui.screens.add_treatment_screen import AddTreatmentDialog
from ui.screens.add_receipt_screen import AddReceiptDialog
from ui.styles import STATUS_LABELS, STATUS_COLORS


class CustomerDetailScreen(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, customer_id: int):
        super().__init__()
        self._customer_id = customer_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # Header row
        header = QHBoxLayout()
        btn_back = QPushButton("→ חזרה לרשימה")
        btn_back.setStyleSheet("""
            QPushButton { background:transparent; color:#3498db; border:none; font-size:13px; padding:0; }
            QPushButton:hover { color:#2980b9; }
        """)
        btn_back.clicked.connect(self.back_requested.emit)
        header.addWidget(btn_back)
        header.addStretch()
        layout.addLayout(header)

        # Customer summary card
        self._summary_card = QWidget()
        self._summary_card.setStyleSheet("""
            QWidget { background:#f0f7fd; border-radius:8px; border:1px solid #d6eaf8; }
        """)
        card_layout = QHBoxLayout(self._summary_card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(24)

        self._name_label = QLabel()
        self._name_label.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self._name_label.setStyleSheet("color:#2c3e50; border:none; background:transparent;")
        card_layout.addWidget(self._name_label)

        self._status_label = QLabel()
        self._status_label.setStyleSheet(
            "color:white; border-radius:10px; padding:3px 12px; font-size:12px; border:none;"
        )
        card_layout.addWidget(self._status_label)

        card_layout.addStretch()

        self._phone_label = QLabel()
        self._phone_label.setStyleSheet("color:#555; font-size:13px; border:none; background:transparent;")
        card_layout.addWidget(self._phone_label)

        self._email_label = QLabel()
        self._email_label.setStyleSheet("color:#555; font-size:13px; border:none; background:transparent;")
        card_layout.addWidget(self._email_label)

        layout.addWidget(self._summary_card)
        self._customer_name = ""
        self._refresh_summary()

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border:1px solid #ddd; border-radius:4px; background:white; }
            QTabBar::tab {
                background:#ecf0f1; color:#555; padding:8px 20px;
                border:1px solid #ddd; border-bottom:none; border-radius:4px 4px 0 0;
                font-size:13px; margin-left:2px;
            }
            QTabBar::tab:selected { background:white; color:#2c3e50; font-weight:bold; }
            QTabBar::tab:hover { background:#d5dbdb; }
        """)

        self.tabs.addTab(self._build_treatments_tab(), "היסטוריית טיפולים")
        self.tabs.addTab(self._build_receipts_tab(), "קבלות")
        layout.addWidget(self.tabs)

    # ── Summary card ──────────────────────────────────────────

    def _refresh_summary(self):
        c = customer_controller.get_by_id(self._customer_id)
        if not c:
            return
        self._name_label.setText(f"{c.name} {c.surname}")
        self._customer_name = f"{c.name} {c.surname}"
        status_text = STATUS_LABELS.get(c.status.value, c.status.value)
        color = STATUS_COLORS.get(c.status.value, "#999")
        self._status_label.setText(status_text)
        self._status_label.setStyleSheet(
            f"color:white; background:{color}; border-radius:10px; "
            f"padding:3px 12px; font-size:12px; border:none;"
        )
        phones = [p for p in [c.phone, c.phone2, c.phone3] if p]
        self._phone_label.setText("📞 " + " | ".join(phones) if phones else "")
        self._email_label.setText("✉ " + c.email if c.email else "")

    # ── Treatments tab ────────────────────────────────────────

    def _build_treatments_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.addStretch()
        if auth_service.has_permission("treatments.add"):
            btn_add = QPushButton("+ הוסף טיפול")
            btn_add.clicked.connect(self._add_treatment)
            top.addWidget(btn_add)
        layout.addLayout(top)

        self.treatments_table = self._make_table(
            ["תאריך", "תיאור", "בוצע על ידי", "הערות", "פעולות"]
        )
        self.treatments_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.treatments_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.treatments_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.treatments_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.treatments_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.treatments_table.setColumnWidth(4, 110)
        layout.addWidget(self.treatments_table)
        self._refresh_treatments()
        return widget

    def _refresh_treatments(self):
        treatments = treatment_controller.get_by_customer(self._customer_id)
        self.treatments_table.setRowCount(0)
        for i, t in enumerate(treatments):
            self.treatments_table.insertRow(i)
            self.treatments_table.setItem(i, 0, self._cell(t.date.strftime("%d/%m/%Y")))
            self.treatments_table.setItem(i, 1, self._cell(t.description or ""))
            self.treatments_table.setItem(i, 2, self._cell(t.performed_by or ""))
            self.treatments_table.setItem(i, 3, self._cell(t.notes or ""))
            self.treatments_table.setCellWidget(i, 4, self._treatment_actions(t.id))
            self.treatments_table.setRowHeight(i, 44)

    def _treatment_actions(self, treatment_id: int) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(8, 4, 8, 4)
        row.addStretch()

        btn = QPushButton("פעולות ▾")
        btn.setFixedHeight(28)
        btn.setMinimumWidth(80)
        btn.setStyleSheet("""
            QPushButton {
                background: #f0f4f8; color: #2c3e50;
                border: 1px solid #bdc3c7; border-radius: 5px;
                font-size: 12px; padding: 0 8px;
            }
            QPushButton:hover { background: #d6eaf8; border-color: #3498db; color: #2980b9; }
        """)

        def open_menu(tid=treatment_id):
            menu = QMenu(self)
            menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            menu.setStyleSheet("""
                QMenu {
                    background: white; border: 1px solid #ddd;
                    border-radius: 6px; padding: 4px; font-size: 13px;
                }
                QMenu::item { padding: 7px 20px; border-radius: 4px; color: #2c3e50; }
                QMenu::item:selected { background: #f0f4f8; }
                QMenu::separator { height: 1px; background: #eee; margin: 3px 8px; }
            """)
            menu.addAction("+ הוסף קבלה", lambda: self._add_receipt(tid))
            if auth_service.has_permission("treatments.add"):
                menu.addAction("✎  עריכה", lambda: self._edit_treatment(tid))
                menu.addSeparator()
                menu.addAction("✕  מחק", lambda: self._delete_treatment(tid))
            menu.exec(QCursor.pos())

        btn.clicked.connect(open_menu)
        row.addWidget(btn)
        return w

    def _add_treatment(self):
        dlg = AddTreatmentDialog(self._customer_id, parent=self)
        dlg.saved.connect(self._refresh_treatments)
        dlg.exec()

    def _edit_treatment(self, treatment_id: int):
        dlg = AddTreatmentDialog(self._customer_id, treatment_id=treatment_id, parent=self)
        dlg.saved.connect(self._refresh_treatments)
        dlg.exec()

    def _delete_treatment(self, treatment_id: int):
        reply = QMessageBox.question(
            self, "אישור מחיקה", "האם למחוק טיפול זה? קבלות מקושרות ינותקו.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                treatment_controller.delete(treatment_id)
                self._refresh_treatments()
            except Exception as e:
                QMessageBox.critical(self, "שגיאה", str(e))

    # ── Receipts tab ──────────────────────────────────────────

    def _build_receipts_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.addStretch()
        if auth_service.has_permission("receipts.add"):
            btn_add = QPushButton("+ הוסף קבלה")
            btn_add.clicked.connect(lambda: self._add_receipt(None))
            top.addWidget(btn_add)
        layout.addLayout(top)

        self.receipts_table = self._make_table(
            ["תאריך", "סכום", "תיאור", "טיפול מקושר", "פעולות"]
        )
        self.receipts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.receipts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.receipts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.receipts_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.receipts_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.receipts_table.setColumnWidth(4, 110)
        layout.addWidget(self.receipts_table)
        self._refresh_receipts()
        return widget

    def _refresh_receipts(self):
        receipts = receipt_controller.get_by_customer(self._customer_id)
        self.receipts_table.setRowCount(0)

        # Build treatment lookup
        treatments = {t.id: t for t in treatment_controller.get_by_customer(self._customer_id)}

        for i, r in enumerate(receipts):
            self.receipts_table.insertRow(i)
            self.receipts_table.setItem(i, 0, self._cell(r.date.strftime("%d/%m/%Y")))
            self.receipts_table.setItem(i, 1, self._cell(r.amount or ""))
            self.receipts_table.setItem(i, 2, self._cell(r.description or ""))
            linked = ""
            if r.treatment_id and r.treatment_id in treatments:
                t = treatments[r.treatment_id]
                linked = f"{t.date.strftime('%d/%m/%Y')} — {t.description}"
            self.receipts_table.setItem(i, 3, self._cell(linked))
            self.receipts_table.setCellWidget(i, 4, self._receipt_actions(r.id))
            self.receipts_table.setRowHeight(i, 44)

    def _receipt_actions(self, receipt_id: int) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(8, 4, 8, 4)
        row.addStretch()

        if not auth_service.has_permission("receipts.add"):
            return w

        btn = QPushButton("פעולות ▾")
        btn.setFixedHeight(28)
        btn.setMinimumWidth(80)
        btn.setStyleSheet("""
            QPushButton {
                background: #f0f4f8; color: #2c3e50;
                border: 1px solid #bdc3c7; border-radius: 5px;
                font-size: 12px; padding: 0 8px;
            }
            QPushButton:hover { background: #d6eaf8; border-color: #3498db; color: #2980b9; }
        """)

        def open_menu(rid=receipt_id):
            menu = QMenu(self)
            menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            menu.setStyleSheet("""
                QMenu {
                    background: white; border: 1px solid #ddd;
                    border-radius: 6px; padding: 4px; font-size: 13px;
                }
                QMenu::item { padding: 7px 20px; border-radius: 4px; color: #2c3e50; }
                QMenu::item:selected { background: #f0f4f8; }
                QMenu::separator { height: 1px; background: #eee; margin: 3px 8px; }
            """)
            menu.addAction("✎  עריכה", lambda: self._edit_receipt(rid))
            menu.addSeparator()
            menu.addAction("✕  מחק", lambda: self._delete_receipt(rid))
            menu.exec(QCursor.pos())

        btn.clicked.connect(open_menu)
        row.addWidget(btn)
        return w

    def _add_receipt(self, treatment_id: int | None):
        dlg = AddReceiptDialog(self._customer_id, preselect_treatment_id=treatment_id, customer_name=self._customer_name, parent=self)
        dlg.saved.connect(self._refresh_receipts)
        dlg.exec()

    def _edit_receipt(self, receipt_id: int):
        dlg = AddReceiptDialog(self._customer_id, receipt_id=receipt_id, customer_name=self._customer_name, parent=self)
        dlg.saved.connect(self._refresh_receipts)
        dlg.exec()

    def _delete_receipt(self, receipt_id: int):
        reply = QMessageBox.question(
            self, "אישור מחיקה", "האם למחוק קבלה זו?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                receipt_controller.delete(receipt_id)
                self._refresh_receipts()
            except Exception as e:
                QMessageBox.critical(self, "שגיאה", str(e))

    # ── Helpers ───────────────────────────────────────────────

    def _make_table(self, columns: list[str]) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(columns))
        t.setHorizontalHeaderLabels(columns)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        return t

    def _cell(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text or "")
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        item.setForeground(QBrush(QColor("#2c3e50")))
        return item
