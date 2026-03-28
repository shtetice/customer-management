import os
import shutil
import subprocess
import sys

# Resolve app root so photo paths work regardless of working directory
_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QFrame, QMenu, QScrollArea, QSizePolicy,
    QTextEdit, QDialog, QLineEdit, QFileDialog, QRubberBand
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QFontMetrics, QBrush, QColor, QCursor, QPixmap, QPainter, QPainterPath

from controllers.customer_controller import customer_controller
from controllers.treatment_controller import treatment_controller
from controllers.receipt_controller import receipt_controller
from services.auth_service import auth_service
from ui.screens.add_treatment_screen import AddTreatmentDialog
from ui.confirm_dialog import confirm
from ui.screens.add_receipt_screen import AddReceiptDialog
from ui.screens.add_contact_screen import AddContactDialog
from controllers.contact_controller import contact_controller
from controllers.file_controller import file_controller
from ui.styles import STATUS_LABELS, STATUS_COLORS


class CustomerDetailScreen(QWidget):
    back_requested = pyqtSignal()
    edit_requested = pyqtSignal(int)  # customer_id

    def __init__(self, customer_id: int):
        super().__init__()
        self._customer_id = customer_id
        self._profile_photo_path = ""  # cached after _refresh_summary
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # Header row
        header = QHBoxLayout()
        btn_back = QPushButton("→ חזרה לרשימה")
        btn_back.setObjectName("btn_link")
        btn_back.setStyleSheet("")
        btn_back.clicked.connect(self.back_requested.emit)
        header.addWidget(btn_back)
        header.addStretch()
        layout.addLayout(header)

        # Customer summary card
        self._summary_card = QWidget()
        self._summary_card.setObjectName("summaryCard")
        self._summary_card.setStyleSheet("""
            QWidget#summaryCard {
                border-radius: 10px;
                border: 1px solid #c8cdd8;
            }
        """)
        card_layout = QHBoxLayout(self._summary_card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(20)

        # Avatar circle (clickable)
        self._avatar_label = QLabel()
        self._avatar_label.setFixedSize(56, 56)
        self._avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self._avatar_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._avatar_label.setToolTip("לחץ לשינוי תמונת פרופיל | לחץ קליק ימני להסרה")
        self._avatar_label.mousePressEvent = self._avatar_mouse_press
        card_layout.addWidget(self._avatar_label)

        # Name + status column
        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        name_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._name_label = QLabel()
        self._name_label.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        self._name_label.setStyleSheet("border:none; background:transparent;")
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
        self._phone_label.setStyleSheet("font-size:13px; border:none; background:transparent;")
        contact_col.addWidget(self._phone_label)

        self._email_label = QLabel()
        self._email_label.setStyleSheet("font-size:13px; border:none; background:transparent;")
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
            cid = self._customer_id
            self._card_edit_btn.clicked.connect(lambda: self.edit_requested.emit(cid))
            btn_col.addWidget(self._card_edit_btn)

        if auth_service.has_permission("customers.delete"):
            btn_delete = QPushButton("✕  מחק")
            btn_delete.setFixedHeight(32)
            btn_delete.setMinimumWidth(90)
            btn_delete.setObjectName("btn_danger")
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
            QTabWidget::pane { border:1px solid #c8cdd8; border-radius:4px; }
            QTabBar::tab {
                padding:8px 20px;
                border:1px solid #c8cdd8; border-bottom:none; border-radius:4px 4px 0 0;
                font-size:13px; margin-left:2px;
            }
            QTabBar::tab:selected { font-weight:bold; }
        """)

        self.tabs.addTab(self._build_info_tab(), "פרטי לקוח")
        self.tabs.addTab(self._build_treatments_tab(), "היסטוריית טיפולים")
        self.tabs.addTab(self._build_receipts_tab(), "קבלות")
        self.tabs.addTab(self._build_contact_tab(), "יצירת קשר")
        self.tabs.addTab(self._build_photos_tab(), "תמונות")
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

        # Cache photo path so mouse events don't need a DB round-trip
        self._profile_photo_path = c.profile_photo_path or ""

        # Avatar: photo if available, otherwise initials in a colored circle
        photo_path = self._profile_photo_path
        if photo_path and os.path.isfile(photo_path):
            pixmap = self._make_circular_photo(photo_path, 56)
            self._avatar_label.setPixmap(pixmap)
            self._avatar_label.setText("")
            self._avatar_label.setStyleSheet("border-radius: 28px; border: none; background: transparent;")
        else:
            initials = (c.name[:1] + c.surname[:1]).upper() if c.surname else c.name[:2].upper()
            color_idx = ord(c.name[0].upper()) % len(self._AVATAR_COLORS) if c.name else 0
            avatar_color = self._AVATAR_COLORS[color_idx]
            self._avatar_label.setPixmap(QPixmap())
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

    def _avatar_mouse_press(self, event):
        has_photo = bool(self._profile_photo_path and os.path.isfile(self._profile_photo_path))

        if event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)
            if has_photo:
                menu.addAction("🔍  הגדל תמונה", self._show_photo_enlarged)
            menu.addAction("📷  שנה תמונה", self._pick_profile_photo)
            if has_photo:
                menu.addAction("🗑  הסר תמונה", self._remove_profile_photo)
            menu.exec(QCursor.pos())
        else:
            if has_photo:
                self._show_photo_enlarged()
            else:
                self._pick_profile_photo()

    def _show_photo_enlarged(self):
        if not self._profile_photo_path or not os.path.isfile(self._profile_photo_path):
            return
        dlg = _PhotoViewerDialog(self._profile_photo_path, self._customer_name, parent=self)
        dlg.exec()

    def _pick_profile_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "בחר תמונת פרופיל", "",
            "תמונות (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if not path:
            return
        # Copy to <app_root>/uploads/photos/<customer_id>/
        ext = os.path.splitext(path)[1].lower()
        dest_dir = os.path.join(_APP_ROOT, "uploads", "photos", str(self._customer_id))
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, f"profile{ext}")
        shutil.copy2(path, dest)
        customer_controller.set_profile_photo(self._customer_id, dest)
        self._refresh_summary()

    def _remove_profile_photo(self):
        customer_controller.set_profile_photo(self._customer_id, None)
        self._refresh_summary()

    @staticmethod
    def _make_circular_photo(path: str, size: int) -> QPixmap:
        src = QPixmap(path)
        if src.isNull():
            return QPixmap()
        src = src.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                          Qt.TransformationMode.SmoothTransformation)
        # Crop to square from center
        x = (src.width() - size) // 2
        y = (src.height() - size) // 2
        src = src.copy(x, y, size, size)

        result = QPixmap(size, size)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path_clip = QPainterPath()
        path_clip.addEllipse(0, 0, size, size)
        painter.setClipPath(path_clip)
        painter.drawPixmap(0, 0, src)
        painter.end()
        return result

    # ── Info tab ──────────────────────────────────────────────

    def _build_info_tab(self) -> QWidget:
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        self._info_layout = QVBoxLayout(inner)
        self._info_layout.setSpacing(16)
        self._info_layout.setContentsMargins(20, 16, 20, 20)
        self._refresh_info()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setWidget(inner)
        return scroll

    @staticmethod
    def _make_section_card(title: str) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget()
        card.setObjectName("infoCard")
        card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        card.setStyleSheet("""
            QWidget#infoCard {
                border: 1px solid #c8cdd8;
                border-radius: 8px;
            }
        """)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 14, 16, 16)
        inner.setSpacing(10)

        hdr = QLabel(title)
        hdr.setStyleSheet(
            "font-size: 15px; font-weight: bold; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        inner.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("border: none; max-height: 1px;")
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
        val.setStyleSheet("font-size: 13px; background: transparent; border: none;")

        label_font = QFont("Arial", 10, QFont.Weight.Bold)
        lbl = QLabel(label.upper())
        lbl.setFont(label_font)
        lbl.setStyleSheet("background: transparent; border: none; opacity: 0.6;")
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
            import json
            preferred = []
            if c.preferred_treatments:
                try:
                    preferred = json.loads(c.preferred_treatments)
                except Exception:
                    pass
            self._add_grid_row(personal_grid, "טיפולים מועדפים", "،  ".join(preferred) if preferred else "")
            self._info_layout.addWidget(personal_card)

            # Notes card — scrollable, 1000-word limit
            notes_card = QWidget()
            notes_card.setObjectName("infoCard")
            notes_card.setStyleSheet("""
                QWidget#infoCard {
                    border: 1px solid #c8cdd8;
                    border-radius: 8px;
                }
            """)
            notes_inner = QVBoxLayout(notes_card)
            notes_inner.setContentsMargins(16, 14, 16, 16)
            notes_inner.setSpacing(10)

            notes_hdr = QLabel("הערות")
            notes_hdr.setStyleSheet(
                "font-size: 15px; font-weight: bold; "
                "letter-spacing: 1px; background: transparent; border: none;"
            )
            notes_inner.addWidget(notes_hdr)

            notes_sep = QFrame()
            notes_sep.setFrameShape(QFrame.Shape.HLine)
            notes_sep.setStyleSheet("border: none; max-height: 1px;")
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
            style = "font-style: italic;" if not c.notes else ""
            notes_edit.setStyleSheet(f"""
                QTextEdit {{
                    font-size: 13px;
                    {style}
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

        def open_menu(checked=False, tid=treatment_id):
            menu = QMenu(self)
            menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
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
        if confirm(self, "אישור מחיקה", "האם למחוק טיפול זה? קבלות מקושרות ינותקו.", danger=True):
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

        def open_menu(checked=False, rid=receipt_id, pdf=pdf_path):
            menu = QMenu(self)
            menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
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

        def open_menu(checked=False, lid=log_id):
            menu = QMenu(self)
            menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
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
        if confirm(self, "אישור מחיקה", "האם למחוק רשומה זו?", danger=True):
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

    # ── Photos tab ────────────────────────────────────────────

    def _build_photos_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        lbl = QLabel("תמונות שנשלחו")
        lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        header.addWidget(lbl)
        header.addStretch()
        btn_upload = QPushButton("+ הוסף תמונה")
        btn_upload.setFixedHeight(32)
        btn_upload.clicked.connect(self._upload_photo)
        header.addWidget(btn_upload)
        layout.addLayout(header)

        # Empty state label (shown when no photos)
        self._photos_empty_lbl = QLabel("אין תמונות עדיין.\nלחץ על '+ הוסף תמונה' כדי להעלות.")
        self._photos_empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._photos_empty_lbl.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._photos_empty_lbl, 1)

        # Scroll area with thumbnail grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._photos_container = QWidget()
        self._photos_grid = QGridLayout(self._photos_container)
        self._photos_grid.setSpacing(12)
        self._photos_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._photos_container)
        self._photos_scroll = scroll
        layout.addWidget(scroll, 1)

        self._refresh_photos()
        return widget

    def _refresh_photos(self):
        while self._photos_grid.count():
            item = self._photos_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        photos = file_controller.get_photos(self._customer_id)

        has_photos = bool(photos)
        self._photos_empty_lbl.setVisible(not has_photos)
        self._photos_scroll.setVisible(has_photos)

        if not has_photos:
            return

        cols = 4
        for idx, photo in enumerate(photos):
            cell = self._make_thumbnail(photo)
            self._photos_grid.addWidget(cell, idx // cols, idx % cols)

    def _make_thumbnail(self, photo) -> QWidget:
        cell = QWidget()
        cell.setFixedSize(150, 180)
        cell_layout = QVBoxLayout(cell)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setSpacing(4)

        # Image
        thumb = QLabel()
        thumb.setFixedSize(150, 150)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet("border: 1px solid #c8cdd8; border-radius: 6px; background: #f0f2f5;")
        thumb.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        if os.path.isfile(photo.filepath):
            pix = QPixmap(photo.filepath)
            if not pix.isNull():
                pix = pix.scaled(148, 148, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                thumb.setPixmap(pix)
            else:
                thumb.setText("❌")
        else:
            thumb.setText("קובץ חסר")
            thumb.setStyleSheet(thumb.styleSheet() + "color: #aaa;")

        thumb.mousePressEvent = lambda e, p=photo: self._view_photo(p)
        cell_layout.addWidget(thumb)

        # Filename + action buttons
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(3)
        name_lbl = QLabel(photo.filename)
        name_lbl.setStyleSheet("font-size: 10px; color: #888;")
        name_lbl.setMaximumWidth(86)
        name_lbl.setWordWrap(False)
        name_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        bottom.addWidget(name_lbl, 1)

        btn_save = QPushButton("💾")
        btn_save.setFixedSize(22, 22)
        btn_save.setObjectName("btn_secondary")
        btn_save.setStyleSheet("QPushButton#btn_secondary { font-size: 10px; padding: 0; }")
        btn_save.setToolTip("שמור תמונה")
        btn_save.clicked.connect(lambda checked=False, p=photo: self._save_photo(p))
        bottom.addWidget(btn_save)

        btn_del = QPushButton("✕")
        btn_del.setFixedSize(22, 22)
        btn_del.setObjectName("btn_danger")
        btn_del.setStyleSheet("QPushButton#btn_danger { font-size: 10px; padding: 0; }")
        btn_del.clicked.connect(lambda checked=False, pid=photo.id: self._delete_photo(pid))
        bottom.addWidget(btn_del)
        cell_layout.addLayout(bottom)

        return cell

    def _upload_photo(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "בחר תמונות", "",
            "תמונות (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.heic *.heif)"
        )
        if not paths:
            return
        errors = []
        for path in paths:
            try:
                file_controller.add_photo(self._customer_id, path)
            except Exception as e:
                errors.append(str(e))
        if errors:
            QMessageBox.warning(self, "שגיאה", "\n".join(errors))
        self._refresh_photos()

    def _delete_photo(self, photo_id: int):
        if confirm(self, "מחיקת תמונה", "האם אתה בטוח שברצונך למחוק את התמונה?", danger=True):
            file_controller.delete_photo(photo_id)
            self._refresh_photos()

    def _save_photo(self, photo):
        import shutil
        ext = os.path.splitext(photo.filename)[1] or f".{photo.filetype}"
        dest, _ = QFileDialog.getSaveFileName(
            self, "שמור תמונה", photo.filename,
            f"תמונות (*{ext});;כל הקבצים (*)"
        )
        if not dest:
            return
        try:
            shutil.copy2(photo.filepath, dest)
            QMessageBox.information(self, "נשמר", f"התמונה נשמרה בהצלחה:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", f"לא ניתן לשמור את התמונה:\n{e}")

    def _view_photo(self, photo):
        if not os.path.isfile(photo.filepath):
            QMessageBox.warning(self, "שגיאה", "קובץ התמונה לא נמצא")
            return
        dlg = _PhotoViewerDialog(photo.filepath, photo.filename, parent=self)
        dlg.exec()


class _PhotoViewerDialog(QDialog):
    def __init__(self, filepath: str, filename: str, parent=None):
        super().__init__(parent)
        self._filepath = filepath
        self._filename = filename
        self.setWindowTitle(filename)
        self.setModal(True)
        self.setMinimumSize(400, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(filepath)
        if not pix.isNull():
            screen = self.screen().availableGeometry() if self.screen() else None
            max_w = int(screen.width() * 0.8) if screen else 900
            max_h = int(screen.height() * 0.8) if screen else 700
            if pix.width() > max_w or pix.height() > max_h:
                pix = pix.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.resize(pix.width() + 24, pix.height() + 60)
            img_label.setPixmap(pix)
        else:
            img_label.setText("לא ניתן לטעון את התמונה")

        scroll.setWidget(img_label)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾  שמור תמונה")
        btn_save.setFixedHeight(32)
        btn_save.setObjectName("btn_secondary")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        btn_close = QPushButton("סגור")
        btn_close.setFixedHeight(32)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _save(self):
        import shutil
        ext = os.path.splitext(self._filename)[1] or ".jpg"
        dest, _ = QFileDialog.getSaveFileName(
            self, "שמור תמונה", self._filename,
            f"תמונות (*{ext});;כל הקבצים (*)"
        )
        if not dest:
            return
        try:
            shutil.copy2(self._filepath, dest)
            QMessageBox.information(self, "נשמר", f"התמונה נשמרה בהצלחה:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", f"לא ניתן לשמור את התמונה:\n{e}")


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
        msg_label.setStyleSheet("font-size: 13px;")
        msg_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(msg_label)

        self._input = QLineEdit()
        self._input.setPlaceholderText(f"הקלד: {expected}")
        self._input.setMinimumHeight(36)
        self._input.setStyleSheet("""
            QLineEdit {
                border-radius: 5px;
                padding: 6px 10px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #e74c3c; }
        """)
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("ביטול")
        btn_cancel.setFixedHeight(34)
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.setStyleSheet("")
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


class _PhotoViewerDialog(QDialog):
    """Full-size photo viewer — click anywhere or press Escape to close."""

    def __init__(self, photo_path: str, customer_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(customer_name)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Load and scale image to fit within 600×600 while keeping aspect ratio
        pixmap = QPixmap(photo_path)
        if not pixmap.isNull():
            max_size = 600
            if pixmap.width() > max_size or pixmap.height() > max_size:
                pixmap = pixmap.scaled(
                    max_size, max_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

        img_label = QLabel()
        img_label.setPixmap(pixmap)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(img_label)

        btn_close = QPushButton("סגור")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn_close)
        layout.addLayout(row)

        self.adjustSize()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Only close when clicking the dialog background, not child widgets
        if self.childAt(event.pos()) is None:
            self.accept()
        else:
            super().mousePressEvent(event)

