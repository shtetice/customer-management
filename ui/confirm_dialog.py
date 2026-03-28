"""Shared Hebrew confirmation dialog — replaces QMessageBox.question Yes/No throughout the app."""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

_BTN_CANCEL = """
    QPushButton { background:#ecf0f1; color:#555; border:1px solid #ccc;
                  border-radius:4px; font-size:13px; padding:0 14px; min-height:32px; }
    QPushButton:hover { background:#dde1e5; }
"""
_BTN_CONFIRM = """
    QPushButton { background:#3498db; color:white; border:none;
                  border-radius:4px; font-size:13px; padding:0 14px; min-height:32px; }
    QPushButton:hover { background:#2980b9; }
"""
_BTN_DANGER = """
    QPushButton { background:#e74c3c; color:white; border:none;
                  border-radius:4px; font-size:13px; padding:0 14px; min-height:32px; }
    QPushButton:hover { background:#c0392b; }
"""


def confirm(parent, title: str, message: str, danger: bool = False) -> bool:
    """
    Show a Hebrew confirmation dialog.
    Returns True if the user clicked אישור, False if ביטול.
    Uses a custom QDialog (not QMessageBox) to avoid RTL rendering issues on macOS.
    """
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    dlg.setMinimumWidth(320)

    vl = QVBoxLayout(dlg)
    vl.setContentsMargins(20, 18, 20, 16)
    vl.setSpacing(16)

    lbl = QLabel(f"<div dir='rtl' style='font-size:13px;'>{message}</div>")
    lbl.setWordWrap(True)
    vl.addWidget(lbl)

    br = QHBoxLayout()
    br.setSpacing(8)

    btn_cancel = QPushButton("ביטול")
    btn_cancel.setStyleSheet(_BTN_CANCEL)
    btn_cancel.clicked.connect(dlg.reject)

    btn_ok = QPushButton("אישור")
    btn_ok.setStyleSheet(_BTN_DANGER if danger else _BTN_CONFIRM)
    btn_ok.clicked.connect(dlg.accept)
    btn_ok.setDefault(True)

    br.addStretch()
    br.addWidget(btn_cancel)
    br.addWidget(btn_ok)
    vl.addLayout(br)

    return dlg.exec() == QDialog.DialogCode.Accepted
