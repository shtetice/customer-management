import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.settings_service import settings_service


class SettingsScreen(QWidget):

    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(24)

        title = QLabel("הגדרות")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        # ── Section: receipts ──────────────────────────────────
        section = self._section("שמירת קבלות")
        layout.addWidget(section)
        sec_layout = section.layout()

        # Folder path row
        row = QHBoxLayout()
        row.setSpacing(8)

        self._folder_input = QLineEdit()
        self._folder_input.setPlaceholderText("בחר תיקיית שמירה...")
        self._folder_input.setMinimumHeight(36)
        self._folder_input.setReadOnly(True)
        self._folder_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc; border-radius: 5px;
                padding: 7px 10px; font-size: 13px;
                background: #fafafa; color: #2c3e50;
            }
        """)
        saved = settings_service.get("receipts_folder", "")
        if saved:
            self._folder_input.setText(saved)
        row.addWidget(self._folder_input, stretch=1)

        btn_browse = QPushButton("בחר תיקייה")
        btn_browse.setFixedHeight(36)
        btn_browse.setMinimumWidth(110)
        btn_browse.setStyleSheet("""
            QPushButton { background: #3498db; color: white; border: none;
                          border-radius: 5px; font-size: 13px; padding: 0 12px; }
            QPushButton:hover { background: #2980b9; }
        """)
        btn_browse.clicked.connect(self._browse)
        row.addWidget(btn_browse)

        sec_layout.addLayout(row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #27ae60; font-size: 12px;")
        sec_layout.addWidget(self._status_label)

        layout.addStretch()

    def _section(self, title: str) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        lbl = QLabel(title)
        lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #2c3e50; border: none; background: transparent;")
        layout.addWidget(lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #eee; border: none; background: #eee;")
        line.setFixedHeight(1)
        layout.addWidget(line)

        return widget

    def _browse(self):
        current = self._folder_input.text() or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self, "בחר תיקיית שמירה", current)
        if folder:
            settings_service.set("receipts_folder", folder)
            self._folder_input.setText(folder)
            self._status_label.setText("נשמר בהצלחה")
