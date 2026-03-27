from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QCursor

from controllers.appointment_controller import appointment_controller
from controllers.customer_controller import customer_controller
from database.models import AppointmentStatus

# ── Grid constants ────────────────────────────────────────────────────────────
SLOT_H   = 44    # px per 30-min slot
TIME_W   = 56    # px — time label column
DAY_W    = 120   # px per day column
HOUR_START = 7   # 07:00
HOUR_END   = 22  # last slot starts at 21:30
N_SLOTS  = (HOUR_END - HOUR_START) * 2   # 30 slots
GRID_W   = TIME_W + 7 * DAY_W            # 896 px total

# ── Status colours ────────────────────────────────────────────────────────────
_STATUS_STYLE = {
    AppointmentStatus.SCHEDULED: ("#2980b9", "#dbeeff"),
    AppointmentStatus.COMPLETED: ("#1e8449", "#d5f5e3"),
    AppointmentStatus.CANCELLED: ("#7f8c8d", "#eaecee"),
    AppointmentStatus.NO_SHOW:   ("#c0392b", "#fadbd8"),
}

# ── Hebrew day names (index = isoweekday() % 7 → Sun=0 … Sat=6) ──────────────
_HEB_DAYS = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]

_NAV_BTN = """
    QPushButton { background:#ecf0f1; color:#2c3e50; border:1px solid #ccc;
                  border-radius:5px; font-size:13px; }
    QPushButton:hover { background:#d6eaf8; border-color:#3498db; }
"""
_TODAY_BTN = """
    QPushButton { background:#ecf0f1; color:#2c3e50; border:1px solid #ccc;
                  border-radius:5px; font-size:13px; padding:0 12px; }
    QPushButton:hover { background:#d6eaf8; border-color:#3498db; }
"""
_ADD_BTN = """
    QPushButton { background:#3498db; color:white; border:none;
                  border-radius:5px; font-size:13px; padding:0 14px; }
    QPushButton:hover { background:#2980b9; }
"""


def _week_sunday(d: date) -> date:
    """Return the Sunday that starts the week containing *d* (Israeli convention)."""
    return d - timedelta(days=d.isoweekday() % 7)


# ── Appointment card ──────────────────────────────────────────────────────────

