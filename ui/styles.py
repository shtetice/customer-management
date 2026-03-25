"""Shared stylesheet for the application."""

APP_STYLE = """
QMainWindow, QWidget {
    background-color: #dce8f5;
    color: #1a2e45;
    font-family: Arial;
    font-size: 14px;
}

/* Sidebar */
#sidebar {
    background-color: #1e3a5f;
    min-width: 200px;
    max-width: 200px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #c8d8eb;
    border: none;
    text-align: right;
    padding: 14px 16px;
    font-size: 14px;
    border-radius: 0;
}

#sidebar QPushButton:hover {
    background-color: #2a4f7c;
}

#sidebar QPushButton[active="true"] {
    background-color: #163152;
    border-right: 4px solid #5ba3d9;
}

#app_title {
    color: #e8f0f9;
    font-size: 16px;
    font-weight: bold;
    padding: 20px 16px;
    background-color: #163152;
}

/* Cards / content area */
#content_area {
    background-color: #dce8f5;
    border-radius: 8px;
    margin: 16px;
}

/* Buttons */
QPushButton {
    background-color: #2e86c1;
    color: white;
    border: none;
    padding: 8px 18px;
    border-radius: 4px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #2471a3;
}

QPushButton:pressed {
    background-color: #1a5e8a;
}

QPushButton#btn_danger {
    background-color: #e74c3c;
}

QPushButton#btn_danger:hover {
    background-color: #c0392b;
}

QPushButton#btn_secondary {
    background-color: #95a5a6;
}

QPushButton#btn_secondary:hover {
    background-color: #7f8c8d;
}

/* Table */
QTableWidget {
    border: 1px solid #b8cfe8;
    border-radius: 4px;
    gridline-color: #ccddf0;
    background-color: #eaf2fb;
    selection-background-color: #aed6f1;
    selection-color: #1a2e45;
}

QTableWidget::item {
    padding: 6px 10px;
    text-align: right;
}

QTableWidget::item:alternate {
    background-color: #dce8f5;
}

QTableWidget::item:selected {
    background-color: #aed6f1;
    color: #1a2e45;
}

QHeaderView::section {
    background-color: #c5daf0;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #8db8e0;
    font-weight: bold;
    text-align: right;
    color: #1a2e45;
}

/* Inputs */
QLineEdit, QTextEdit, QComboBox {
    border: 1px solid #a0bcd8;
    border-radius: 4px;
    padding: 6px 10px;
    background-color: #f0f7ff;
    color: #1a2e45;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #2e86c1;
}

/* Dropdown popup — compact native style */
QComboBox QAbstractItemView {
    background-color: #f0f7ff;
    color: #1a2e45;
    border: 1px solid #a0bcd8;
    outline: none;
    selection-background-color: #2e86c1;
    selection-color: #ffffff;
}

QComboBox QAbstractItemView::item {
    padding: 4px 8px;
    min-height: 22px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #2e86c1;
    color: white;
}

/* Status badges */
QLabel#badge_lead       { color: white; background: #f39c12; padding: 2px 8px; border-radius: 10px; }
QLabel#badge_customer   { color: white; background: #27ae60; padding: 2px 8px; border-radius: 10px; }
QLabel#badge_retention  { color: white; background: #8e44ad; padding: 2px 8px; border-radius: 10px; }
QLabel#badge_vip        { color: white; background: #c0392b; padding: 2px 8px; border-radius: 10px; }

/* Search bar */
QLineEdit#search_bar {
    padding: 8px 14px;
    font-size: 14px;
    border-radius: 20px;
}
"""

STATUS_COLORS = {
    "lead":      "#e67e22",
    "customer":  "#27ae60",
    "retention": "#8e44ad",
    "vip":       "#c0392b",
}

STATUS_BG_COLORS = {
    "lead":      "#fef0e0",
    "customer":  "#e9f7ef",
    "retention": "#f4ecf7",
    "vip":       "#fdedec",
}

STATUS_LABELS = {
    "lead":      "ליד",
    "customer":  "לקוח",
    "retention": "שימור",
    "vip":       "VIP",
}
