"""Shared stylesheet for the application."""

APP_STYLE = """
QMainWindow, QWidget {
    background-color: #f0f2f5;
    color: #1c2333;
    font-family: Arial;
    font-size: 14px;
}

/* Sidebar */
#sidebar {
    background-color: #2c3444;
    min-width: 200px;
    max-width: 200px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #b0b8c8;
    border: none;
    text-align: right;
    padding: 14px 16px;
    font-size: 14px;
    border-radius: 0;
}

#sidebar QPushButton:hover {
    background-color: #3a4358;
}

#sidebar QPushButton[active="true"] {
    background-color: #1e2530;
    border-right: 4px solid #7b96c8;
}

#app_title {
    color: #e8ecf4;
    font-size: 16px;
    font-weight: bold;
    padding: 20px 16px;
    background-color: #1e2530;
}

/* Cards / content area */
#content_area {
    background-color: #f0f2f5;
    border-radius: 8px;
    margin: 16px;
}

/* Buttons */
QPushButton {
    background-color: #5c7ab0;
    color: white;
    border: none;
    padding: 8px 18px;
    border-radius: 4px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #4a6898;
}

QPushButton:pressed {
    background-color: #3a5680;
}

QPushButton#btn_danger {
    background-color: #b03a2e;
}

QPushButton#btn_danger:hover {
    background-color: #962c22;
}

QPushButton#btn_secondary {
    background-color: #8c98ac;
    color: white;
}

QPushButton#btn_secondary:hover {
    background-color: #748090;
}

/* Table */
QTableWidget {
    border: 1px solid #c8cdd8;
    border-radius: 4px;
    gridline-color: #d8dce6;
    background-color: #fafbfc;
    selection-background-color: #c0ccdc;
    selection-color: #1c2333;
}

QTableWidget::item {
    padding: 6px 10px;
    text-align: right;
}

QTableWidget::item:alternate {
    background-color: #f0f2f5;
}

QTableWidget::item:selected {
    background-color: #c0ccdc;
    color: #1c2333;
}

QHeaderView::section {
    background-color: #dde0e8;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #a8b4c8;
    font-weight: bold;
    text-align: right;
    color: #1c2333;
}

/* Inputs */
QLineEdit, QTextEdit, QComboBox {
    border: 1px solid #b0b8c8;
    border-radius: 4px;
    padding: 6px 10px;
    background-color: #fafbfc;
    color: #1c2333;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #5c7ab0;
}

/* Dropdown popup — compact native style */
QComboBox QAbstractItemView {
    background-color: #fafbfc;
    color: #1c2333;
    border: 1px solid #b0b8c8;
    outline: none;
    selection-background-color: #5c7ab0;
    selection-color: #ffffff;
}

QComboBox QAbstractItemView::item {
    padding: 4px 8px;
    min-height: 22px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #5c7ab0;
    color: white;
}

/* Status badges */
QLabel#badge_lead       { color: white; background: #e67e22; padding: 2px 8px; border-radius: 10px; }
QLabel#badge_customer   { color: white; background: #27ae60; padding: 2px 8px; border-radius: 10px; }
QLabel#badge_retention  { color: white; background: #8e44ad; padding: 2px 8px; border-radius: 10px; }
QLabel#badge_vip        { color: white; background: #c0392b; padding: 2px 8px; border-radius: 10px; }

/* Search bar */
QLineEdit#search_bar {
    padding: 8px 14px;
    font-size: 14px;
    border-radius: 20px;
}

/* Link-style button (back / navigation) */
QPushButton#btn_link {
    background: transparent;
    border: none;
    color: #5c7ab0;
    font-size: 13px;
    padding: 0;
    text-align: right;
}

QPushButton#btn_link:hover {
    color: #3a5680;
    text-decoration: underline;
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
