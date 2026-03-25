import os
import subprocess
import sys

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QFrame, QMenu, QScrollArea, QSizePolicy,
    QTextEdit, QDialog, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QBrush, QColor, QCursor

from controllers.customer_controller import customer_controller
from controllers.treatment_controller import treatment_controller
from controllers.receipt_controller import receipt_controller
from services.auth_service import auth_service
from ui.screens.add_treatment_screen import AddTreatmentDialog
from ui.screens.add_receipt_screen import AddReceiptDialog
from ui.screens.add_contact_screen import AddContactDialog
from controllers.contact_controller import contact_controller
from ui.styles import STATUS_LABELS, STATUS_COLORS


class CustomerDetailScreen(QWidget):
    back_requested = pyqtSignal()
    edit_requested = pyqtSignal(int)  # customer_id

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
        self._summary_card.setObjectName("summaryCard")
        self._summary_card.setStyleSheet("""
            QWidget#summaryCard {
                background: white;
                border-radius: 10px;
                border: 1px solid #e0e6ed;
            }
        """)
        card_layout = QHBoxLayout(self._summary_card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(20)

        # Avatar circle
        self._avatar_label = QLabel()
        self._avatar_label.setFixedSize(56, 56)
        self._avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        card_layout.addWidget(self._avatar_label)

        # Name + status column
        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        name_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._name_label = QLabel()
        self._name_label.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        self._name_label.setStyleSheet("color:#1a2533; border:none; background:transparent;")
        name_col.addWidget(self._name_label)

        self._status_label = QLabel()
        self._status_label.setStyleSheet(
            "color:white; border-radius:10px; padding:3px 12px; font-size:12px; border:none; font-weight:bold;"
        )
        self._status_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        name_col.addWidget(self._status_label)
        card_layout.addLayout(name_col)

        card_layout.addStretch()

        # Contact info column (phone + email stacked)
        contact_col = QVBoxLayout()
        contact_col.setSpacing(6)
        contact_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._phone_label = QLabel()
        self._phone_label.setStyleSheet("color:#444; font-size:13px; border:none; background:transparent;")
        contact_col.addWidget(self._phone_label)

        self._email_label = QLabel()
        self._email_label.setStyleSheet("color:#444; font-size:13px; border:none; background:transparent;")
        contact_col.addWidget(self._email_label)

        card_layout.addLayout(contact_col)

        # Edit / Delete buttons (top-right)
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        if auth_service.has_permission("customers.edit"):
            self._card_edit_btn = QPushButton("✎  עריכה")
            self._card_edit_btn.setFixedHeight(32)
            self._card_edit_btn.setMinimumWidth(90)
            self._card_edit_btn.setStyleSheet("""
                QPushButton {
                    background: #f0f4f8; color: #2c3e50;
                    border: 1px solid #d0d7de; border-radius: 6px;
                    font-size: 12px; padding: 0 12px;
                }
                QPushButton:hover { background: #dce8f5; border-color: #3498db; color: #2980b9; }
            """)
            cid = self._customer_id
            self._card_edit_btn.clicked.connect(lambda: self.edit_requested.emit(cid))
            btn_col.addWidget(self._card_edit_btn)

        if auth_service.has_permission("customers.delete"):
            btn_delete = QPushButton("✕  מחק")
            btn_delete.setFixedHeight(32)
            btn_delete.setMinimumWidth(90)
            btn_delete.setStyleSheet("""
                QPushButton {
                    background: #fdf2f2; color: #e74c3c;
                    border: 1px solid #f5c6c6; border-radius: 6px;
                    font-size: 12px; padding: 0 12px;
                }
                QPushButton:hover { background: #fce8e8; border-color: #e74c3c; }
            """)
            btn_delete.clicked.connect(self._confirm_delete)
            btn_col.addWidget(btn_delete)

        card_layout.addLayout(btn_col)

        self._summary_card.setMaximumHeight(110)
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

        self.tabs.addTab(self._build_info_tab(), "פרטי לקוח")
        self.tabs.addTab(self._build_treatments_tab(), "היסטוריית טיפולים")
        self.tabs.addTab(self._build_receipts_tab(), "קבלות")
        self.tabs.addTab(self._build_contact_tab(), "יצירת קשר")
        layout.addWidget(self.tabs, 1)

    # ── Summary card ──────────────────────────────────────────

    # Palette for avatar background — cycles by first letter
    _AVATAR_COLORS = [
        "#3498db", "#2ecc71", "#e67e22", "#9b59b6",
        "#1abc9c", "#e74c3c", "#2980b9", "#27ae60",
    ]

    def _refresh_summary(self):
        c = customer_controller.get_by_id(self._customer_id)
        if not c:
            return
        full_name = f"{c.name} {c.surname}"
        self._name_label.setText(full_name)
        self._customer_name = full_name

        # Avatar: initials in a colored circle
        initials = (c.name[:1] + c.surname[:1]).upper() if c.surname else c.name[:2].upper()
        color_idx = ord(c.name[0].upper()) % len(self._AVATAR_COLORS) if c.name else 0
        avatar_color = self._AVATAR_COLORS[color_idx]
        self._avatar_label.setText(initials)
        self._avatar_label.setStyleSheet(f"""
            QLabel {{
                background: {avatar_color};
                color: white;
                border-radius: 28px;
                border: none;
            }}
        """)

        # Status badge
        status_text = STATUS_LABELS.get(c.status.value, c.status.value)
        color = STATUS_COLORS.get(c.status.value, "#999")
        self._status_label.setText(f"● {status_text}")
        self._status_label.setStyleSheet(
            f"color:white; background:{color}; border-radius:10px; "
            f"padding:3px 12px; font-size:12px; border:none; font-weight:bold;"
        )

        # Contact
        phones = [p for p in [c.phone, c.phone2, c.phone3] if p]
        self._phone_label.setText("📞  " + "  |  ".join(phones) if phones else "")
        self._email_label.setText("✉   " + c.email if c.email else "")

    def _confirm_delete(self):
        from controllers.customer_controller import customer_controller
        c = customer_controller.get_by_id(self._customer_id)
        if not c:
            return

        dlg = _DeleteConfirmDialog(c.name, c.surname, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                customer_controller.delete(self._customer_id)
                self.back_requested.emit()
            except Exception as e:
                QMessageBox.critical(self, "שגיאה", str(e))

    # ── Info tab ──────────────────────────────────────────────

    def _build_info_tab(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        self._info_layout = QVBoxLayout(widget)
        self._info_layout.setSpacing(16)
        self._info_layout.setContentsMargins(20, 16, 20, 20)
        self._refresh_info()
        return widget

    @staticmethod
    def _make_section_card(title: str) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget()
        card.setObjectName("infoCard")
        card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        card.setStyleSheet("""
            QWidget#infoCard {
                background: white;
                border: 1px solid #e0e6ed;
                border-radius: 8px;
            }
        """)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 14, 16, 16)
        inner.setSpacing(10)

        hdr = QLabel(title)
        hdr.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #7f8c8d; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        inner.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #e8ecf0; border: none; max-height: 1px;")
        inner.addWidget(sep)

        rows = QVBoxLayout()
        rows.setSpacing(12)
        rows.setContentsMargins(0, 0, 0, 0)
        inner.addLayout(rows)
        return card, rows

    @staticmethod
    def _add_grid_row(rows: QVBoxLayout, label: str, value: str):
        # Each row is an explicit HBox: [value — stretches left] [label — fixed width right]
        # Using LTR layout so column ordering is predictable regardless of parent direction.
        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent; border: none;")
        row_widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        row_hbox = QHBoxLayout(row_widget)
        row_hbox.setContentsMargins(0, 0, 0, 0)
        row_hbox.setSpacing(16)

        val = QLabel(value if value else "—")
        val.setWordWrap(True)
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignTop)
        if value:
            val.setStyleSheet("font-size: 13px; color: #1a2533; background: transparent; border: none;")
        else:
            val.setStyleSheet("font-size: 13px; color: #bdc3c7; font-style: italic; background: transparent; border: none;")

        label_font = QFont("Arial", 10, QFont.Weight.Bold)
        lbl = QLabel(label.upper())
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #95a5a6; background: transparent; border: none;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        lbl.setFixedWidth(100)  # explicit fixed width — never clipped

        # LTR order: value fills the left, label sits on the right
        row_hbox.addWidget(val, 1)
        row_hbox.addWidget(lbl, 0)

        rows.addWidget(row_widget)

    def _refresh_info(self):
        while self._info_layout.count():
            item = self._info_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            c = customer_controller.get_by_id(self._customer_id)
            if not c:
                self._info_layout.addWidget(QLabel("לקוח לא נמצא"))
                self._info_layout.addStretch()
                return

            from database.models import Gender
            GENDER_LABELS = {Gender.MALE: "זכר", Gender.FEMALE: "נקבה", Gender.OTHER: "אחר"}

            # Contact card
            contact_card, contact_grid = self._make_section_card("פרטי קשר")
            phones = [p for p in [c.phone, c.phone2, c.phone3] if p]
            self._add_grid_row(contact_grid, "טלפון", "  |  ".join(phones))
            self._add_grid_row(contact_grid, "אימייל", c.email or "")
            self._add_grid_row(contact_grid, "כתובת", c.address or "")
            self._add_grid_row(contact_grid, "עיר", c.city or "")
            self._info_layout.addWidget(contact_card)

            # Personal card
            personal_card, personal_grid = self._make_section_card("פרטים אישיים")
            dob = c.date_of_birth.strftime("%d/%m/%Y") if c.date_of_birth else ""
            self._add_grid_row(personal_grid, "תאריך לידה", dob)
            self._add_grid_row(personal_grid, "מגדר", GENDER_LABELS.get(c.gender, "") if c.gender else "")
            self._info_layout.addWidget(personal_card)

            # Notes card — scrollable, 1000-word limit
            notes_card = QWidget()
            notes_card.setObjectName("infoCard")
            notes_card.setStyleSheet("""
                QWidget#infoCard {
                    background: white;
                    border: 1px solid #e0e6ed;
                    border-radius: 8px;
                }
            """)
            notes_inner = QVBoxLayout(notes_card)
            notes_inner.setContentsMargins(16, 14, 16, 16)
            notes_inner.setSpacing(10)

            notes_hdr = QLabel("הערות")
            notes_hdr.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #7f8c8d; "
                "letter-spacing: 1px; background: transparent; border: none;"
            )
            notes_inner.addWidget(notes_hdr)

            notes_sep = QFrame()
            notes_sep.setFrameShape(QFrame.Shape.HLine)
            notes_sep.setStyleSheet("background: #e8ecf0; border: none; max-height: 1px;")
            notes_inner.addWidget(notes_sep)

            raw_notes = c.notes or ""
            words = raw_notes.split()
            if len(words) > 1000:
                raw_notes = " ".join(words[:1000]) + "…"

            notes_edit = QTextEdit()
            notes_edit.setReadOnly(True)
            notes_edit.setFixedHeight(80)
            notes_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            notes_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            notes_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            notes_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            color = "#1a2533" if c.notes else "#bdc3c7"
            style = "font-style: italic;" if not c.notes else ""
            notes_edit.setStyleSheet(f"""
                QTextEdit {{
                    font-size: 13px;
                    color: {color};
                    {style}
                    background: #f8f9fa;
                    border: 1px solid #e0e6ed;
                    border-radius: 6px;
                    padding: 8px;
                }}
            """)

            def _resize_notes():
                doc_h = int(notes_edit.document().size().height())
                notes_edit.setFixedHeight(min(300, max(80, doc_h + 20)))

            notes_edit.document().contentsChanged.connect(_resize_notes)
            # Set text after connecting so the signal fires with real dimensions
            notes_edit.setPlainText(raw_notes if raw_notes else "—")
            notes_inner.addWidget(notes_edit)
            self._info_layout.addWidget(notes_card)

        except Exception as e:
            import traceback
            traceback.print_exc()
            err = QLabel(f"שגיאה בטעינת פרטים: {e}")
            err.setStyleSheet("color: #e74c3c; font-size: 13px;")
            err.setWordWrap(True)
            self._info_layout.addWidget(err)

        self._info_layout.addStretch()

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
            self.treatments_table.setRowHeight(i, 46)

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

        def open_menu(checked=False, tid=treatment_id):
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
            self.receipts_table.setCellWidget(i, 4, self._receipt_actions(r.id, r.pdf_path))
            self.receipts_table.setRowHeight(i, 46)

    def _receipt_actions(self, receipt_id: int, pdf_path: str | None = None) -> QWidget:
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

        def open_menu(checked=False, rid=receipt_id, pdf=pdf_path):
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
            if pdf and os.path.isfile(pdf):
                menu.addAction("📄  פתח PDF", lambda: self._open_pdf(pdf))
                menu.addSeparator()
            menu.addAction("✎  עריכה", lambda: self._edit_receipt(rid))
            menu.addSeparator()
            menu.addAction("✕  מחק", lambda: self._delete_receipt(rid))
            menu.exec(QCursor.pos())

        btn.clicked.connect(open_menu)
        row.addWidget(btn)
        return w

    def _open_pdf(self, path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path], check=True)
            else:
                subprocess.run(["xdg-open", path], check=True)
        except Exception as e:
            QMessageBox.critical(self, "שגיאה בפתיחת קובץ", str(e))

    def _add_receipt(self, treatment_id: int | None):
        dlg = AddReceiptDialog(self._customer_id, preselect_treatment_id=treatment_id, customer_name=self._customer_name, parent=self)
        dlg.saved.connect(self._refresh_receipts)
        dlg.exec()

    def _edit_receipt(self, receipt_id: int):
        dlg = AddReceiptDialog(self._customer_id, receipt_id=receipt_id, customer_name=self._customer_name, parent=self)
        dlg.saved.connect(self._refresh_receipts)
        dlg.exec()

    def _delete_receipt(self, receipt_id: int):
        dlg = _ConfirmByTypingDialog(
            title="אישור מחיקת קבלה",
            message="פעולה זו תמחק את הקבלה לצמיתות.<br>כדי לאשר, הקלד <b>כן</b>:",
            expected="כן",
            confirm_label="מחק קבלה",
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                receipt_controller.delete(receipt_id)
                self._refresh_receipts()
            except Exception as e:
                QMessageBox.critical(self, "שגיאה", str(e))

    # ── Contact tab ───────────────────────────────────────────

    def _build_contact_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.addStretch()
        btn_add = QPushButton("+ הוסף יצירת קשר")
        btn_add.clicked.connect(self._add_contact)
        top.addWidget(btn_add)
        layout.addLayout(top)

        self.contact_table = self._make_table(["תאריך", "נושא", "תוכן", "פעולות"])
        self.contact_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.contact_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.contact_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.contact_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.contact_table.setColumnWidth(3, 110)
        layout.addWidget(self.contact_table)
        self._refresh_contacts()
        return widget

    def _refresh_contacts(self):
        logs = contact_controller.get_by_customer(self._customer_id)
        self.contact_table.setRowCount(0)
        for i, log in enumerate(logs):
            self.contact_table.insertRow(i)
            self.contact_table.setItem(i, 0, self._cell(log.date.strftime("%d/%m/%Y")))
            self.contact_table.setItem(i, 1, self._cell(log.subject or ""))
            self.contact_table.setItem(i, 2, self._cell(log.content or ""))
            self.contact_table.setCellWidget(i, 3, self._contact_actions(log.id))
            self.contact_table.setRowHeight(i, 46)

    def _contact_actions(self, log_id: int) -> QWidget:
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

        def open_menu(checked=False, lid=log_id):
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
            menu.addAction("✎  עריכה", lambda: self._edit_contact(lid))
            menu.addSeparator()
            menu.addAction("✕  מחק", lambda: self._delete_contact(lid))
            menu.exec(QCursor.pos())

        btn.clicked.connect(open_menu)
        row.addWidget(btn)
        return w

    def _add_contact(self):
        dlg = AddContactDialog(self._customer_id, parent=self)
        dlg.saved.connect(self._refresh_contacts)
        dlg.exec()

    def _edit_contact(self, log_id: int):
        dlg = AddContactDialog(self._customer_id, log_id=log_id, parent=self)
        dlg.saved.connect(self._refresh_contacts)
        dlg.exec()

    def _delete_contact(self, log_id: int):
        reply = QMessageBox.question(
            self, "אישור מחיקה", "האם למחוק רשומה זו?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                contact_controller.delete(log_id)
                self._refresh_contacts()
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
        t.verticalHeader().setDefaultSectionSize(46)
        return t

    def _cell(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text or "")
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        item.setForeground(QBrush(QColor("#2c3e50")))
        return item


class _ConfirmByTypingDialog(QDialog):
    """Generic confirmation dialog that requires the user to type an exact word."""

    def __init__(self, title: str, message: str, expected: str,
                 confirm_label: str = "אשר", parent=None):
        super().__init__(parent)
        self._expected = expected
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle(title)
        self.setFixedWidth(380)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        hdr = QLabel(f"⚠️  {title}")
        hdr.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        hdr.setStyleSheet("color: #c0392b;")
        layout.addWidget(hdr)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("font-size: 13px; color: #2c3e50;")
        msg_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(msg_label)

        self._input = QLineEdit()
        self._input.setPlaceholderText(f"הקלד: {expected}")
        self._input.setMinimumHeight(36)
        self._input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc; border-radius: 5px;
                padding: 6px 10px; font-size: 13px;
                background: white; color: #2c3e50;
            }
            QLineEdit:focus { border-color: #e74c3c; }
        """)
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("ביטול")
        btn_cancel.setFixedHeight(34)
        btn_cancel.setStyleSheet(
            "background:#ecf0f1; color:#555; border:1px solid #ccc; border-radius:4px; padding: 0 16px;"
        )
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        self._btn_confirm = QPushButton(confirm_label)
        self._btn_confirm.setFixedHeight(34)
        self._btn_confirm.setEnabled(False)
        self._btn_confirm.setStyleSheet("""
            QPushButton {
                background: #e74c3c; color: white;
                border: none; border-radius: 4px;
                font-size: 13px; font-weight: bold; padding: 0 16px;
            }
            QPushButton:hover { background: #c0392b; }
            QPushButton:disabled { background: #f5b7b1; color: white; }
        """)
        self._btn_confirm.clicked.connect(self.accept)
        btn_row.addWidget(self._btn_confirm)

        layout.addLayout(btn_row)

    def _on_text_changed(self, text: str):
        self._btn_confirm.setEnabled(text.strip() == self._expected)


class _DeleteConfirmDialog(_ConfirmByTypingDialog):
    def __init__(self, first_name: str, last_name: str, parent=None):
        super().__init__(
            title="מחיקת לקוח",
            message=(
                f"פעולה זו תמחק לצמיתות את <b>{first_name} {last_name}</b> "
                f"וכל הנתונים המשויכים (טיפולים, קבלות, יצירות קשר).<br><br>"
                f"כדי לאשר, הקלד את השם הפרטי של הלקוח:"
            ),
            expected=first_name,
            confirm_label="מחק לצמיתות",
            parent=parent,
        )
