from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QLineEdit, QComboBox, QCheckBox, QFormLayout,
    QMessageBox, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QBrush, QColor

from database.models import UserRole
from services.auth_service import auth_service
from database.db import DEFAULT_FEATURES
from ui.screens.customer_detail_screen import _ConfirmByTypingDialog


ROLE_LABELS = {
    UserRole.MANAGER: "מנהל",
    UserRole.USER: "משתמש",
}

# Features that only managers can use — no point showing them as toggleable
_MANAGER_ONLY = {"users.manage"}


class UserManagementScreen(QWidget):
    COLUMNS = ["שם משתמש", "שם מלא", "תפקיד", "סטטוס", "פעולות"]

    def __init__(self):
        super().__init__()
        self.setObjectName("userMgmtScreen")
        self.setStyleSheet("#userMgmtScreen { background-color: #f0f2f5; }")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("ניהול משתמשים")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        btn_add = QPushButton("+ הוסף משתמש")
        btn_add.setFixedHeight(34)
        btn_add.clicked.connect(self._add_user)
        header.addWidget(btn_add)
        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 240)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(46)
        layout.addWidget(self.table)

        self._refresh()

    def _refresh(self):
        self.table.setRowCount(0)
        users = auth_service.get_all_users()
        current_id = auth_service.current_user.id if auth_service.current_user else None

        for row_idx, user in enumerate(users):
            self.table.insertRow(row_idx)

            self.table.setItem(row_idx, 0, self._cell(user.username))
            self.table.setItem(row_idx, 1, self._cell(user.full_name or ""))
            self.table.setItem(row_idx, 2, self._cell(ROLE_LABELS.get(user.role, "")))

            status_item = QTableWidgetItem("פעיל" if user.is_active else "מושבת")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter)
            if user.is_active:
                status_item.setForeground(QBrush(QColor("#27ae60")))
            else:
                status_item.setForeground(QBrush(QColor("#e74c3c")))
            self.table.setItem(row_idx, 3, status_item)

            # Actions widget
            actions_w = QWidget()
            actions_l = QHBoxLayout(actions_w)
            actions_l.setContentsMargins(6, 4, 6, 4)
            actions_l.setSpacing(6)
            actions_l.addStretch()

            btn_edit = QPushButton("עריכה")
            btn_edit.setFixedHeight(28)
            btn_edit.clicked.connect(lambda checked=False, uid=user.id: self._edit_user(uid))
            actions_l.addWidget(btn_edit)

            # Can't deactivate or delete yourself
            if user.id != current_id:
                btn_toggle = QPushButton("השבת" if user.is_active else "הפעל")
                btn_toggle.setFixedHeight(28)
                if user.is_active:
                    btn_toggle.setObjectName("btn_danger")
                else:
                    btn_toggle.setObjectName("btn_secondary")
                btn_toggle.clicked.connect(lambda checked=False, uid=user.id, active=user.is_active: self._toggle_active(uid, active))
                actions_l.addWidget(btn_toggle)

                btn_delete = QPushButton("מחק")
                btn_delete.setFixedHeight(28)
                btn_delete.setObjectName("btn_danger")
                btn_delete.clicked.connect(lambda checked=False, uid=user.id, uname=user.username: self._delete_user(uid, uname))
                actions_l.addWidget(btn_delete)

            self.table.setCellWidget(row_idx, 4, actions_w)
            self.table.setRowHeight(row_idx, 46)

    def _cell(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute | Qt.AlignmentFlag.AlignVCenter)
        return item

    def _add_user(self):
        dlg = UserDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                user = auth_service.create_user(
                    username=data["username"],
                    password=data["password"],
                    full_name=data["full_name"],
                    role=data["role"],
                )
                # Set permissions
                for key, allowed in data["permissions"].items():
                    auth_service.set_permission(user.id, key, allowed)
                self._refresh()
            except ValueError as e:
                QMessageBox.warning(self, "שגיאה", str(e))

    def _edit_user(self, user_id: int):
        user = auth_service.get_user_by_id(user_id)
        if not user:
            return
        perms = auth_service.get_user_permissions(user_id)
        dlg = UserDialog(user=user, permissions=perms, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                auth_service.update_user(
                    user_id=user_id,
                    full_name=data["full_name"],
                    role=data["role"],
                    is_active=data["is_active"],
                )
                if data.get("password"):
                    auth_service.reset_password(user_id, data["password"])
                for key, allowed in data["permissions"].items():
                    auth_service.set_permission(user_id, key, allowed)
                self._refresh()
            except ValueError as e:
                QMessageBox.warning(self, "שגיאה", str(e))

    def _delete_user(self, user_id: int, username: str):
        dlg = _ConfirmByTypingDialog(
            title="מחיקת משתמש",
            message=(
                f"פעולה זו תמחק לצמיתות את המשתמש <b>{username}</b>.<br><br>"
                f"כדי לאשר, הקלד את שם המשתמש:"
            ),
            expected=username,
            confirm_label="מחק לצמיתות",
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                auth_service.delete_user(user_id)
                self._refresh()
            except ValueError as e:
                QMessageBox.warning(self, "שגיאה", str(e))

    def _toggle_active(self, user_id: int, currently_active: bool):
        user = auth_service.get_user_by_id(user_id)
        if not user:
            return
        action = "להשבית" if currently_active else "להפעיל"
        reply = QMessageBox.question(
            self, "אישור",
            f"האם אתה בטוח שברצונך {action} את המשתמש {user.username}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            auth_service.update_user(user_id, user.full_name or "", user.role, not currently_active)
            self._refresh()


class UserDialog(QDialog):
    def __init__(self, user=None, permissions: dict[str, bool] | None = None, parent=None):
        super().__init__(parent)
        self._user = user
        self._perm_checks: dict[str, QCheckBox] = {}
        self.setWindowTitle("עריכת משתמש" if user else "הוספת משתמש")
        self.setFixedWidth(460)
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui(permissions or {})

    def _build_ui(self, perms: dict[str, bool]):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("עריכת משתמש" if self._user else "הוספת משתמש חדש")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Username
        self._username = QLineEdit()
        if self._user:
            self._username.setText(self._user.username)
            self._username.setReadOnly(True)
            self._username.setStyleSheet("QLineEdit { color: #888; }")
        form.addRow("שם משתמש:", self._username)

        # Full name
        self._full_name = QLineEdit()
        if self._user:
            self._full_name.setText(self._user.full_name or "")
        form.addRow("שם מלא:", self._full_name)

        # Password
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("השאר ריק לאי-שינוי" if self._user else "סיסמה")
        form.addRow("סיסמה:" if not self._user else "סיסמה חדשה:", self._password)

        # Role
        self._role = QComboBox()
        self._role.addItem("משתמש", UserRole.USER)
        self._role.addItem("מנהל", UserRole.MANAGER)
        if self._user:
            idx = self._role.findData(self._user.role)
            if idx >= 0:
                self._role.setCurrentIndex(idx)
        self._role.currentIndexChanged.connect(self._on_role_changed)
        form.addRow("תפקיד:", self._role)

        # Active toggle (edit only)
        if self._user:
            self._is_active = QCheckBox("משתמש פעיל")
            self._is_active.setChecked(self._user.is_active)
            form.addRow("סטטוס:", self._is_active)

        layout.addLayout(form)

        # Permissions section (only for USER role)
        self._perm_group = QGroupBox("הרשאות")
        self._perm_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        perm_layout = QVBoxLayout(self._perm_group)
        perm_layout.setSpacing(6)

        for key, label, _ in DEFAULT_FEATURES:
            if key in _MANAGER_ONLY:
                continue
            cb = QCheckBox(label)
            cb.setChecked(perms.get(key, False))
            perm_layout.addWidget(cb)
            self._perm_checks[key] = cb

        scroll = QScrollArea()
        scroll.setWidget(self._perm_group)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(220)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        layout.addWidget(scroll)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("ביטול")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_save = QPushButton("שמור")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        self._on_role_changed()

    def _on_role_changed(self):
        is_user_role = self._role.currentData() == UserRole.USER
        self._perm_group.setVisible(is_user_role)

    def _save(self):
        username = self._username.text().strip()
        full_name = self._full_name.text().strip()
        password = self._password.text()

        if not self._user and not username:
            QMessageBox.warning(self, "שגיאה", "שם משתמש הוא שדה חובה")
            return
        if not self._user and not password:
            QMessageBox.warning(self, "שגיאה", "סיסמה היא שדה חובה למשתמש חדש")
            return

        self.accept()

    def get_data(self) -> dict:
        return {
            "username": self._username.text().strip(),
            "full_name": self._full_name.text().strip(),
            "password": self._password.text(),
            "role": self._role.currentData(),
            "is_active": self._is_active.isChecked() if self._user else True,
            "permissions": {key: cb.isChecked() for key, cb in self._perm_checks.items()},
        }
