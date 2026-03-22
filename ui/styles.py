"""Shared stylesheet for the application."""

APP_STYLE = """
QMainWindow, QWidget {
    background-color: #f5f5f5;
    font-family: Arial;
    font-size: 14px;
}

/* Sidebar */
#sidebar {
    background-color: #2c3e50;
    min-width: 200px;
    max-width: 200px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #ecf0f1;
    border: none;
    text-align: right;
    padding: 14px 16px;
    font-size: 14px;
    border-radius: 0;
}

#sidebar QPushButton:hover {
    background-color: #34495e;
}

#sidebar QPushButton[active="true"] {
    background-color: #1a252f;
    border-right: 4px solid #3498db;
}

#app_title {
    color: #ecf0f1;
    font-size: 16px;
    font-weight: bold;
    padding: 20px 16px;
    background-color: #1a252f;
}

/* Cards / content area */
#content_area {
    background-color: #ffffff;
    border-radius: 8px;
    margin: 16px;
}

/* Buttons */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 18px;
    border-radius: 4px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #2471a3;
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
    border: 1px solid #ddd;
    border-radius: 4px;
    gridline-color: #ececec;
    background-color: white;
    selection-background-color: #d6eaf8;
    selection-color: #2c3e50;
}

QTableWidget::item {
    padding: 6px 10px;
    text-align: right;
    color: #2c3e50;
    background-color: white;
}

QTableWidget::item:alternate {
    background-color: #f9f9f9;
}

QTableWidget::item:selected {
    background-color: #d6eaf8;
    color: #2c3e50;
}

QHeaderView::section {
    background-color: #ecf0f1;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #bdc3c7;
    font-weight: bold;
    text-align: right;
}

/* Inputs */
QLineEdit, QTextEdit, QComboBox {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 6px 10px;
    background-color: white;
    color: #2c3e50;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #3498db;
}

/* Dropdown popup — compact native style */
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #b0b8c1;
    outline: none;
    selection-background-color: #3498db;
    selection-color: #ffffff;
}

QComboBox QAbstractItemView::item {
    padding: 4px 8px;
    min-height: 22px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #3498db;
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
    "lead":      "#f39c12",
    "customer":  "#27ae60",
    "retention": "#8e44ad",
    "vip":       "#c0392b",
}

STATUS_LABELS = {
    "lead":      "ליד",
    "customer":  "לקוח",
    "retention": "שימור",
    "vip":       "VIP",
}
