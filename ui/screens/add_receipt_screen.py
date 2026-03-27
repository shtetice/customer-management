import os
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QMessageBox, QFrame, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from controllers.receipt_controller import receipt_controller
from controllers.treatment_controller import treatment_controller
from services.settings_service import settings_service
from services.pdf_service import generate_receipt_pdf
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


class AddReceiptDialog(QDialog):
    saved = pyqtSignal()

    def __init__(self, customer_id: int, receipt_id: int | None = None,
                 preselect_treatment_id: int | None = None,
                 customer_name: str = "", parent=None):
        super().__init__(parent)
        self._customer_id = customer_id
        self._receipt_id = receipt_id
        self._preselect_treatment_id = preselect_treatment_id
        self._customer_name = customer_name
        self._pdf_source_path: str | None = None   # newly selected PDF from disk
        self._existing_pdf_path: str | None = None  # PDF already saved in DB
        self._clear_pdf = False
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("עריכת קבלה" if receipt_id else "הוספת קבלה")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build_ui()
        if receipt_id:
            self._load(receipt_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("עריכת קבלה" if self._receipt_id else "הוספת קבלה")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # Date
        layout.addWidget(self._lbl("תאריך"))
        self.date_picker = _DatePickerButton()
        self.date_picker.set_date(date.today())
        layout.addWidget(self.date_picker)

        # Amount
        layout.addWidget(self._lbl("סכום *"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("לדוגמה: ₪250")
        self.amount_input.setMinimumHeight(36)
        self.amount_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.amount_input)

        # Description
        layout.addWidget(self._lbl("תיאור"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("פירוט השירות...")
        self.description_input.setFixedHeight(70)
        self.description_input.setStyleSheet(FIELD_STYLE)
        layout.addWidget(self.description_input)

        # Linked treatment
        layout.addWidget(self._lbl("טיפול מקושר (אופציונלי)"))
        self.treatment_combo = QComboBox()
        self.treatment_combo.setMinimumHeight(36)
        self.treatment_combo.setStyleSheet(FIELD_STYLE)
        self.treatment_combo.addItem("ללא קישור לטיפול", None)
        treatments = treatment_controller.get_by_customer(self._customer_id)
        for t in treatments:
            label = f"{t.date.strftime('%d/%m/%Y')} — {t.description}"
            self.treatment_combo.addItem(label, t.id)
        if self._preselect_treatment_id:
            for i in range(self.treatment_combo.count()):
                if self.treatment_combo.itemData(i) == self._preselect_treatment_id:
                    self.treatment_combo.setCurrentIndex(i)
                    break
        layout.addWidget(self.treatment_combo)

        # PDF attachment
        layout.addWidget(self._lbl("קובץ PDF מצורף (אופציונלי)"))

        self._pdf_name_label = QLabel("לא נבחר קובץ")
        self._pdf_name_label.setStyleSheet("font-size: 12px; color: #888;")
        self._pdf_name_label.setWordWrap(True)
        layout.addWidget(self._pdf_name_label)

        pdf_btn_row = QHBoxLayout()
        pdf_btn_row.setSpacing(8)

        btn_pick_pdf = QPushButton("בחר קובץ PDF")
        btn_pick_pdf.setFixedHeight(32)
        btn_pick_pdf.setStyleSheet("""
            QPushButton {
                background: #f0f4f8; color: #2c3e50;
                border: 1px solid #bdc3c7; border-radius: 4px;
                font-size: 12px; padding: 0 10px;
            }
            QPushButton:hover { background: #d6eaf8; border-color: #3498db; }
        """)
        btn_pick_pdf.clicked.connect(self._pick_pdf)
        pdf_btn_row.addWidget(btn_pick_pdf)

        self._btn_clear_pdf = QPushButton("הסר קובץ")
        self._btn_clear_pdf.setFixedHeight(32)
        self._btn_clear_pdf.setStyleSheet("""
            QPushButton {
                background: #fdf2f2; color: #e74c3c;
                border: 1px solid #f5c6c6; border-radius: 4px;
                font-size: 12px; padding: 0 10px;
            }
            QPushButton:hover { background: #fce8e8; border-color: #e74c3c; }
        """)
        self._btn_clear_pdf.setVisible(False)
        self._btn_clear_pdf.clicked.connect(self._clear_pdf_selection)
        pdf_btn_row.addWidget(self._btn_clear_pdf)

        pdf_btn_row.addStretch()
        layout.addLayout(pdf_btn_row)

        # Error
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
        layout.addWidget(self.error_label)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #eee;")
        layout.addWidget(line)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("ביטול")
        btn_cancel.setFixedHeight(34)
        btn_cancel.setStyleSheet("background:#ecf0f1;color:#555;border:1px solid #ccc;border-radius:4px;")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save_file = QPushButton("ייצא קובץ")
        btn_save_file.setFixedHeight(34)
        btn_save_file.setStyleSheet("""
            QPushButton { background:#27ae60; color:white; border:none; border-radius:4px; font-size:13px; padding: 0 12px; }
            QPushButton:hover { background:#219a52; }
        """)
        btn_save_file.clicked.connect(lambda: self._save(export_file=True))
        btn_row.addWidget(btn_save_file)

        btn_save = QPushButton("שמור קבלה")
        btn_save.setFixedHeight(34)
        btn_save.clicked.connect(lambda: self._save(export_file=False))
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(LABEL_STYLE)
        return l

    def _pick_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "בחר קובץ PDF", "", "PDF Files (*.pdf)")
        if path:
            self._pdf_source_path = path
            self._clear_pdf = False
            self._pdf_name_label.setText(os.path.basename(path))
            self._pdf_name_label.setStyleSheet("font-size: 12px; color: #2c3e50;")
            self._btn_clear_pdf.setVisible(True)

    def _clear_pdf_selection(self):
        self._pdf_source_path = None
        self._clear_pdf = True
        self._pdf_name_label.setText("לא נבחר קובץ")
        self._pdf_name_label.setStyleSheet("font-size: 12px; color: #888;")
        self._btn_clear_pdf.setVisible(False)

    def _load(self, receipt_id: int):
        try:
            r = receipt_controller.get_by_id(receipt_id)
            if not r:
                self.reject()
                return
            self.date_picker.set_date(r.date.date() if hasattr(r.date, 'date') else r.date)
            self.amount_input.setText(r.amount or "")
            self.description_input.setPlainText(r.description or "")
            for i in range(self.treatment_combo.count()):
                if self.treatment_combo.itemData(i) == r.treatment_id:
                    self.treatment_combo.setCurrentIndex(i)
                    break
            if r.pdf_path and os.path.isfile(r.pdf_path):
                self._existing_pdf_path = r.pdf_path
                self._pdf_name_label.setText(os.path.basename(r.pdf_path))
                self._pdf_name_label.setStyleSheet("font-size: 12px; color: #2c3e50;")
                self._btn_clear_pdf.setVisible(True)
        except Exception as e:
            QMessageBox.critical(self, "שגיאה בטעינת קבלה", str(e))

    def _save(self, export_file: bool = False):
        d = self.date_picker.get_date()
        if not d:
            self.error_label.setText("יש לבחור תאריך")
            return
        receipt_date = datetime(d.year, d.month, d.day)
        amount = self.amount_input.text().strip()
        description = self.description_input.toPlainText().strip()
        treatment_id = self.treatment_combo.currentData()
        try:
            if self._receipt_id:
                receipt = receipt_controller.update(
                    self._receipt_id, receipt_date, amount, description, treatment_id,
                    pdf_source_path=self._pdf_source_path,
                    clear_pdf=self._clear_pdf,
                )
            else:
                receipt = receipt_controller.create(
                    self._customer_id, receipt_date, amount, description, treatment_id,
                    pdf_source_path=self._pdf_source_path,
                )
            if export_file:
                self._export_file(receipt, receipt_date, amount, description)
            self.saved.emit()
            self.accept()
        except ValueError as e:
            self.error_label.setText(str(e))
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", str(e))

    def _export_file(self, receipt, receipt_date: datetime, amount: str, description: str):
        folder = settings_service.get("receipts_folder", "")
        if not folder or not os.path.isdir(folder):
            folder = QFileDialog.getExistingDirectory(self, "בחר תיקיית שמירה לקבלות")
            if not folder:
                return
            settings_service.set("receipts_folder", folder)

        filename = f"receipt_{receipt.id}_{receipt_date.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(folder, filename)

        try:
            pdf_bytes = generate_receipt_pdf(
                receipt_id=receipt.id,
                date=receipt_date,
                customer_name=self._customer_name,
                amount=amount,
                description=description,
            )
        except RuntimeError as e:
            QMessageBox.critical(self, "שגיאה ביצירת PDF", str(e))
            return

        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        QMessageBox.information(self, "הקובץ נשמר", f"הקובץ נשמר בהצלחה:\n{filepath}")
