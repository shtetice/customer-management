from __future__ import annotations
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QDialogButtonBox, QScrollArea, QMessageBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush

from controllers.campaign_controller import campaign_controller

_BTN = """
    QPushButton {{ background: {bg}; color: {fg}; border: none;
                   border-radius: 5px; font-size: 13px; padding: 0 16px; }}
    QPushButton:hover {{ background: {hover}; }}
    QPushButton:disabled {{ background: #bdc3c7; color: #fff; }}
"""


class MarketingScreen(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, customers: list, parent=None):
        super().__init__(parent)
        self._customers = customers          # pre-filtered list from customer screen
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(16)

        # Header
        header = QHBoxLayout()
        btn_back = QPushButton("← חזור")
        btn_back.setFixedHeight(34)
        btn_back.setStyleSheet(_BTN.format(bg="#ecf0f1", fg="#555", hover="#dde"))
        btn_back.clicked.connect(self.back_requested)
        header.addWidget(btn_back)
        header.addStretch()
        title = QLabel("📢  שיווק וקמפיינים")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        header.addWidget(title)
        outer.addLayout(header)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._tabs.addTab(self._build_compose_tab(), "שליחת קמפיין")
        self._tabs.addTab(self._build_history_tab(), "היסטוריית קמפיינים")
        outer.addWidget(self._tabs, 1)

    # ── Compose tab ───────────────────────────────────────────

    def _build_compose_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        # Customer count banner
        self._banner = QLabel()
        self._banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._banner.setStyleSheet(
            "background: #eaf4fb; border: 1px solid #aed6f1; border-radius: 6px;"
            "padding: 8px; font-size: 13px; color: #2c3e50;"
        )
        self._update_banner()
        layout.addWidget(self._banner)

        # Customer list (scrollable chips)
        list_frame = QFrame()
        list_frame.setStyleSheet(
            "QFrame { border: 1px solid #dde; border-radius: 6px; background: #fafafa; }"
        )
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(8, 8, 8, 8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(130)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        chips_widget = QWidget()
        chips_widget.setStyleSheet("background: transparent;")
        chips_layout = QHBoxLayout(chips_widget)
        chips_layout.setSpacing(6)
        chips_layout.setContentsMargins(4, 4, 4, 4)
        chips_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        chips_layout.setDirection(QHBoxLayout.Direction.RightToLeft)

        self._chip_layout = chips_layout
        self._refresh_chips()

        scroll.setWidget(chips_widget)
        list_layout.addWidget(scroll)
        layout.addWidget(list_frame)

        # Message area
        msg_lbl = QLabel("תוכן ההודעה:")
        msg_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(msg_lbl)

        self._msg_edit = QTextEdit()
        self._msg_edit.setPlaceholderText("כתוב את הודעת הקמפיין כאן...")
        self._msg_edit.setMinimumHeight(120)
        self._msg_edit.setStyleSheet("""
            QTextEdit { border: 1px solid #ccc; border-radius: 6px;
                        padding: 8px; font-size: 13px; }
        """)
        layout.addWidget(self._msg_edit, 1)

        # Char count
        self._char_lbl = QLabel("0 תווים")
        self._char_lbl.setStyleSheet("color: #999; font-size: 11px;")
        self._char_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._msg_edit.textChanged.connect(
            lambda: self._char_lbl.setText(f"{len(self._msg_edit.toPlainText())} תווים")
        )
        layout.addWidget(self._char_lbl)

        # Send button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_send = QPushButton("📤  שלח לכל הלקוחות")
        self._btn_send.setFixedHeight(40)
        self._btn_send.setMinimumWidth(200)
        self._btn_send.setStyleSheet(_BTN.format(bg="#27ae60", fg="white", hover="#219a52"))
        self._btn_send.clicked.connect(self._on_send)
        btn_row.addWidget(self._btn_send)
        layout.addLayout(btn_row)

        self._compose_status = QLabel("")
        self._compose_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._compose_status.setWordWrap(True)
        layout.addWidget(self._compose_status)

        return widget

    def _update_banner(self):
        n = len(self._customers)
        self._banner.setText(f"קמפיין זה ישלח ל־{n} לקוחות")

    def _refresh_chips(self):
        while self._chip_layout.count():
            item = self._chip_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for c in self._customers:
            chip = QLabel(f"{c.name} {c.surname}")
            chip.setStyleSheet(
                "background: #d6eaf8; color: #2c3e50; border-radius: 10px;"
                "padding: 3px 10px; font-size: 12px; border: none;"
            )
            self._chip_layout.addWidget(chip)
        self._chip_layout.addStretch()

    # ── Send logic ────────────────────────────────────────────

    def _on_send(self):
        message = self._msg_edit.toPlainText().strip()
        if not message:
            self._set_status("יש לכתוב הודעה לפני השליחה.", error=True)
            return
        if not self._customers:
            self._set_status("אין לקוחות בקמפיין.", error=True)
            return

        from services.notification_service import notification_service
        if not notification_service.is_configured():
            self._set_status("יש להגדיר פרטי Twilio בהגדרות לפני שליחה.", error=True)
            return

        # Check weekly frequency
        recent_ids = campaign_controller.get_recent_recipient_ids(days=7)
        repeat_customers = [c for c in self._customers if c.id in recent_ids]

        skip_ids: set[int] = set()
        if repeat_customers:
            dlg = _ApprovalDialog(repeat_customers, parent=self)
            result = dlg.exec()
            if result == QDialog.DialogCode.Rejected:
                return  # user cancelled entirely
            skip_ids = dlg.skip_ids()

        self._btn_send.setEnabled(False)
        self._set_status("שולח...", error=False)
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            camp_id, sent, failed, skipped = campaign_controller.send_campaign(
                message, self._customers, skip_ids=skip_ids
            )
            parts = [f"נשלח ל־{sent} לקוחות"]
            if failed:
                parts.append(f"{failed} נכשלו")
            if skipped:
                parts.append(f"{skipped} דולגו")
            self._set_status("  |  ".join(parts), error=bool(failed))
            self._msg_edit.clear()
            # Refresh history tab
            self._refresh_history()
        except Exception as e:
            self._set_status(f"שגיאה: {e}", error=True)
        finally:
            self._btn_send.setEnabled(True)

    def _set_status(self, text: str, *, error: bool):
        color = "#e74c3c" if error else "#27ae60"
        self._compose_status.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._compose_status.setText(text)

    # ── History tab ───────────────────────────────────────────

    def _build_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(8)

        btn_refresh = QPushButton("רענן")
        btn_refresh.setFixedHeight(32)
        btn_refresh.setFixedWidth(90)
        btn_refresh.setStyleSheet(_BTN.format(bg="#7f8c8d", fg="white", hover="#636e72"))
        btn_refresh.clicked.connect(self._refresh_history)
        layout.addWidget(btn_refresh, alignment=Qt.AlignmentFlag.AlignLeft)

        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels(["תאריך", "שולח", "נשלח", "נכשל", "דולג"])
        self._history_table.horizontalHeader().setStretchLastSection(False)
        self._history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 5):
            self._history_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._history_table.setAlternatingRowColors(True)
        self._history_table.verticalHeader().setVisible(False)
        self._history_table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._history_table.cellDoubleClicked.connect(self._on_history_double_click)
        layout.addWidget(self._history_table, 1)

        hint = QLabel("לחץ פעמיים על שורה לצפייה ברשימת הנמענים והודעה")
        hint.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(hint)

        self._refresh_history()
        return widget

    def _refresh_history(self):
        campaigns = campaign_controller.get_all()
        self._campaigns = campaigns
        self._history_table.setRowCount(0)
        for i, camp in enumerate(campaigns):
            self._history_table.insertRow(i)
            dt_str = camp.sent_at.strftime("%d/%m/%Y %H:%M") if camp.sent_at else ""
            self._history_table.setItem(i, 0, self._cell(dt_str))
            self._history_table.setItem(i, 1, self._cell(camp.sent_by or ""))
            counts = campaign_controller.count_recipients(camp.id)
            self._history_table.setItem(i, 2, self._cell(str(counts.get("sent", 0)), color="#27ae60"))
            self._history_table.setItem(i, 3, self._cell(str(counts.get("failed", 0)), color="#e74c3c"))
            self._history_table.setItem(i, 4, self._cell(str(counts.get("skipped", 0)), color="#e67e22"))

    @staticmethod
    def _cell(text: str, color: str | None = None) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if color:
            item.setForeground(QBrush(QColor(color)))
        return item

    def _on_history_double_click(self, row: int, _col: int):
        if row >= len(self._campaigns):
            return
        camp = self._campaigns[row]
        recipients = campaign_controller.get_recipients(camp.id)
        dlg = _CampaignDetailDialog(camp, recipients, parent=self)
        dlg.exec()

    # ── Public ────────────────────────────────────────────────

    def set_customers(self, customers: list):
        """Replace the customer list (called when launching a new campaign)."""
        self._customers = customers
        self._update_banner()
        self._refresh_chips()
        self._tabs.setCurrentIndex(0)