class _AppointmentCard(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, appt, customer_name: str, parent=None):
        super().__init__(parent)
        self._appt_id = appt.id
        border_c, bg_c = _STATUS_STYLE.get(appt.status, ("#2980b9", "#dbeeff"))

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg_c};
                border: 2px solid {border_c};
                border-radius: 4px;
            }}
        """)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(4, 3, 4, 2)
        vbox.setSpacing(1)

        time_lbl = QLabel(appt.date.strftime("%H:%M"))
        time_lbl.setStyleSheet(
            f"color:{border_c}; font-size:10px; font-weight:bold; border:none; background:transparent;"
        )
        vbox.addWidget(time_lbl)

        name_lbl = QLabel(customer_name)
        name_lbl.setStyleSheet("color:#2c3e50; font-size:11px; border:none; background:transparent;")
        name_lbl.setWordWrap(True)
        vbox.addWidget(name_lbl)

        if appt.staff_name:
            staff_lbl = QLabel(appt.staff_name)
            staff_lbl.setStyleSheet("color:#7f8c8d; font-size:10px; border:none; background:transparent;")
            vbox.addWidget(staff_lbl)

        vbox.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._appt_id)


# ── Scrollable calendar grid ──────────────────────────────────────────────────

class _CalendarGrid(QWidget):
    slot_clicked        = pyqtSignal(datetime)
    appointment_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._week_start: date = _week_sunday(date.today())
        self._appointments: list = []
        self._customer_names: dict[int, str] = {}
        self._cards: list[_AppointmentCard] = []
        self.setFixedWidth(GRID_W)
        self.setFixedHeight(N_SLOTS * SLOT_H)

    def set_week(self, week_start: date, appointments: list, customer_names: dict):
        self._week_start = week_start
        self._appointments = appointments
        self._customer_names = customer_names
        self._rebuild_cards()
        self.update()

    def _rebuild_cards(self):
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        for appt in self._appointments:
            day_offset = (appt.date.date() - self._week_start).days
            if not (0 <= day_offset < 7):
                continue
            slot = (appt.date.hour - HOUR_START) * 2 + appt.date.minute // 30
            if not (0 <= slot < N_SLOTS):
                continue

            n_slots = max(1, appt.duration_minutes // 30)
            x = TIME_W + day_offset * DAY_W + 2
            y = slot * SLOT_H + 1
            w = DAY_W - 4
            h = n_slots * SLOT_H - 2

            name = self._customer_names.get(appt.customer_id, "לקוח")
            card = _AppointmentCard(appt, name, parent=self)
            card.setGeometry(x, y, w, h)
            card.clicked.connect(self.appointment_clicked.emit)
            card.show()
            self._cards.append(card)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Alternating hour-row backgrounds
        for i in range(N_SLOTS):
            y = i * SLOT_H
            color = QColor("#f8f9fa") if i % 2 == 0 else QColor("#ffffff")
            p.fillRect(TIME_W, y, GRID_W - TIME_W, SLOT_H, color)

        # Horizontal slot lines
        for i in range(N_SLOTS + 1):
            y = i * SLOT_H
            pen = QPen(QColor("#cccccc") if i % 2 == 0 else QColor("#e8e8e8"))
            pen.setWidth(1)
            p.setPen(pen)
            p.drawLine(TIME_W, y, GRID_W, y)

        # Vertical day separators
        p.setPen(QPen(QColor("#cccccc")))
        for d in range(8):
            x = TIME_W + d * DAY_W
            p.drawLine(x, 0, x, N_SLOTS * SLOT_H)

        # Time labels (on the hour only)
        p.setPen(QPen(QColor("#999999")))
        font = p.font()
        font.setPointSize(9)
        p.setFont(font)
        for i in range(0, N_SLOTS, 2):
            hour = HOUR_START + i // 2
            p.drawText(
                0, i * SLOT_H + 3, TIME_W - 6, SLOT_H,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                f"{hour:02d}:00",
            )

        # Current-time indicator
        now = datetime.now()
        if (self._week_start <= now.date() < self._week_start + timedelta(days=7)
                and HOUR_START <= now.hour < HOUR_END):
            day_offset = (now.date() - self._week_start).days
            minutes_from_start = (now.hour - HOUR_START) * 60 + now.minute
            y_now = int(minutes_from_start * SLOT_H / 30)
            x_start = TIME_W + day_offset * DAY_W
            pen = QPen(QColor("#e74c3c"))
            pen.setWidth(2)
            p.setPen(pen)
            p.drawLine(x_start, y_now, x_start + DAY_W, y_now)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x = event.position().x()
        y = event.position().y()
        if x < TIME_W:
            return
        day_idx = int((x - TIME_W) // DAY_W)
        slot_idx = int(y // SLOT_H)
        if not (0 <= day_idx < 7) or not (0 <= slot_idx < N_SLOTS):
            return
        click_date = self._week_start + timedelta(days=day_idx)
        hour = HOUR_START + slot_idx // 2
        minute = 30 if slot_idx % 2 else 0
        self.slot_clicked.emit(
            datetime(click_date.year, click_date.month, click_date.day, hour, minute)
        )


# ── Calendar screen ───────────────────────────────────────────────────────────

class CalendarScreen(QWidget):
    _HEADER_H = 52

    def __init__(self):
        super().__init__()
        self._week_start = _week_sunday(date.today())
        self._build_ui()
        self._load_week()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Top bar ───────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(8)

        lbl = QLabel("לוח תורים")
        lbl.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #2c3e50;")
        top.addWidget(lbl)
        top.addStretch()

        btn_prev = QPushButton("◀")
        btn_prev.setFixedSize(34, 34)
        btn_prev.setStyleSheet(_NAV_BTN)
        btn_prev.clicked.connect(self._prev_week)
        top.addWidget(btn_prev)

        self._week_lbl = QLabel()
        self._week_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._week_lbl.setMinimumWidth(230)
        self._week_lbl.setStyleSheet("font-size: 14px; color: #2c3e50; font-weight: bold;")
        top.addWidget(self._week_lbl)

        btn_next = QPushButton("▶")
        btn_next.setFixedSize(34, 34)
        btn_next.setStyleSheet(_NAV_BTN)
        btn_next.clicked.connect(self._next_week)
        top.addWidget(btn_next)

        btn_today = QPushButton("היום")
        btn_today.setFixedHeight(34)
        btn_today.setStyleSheet(_TODAY_BTN)
        btn_today.clicked.connect(self._go_today)
        top.addWidget(btn_today)

        btn_add = QPushButton("＋ תור חדש")
        btn_add.setFixedHeight(34)
        btn_add.setStyleSheet(_ADD_BTN)
        btn_add.clicked.connect(lambda: self._open_add(None))
        top.addWidget(btn_add)

        layout.addLayout(top)

        # ── Card container (header + scrollable grid) ─────────
        card = QWidget()
        card.setStyleSheet(
            "QWidget { background: white; border: 1px solid #e0e0e0; border-radius: 8px; }"
        )
        card_vbox = QVBoxLayout(card)
        card_vbox.setContentsMargins(0, 0, 0, 0)
        card_vbox.setSpacing(0)

        # Day headers
        header = QWidget()
        header.setFixedHeight(self._HEADER_H)
        header.setStyleSheet(
            "QWidget { background: #eef2f7; border-bottom: 1px solid #dde1e7; border-radius: 0; }"
        )
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(0)

        spacer = QWidget()
        spacer.setFixedWidth(TIME_W)
        spacer.setStyleSheet("background: #eef2f7; border: none;")
        header_row.addWidget(spacer)

        self._day_labels: list[QLabel] = []
        for _ in range(7):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(DAY_W)
            lbl.setStyleSheet("font-size: 12px; color: #2c3e50; font-weight: bold; border: none; background: transparent;")
            header_row.addWidget(lbl)
            self._day_labels.append(lbl)

        card_vbox.addWidget(header)

        # Scrollable grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: white; }")

        self._grid = _CalendarGrid()
        self._grid.slot_clicked.connect(self._open_add)
        self._grid.appointment_clicked.connect(self._open_edit)
        scroll.setWidget(self._grid)

        card_vbox.addWidget(scroll)
        layout.addWidget(card)

    def _update_header(self):
        week_end = self._week_start + timedelta(days=6)
        self._week_lbl.setText(
            f"{self._week_start.strftime('%d/%m')} — {week_end.strftime('%d/%m/%Y')}"
        )
        today = date.today()
        for i, lbl in enumerate(self._day_labels):
            d = self._week_start + timedelta(days=i)
            lbl.setText(f"{_HEB_DAYS[d.isoweekday() % 7]}\n{d.strftime('%d/%m')}")
            if d == today:
                lbl.setStyleSheet(
                    "font-size: 12px; color: #2980b9; font-weight: bold; "
                    "border: none; background: #dbeeff; border-radius: 0;"
                )
            else:
                lbl.setStyleSheet(
                    "font-size: 12px; color: #2c3e50; font-weight: bold; border: none; background: transparent;"
                )

    def _load_week(self):
        ws_dt = datetime(self._week_start.year, self._week_start.month, self._week_start.day)
        appointments = appointment_controller.get_by_week(ws_dt)

        customer_names: dict[int, str] = {}
        for cid in {a.customer_id for a in appointments}:
            c = customer_controller.get_by_id(cid)
            if c:
                customer_names[cid] = f"{c.name} {c.surname}"

        self._grid.set_week(self._week_start, appointments, customer_names)
        self._update_header()

    def _prev_week(self):
        self._week_start -= timedelta(days=7)
        self._load_week()

    def _next_week(self):
        self._week_start += timedelta(days=7)
        self._load_week()

    def _go_today(self):
        self._week_start = _week_sunday(date.today())
        self._load_week()

    def _open_add(self, prefill_dt: datetime | None):
        from ui.screens.add_appointment_dialog import AddAppointmentDialog
        dlg = AddAppointmentDialog(prefill_dt=prefill_dt, parent=self)
        dlg.saved.connect(self._load_week)
        dlg.exec()

    def _open_edit(self, appt_id: int):
        from ui.screens.add_appointment_dialog import AddAppointmentDialog
        dlg = AddAppointmentDialog(appointment_id=appt_id, parent=self)
        dlg.saved.connect(self._load_week)
        dlg.exec()