# ── Approval dialog ───────────────────────────────────────────────────────────

class _ApprovalDialog(QDialog):
    """Shown when one or more customers already received a marketing message this week."""

    def __init__(self, repeat_customers: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("אישור שליחה חוזרת")
        self.setMinimumWidth(420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._repeat = repeat_customers
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        warn = QLabel(
            f"הלקוחות הבאים ({len(self._repeat)}) כבר קיבלו הודעת שיווק השבוע.\n"
            "בחר כיצד להמשיך:"
        )
        warn.setWordWrap(True)
        warn.setStyleSheet("font-size: 13px; color: #2c3e50;")
        layout.addWidget(warn)

        lines = []
        for c in self._repeat:
            last_dt = campaign_controller.get_last_campaign_date(c.id)
            date_str = last_dt.strftime("%d/%m/%Y %H:%M") if last_dt else "?"
            lines.append(f"• {c.name} {c.surname}  (נשלח ב־{date_str})")
        names = QLabel("\n".join(lines))
        names.setStyleSheet(
            "background: #fdf2f2; border: 1px solid #f5c6c6; border-radius: 4px;"
            "padding: 8px; font-size: 12px; color: #e74c3c;"
        )
        names.setWordWrap(True)
        layout.addWidget(names)

        btns = QDialogButtonBox()
        btn_skip = btns.addButton("דלג עליהם", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_send_all = btns.addButton("שלח לכולם", QDialogButtonBox.ButtonRole.DestructiveRole)
        btn_cancel = btns.addButton("בטל", QDialogButtonBox.ButtonRole.RejectRole)

        self._skip = True
        btn_skip.clicked.connect(lambda: (setattr(self, "_skip", True), self.accept()))
        btn_send_all.clicked.connect(lambda: (setattr(self, "_skip", False), self.accept()))
        btn_cancel.clicked.connect(self.reject)

        layout.addWidget(btns)

    def skip_ids(self) -> set[int]:
        if self._skip:
            return {c.id for c in self._repeat}
        return set()


# ── Campaign detail dialog ─────────────────────────────────────────────────────

class _CampaignDetailDialog(QDialog):
    def __init__(self, campaign, recipients: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"פרטי קמפיין — {campaign.sent_at.strftime('%d/%m/%Y %H:%M') if campaign.sent_at else ''}")
        self.setMinimumSize(500, 420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build(campaign, recipients)

    def _build(self, campaign, recipients):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Message preview
        msg_lbl = QLabel("ההודעה שנשלחה:")
        msg_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(msg_lbl)

        msg_box = QTextEdit()
        msg_box.setReadOnly(True)
        msg_box.setPlainText(campaign.message)
        msg_box.setFixedHeight(90)
        msg_box.setStyleSheet(
            "QTextEdit { border: 1px solid #dde; border-radius: 4px; padding: 6px; font-size: 13px; }"
        )
        layout.addWidget(msg_box)

        # Recipients table
        recip_lbl = QLabel(f"נמענים ({len(recipients)}):")
        recip_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(recip_lbl)

        table = QTableWidget(len(recipients), 3)
        table.setHorizontalHeaderLabels(["שם", "טלפון", "סטטוס"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)

        STATUS_COLOR = {"sent": "#27ae60", "failed": "#e74c3c", "skipped": "#e67e22"}
        STATUS_HEB   = {"sent": "נשלח", "failed": "נכשל", "skipped": "דולג"}

        for i, r in enumerate(recipients):
            table.setItem(i, 0, QTableWidgetItem(r.customer_name or ""))
            table.setItem(i, 1, QTableWidgetItem(r.phone or ""))
            status_item = QTableWidgetItem(STATUS_HEB.get(r.status, r.status))
            color = STATUS_COLOR.get(r.status, "#999")
            status_item.setForeground(QBrush(QColor(color)))
            table.setItem(i, 2, status_item)
        layout.addWidget(table, 1)

        btn_close = QPushButton("סגור")
        btn_close.setFixedHeight(34)
        btn_close.setStyleSheet(_BTN.format(bg="#7f8c8d", fg="white", hover="#636e72"))
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignLeft)
