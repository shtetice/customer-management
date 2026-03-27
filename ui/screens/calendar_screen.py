import calendar as _cal
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QStackedWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QCursor

from controllers.appointment_controller import appointment_controller
from controllers.customer_controller import customer_controller
from database.models import AppointmentStatus

# ── Week-view grid constants ──────────────────────────────────────────────────
SLOT_H     = 44
TIME_W     = 64    # wider so labels are comfortable
DAY_W      = 118
HOUR_START = 7
HOUR_END   = 22
N_SLOTS    = (HOUR_END - HOUR_START) * 2   # 30 slots
DAYS_W     = 7 * DAY_W                     # total width of day columns
GRID_W     = DAYS_W + TIME_W               # 890 px total

# ── Status colours  (border, background) ─────────────────────────────────────
_STATUS_STYLE = {
    AppointmentStatus.SCHEDULED: ("#2980b9", "#dbeeff"),
    AppointmentStatus.COMPLETED: ("#1e8449", "#d5f5e3"),
    AppointmentStatus.CANCELLED: ("#7f8c8d", "#eaecee"),
    AppointmentStatus.NO_SHOW:   ("#c0392b", "#fadbd8"),
}

_HEB_DAYS   = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
_HEB_MONTHS = [
    "", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
    "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר",
]

# ── Button styles ─────────────────────────────────────────────────────────────
_NAV_BTN = """
    QPushButton { background:#ecf0f1; color:#2c3e50; border:1px solid #ccc;
                  border-radius:5px; font-size:16px; font-weight:bold; }
    QPushButton:hover { background:#d6eaf8; border-color:#3498db; }
"""
_SOFT_BTN = """
    QPushButton { background:#ecf0f1; color:#2c3e50; border:1px solid #ccc;
                  border-radius:5px; font-size:13px; padding:0 12px; }
    QPushButton:hover { background:#d6eaf8; border-color:#3498db; }
"""
_ACTIVE_TOGGLE = """
    QPushButton { background:#3498db; color:white; border:none;
                  border-radius:5px; font-size:13px; padding:0 14px; }
"""
_INACTIVE_TOGGLE = """
    QPushButton { background:#ecf0f1; color:#2c3e50; border:1px solid #ccc;
                  border-radius:5px; font-size:13px; padding:0 14px; }
    QPushButton:hover { background:#d6eaf8; }
"""
_ADD_BTN = """
    QPushButton { background:#27ae60; color:white; border:none;
                  border-radius:5px; font-size:13px; padding:0 14px; }
    QPushButton:hover { background:#219a52; }
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _week_sunday(d: date) -> date:
    """Sunday-based week start (Israeli convention)."""
    return d - timedelta(days=d.isoweekday() % 7)

def _month_grid_start(month_date: date) -> date:
    first = month_date.replace(day=1)
    return first - timedelta(days=first.isoweekday() % 7)

def _month_grid_end(month_date: date) -> date:
    last_day = _cal.monthrange(month_date.year, month_date.month)[1]
    last = month_date.replace(day=last_day)
    days_to_sat = (6 - last.isoweekday() % 7) % 7
    return last + timedelta(days=days_to_sat + 1)


# ─────────────────────────────────────────────────────────────────────────────
# Appointment card  (week view, supports drag)
# ─────────────────────────────────────────────────────────────────────────────

class _AppointmentCard(QFrame):
    clicked    = pyqtSignal(int)
    drag_ended = pyqtSignal(int, int, int)   # appt_id, center_x, center_y (parent coords)

    def __init__(self, appt, customer_name: str, days_w: int, parent=None):
        self._days_w = days_w
        super().__init__(parent)
        self._appt_id   = appt.id
        self._press_pos = None
        self._dragging  = False

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

    # ── Mouse events ──────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.pos()
            self._dragging  = False
        event.accept()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self._press_pos is None:
            return
        if not self._dragging:
            if (event.pos() - self._press_pos).manhattanLength() > 8:
                self._dragging = True
                self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
                self.raise_()
        if self._dragging:
            # Keep press point under cursor
            pos_in_parent = self.mapToParent(event.pos())
            new_x = pos_in_parent.x() - self._press_pos.x()
            new_y = pos_in_parent.y() - self._press_pos.y()
            parent = self.parent()
            if parent:
                new_x = max(0, min(new_x, self._days_w - self.width()))
                new_y = max(0, min(new_y, parent.height() - self.height()))
            self.move(new_x, new_y)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                self._dragging = False
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                center = self.pos() + self.rect().center()
                self.drag_ended.emit(self._appt_id, center.x(), center.y())
            else:
                self.clicked.emit(self._appt_id)
            self._press_pos = None
        event.accept()


# ─────────────────────────────────────────────────────────────────────────────
# Week-view grid
# ─────────────────────────────────────────────────────────────────────────────

class _CalendarGrid(QWidget):
    slot_clicked        = pyqtSignal(datetime)
    appointment_clicked = pyqtSignal(int)
    appointment_dropped = pyqtSignal()       # request parent to reload

    def __init__(self, parent=None):
        super().__init__(parent)
        self._week_start:     date             = _week_sunday(date.today())
        self._appointments:   list             = []
        self._customer_names: dict[int, str]   = {}
        self._cards:          list[_AppointmentCard] = []
        self.setMinimumHeight(N_SLOTS * SLOT_H)
        self.setMaximumHeight(N_SLOTS * SLOT_H)

    @property
    def _day_w(self) -> int:
        return max(60, (self.width() - TIME_W) // 7)

    @property
    def _days_w(self) -> int:
        return self._day_w * 7

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rebuild_cards()
        self.update()

    def set_week(self, week_start: date, appointments: list, customer_names: dict):
        self._week_start      = week_start
        self._appointments    = appointments
        self._customer_names  = customer_names
        self._rebuild_cards()
        self.update()

    # ── Card management ───────────────────────────────────────

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
            dw = self._day_w
            x  = day_offset * dw + 2
            y  = slot * SLOT_H + 1
            w  = dw - 4
            h  = n_slots * SLOT_H - 2

            name = self._customer_names.get(appt.customer_id, "לקוח")
            card = _AppointmentCard(appt, name, days_w=self._days_w, parent=self)
            card.setGeometry(x, y, w, h)
            card.clicked.connect(self.appointment_clicked.emit)
            card.drag_ended.connect(self._on_drag_ended)
            card.show()
            self._cards.append(card)

    def _on_drag_ended(self, appt_id: int, cx: int, cy: int):
        """Called when a card is dropped. cx/cy are center in grid coords."""
        if cx < 0 or cx >= self._days_w:
            self._rebuild_cards()
            return
        day_idx  = int(cx // self._day_w)
        slot_idx = int(cy // SLOT_H)
        if not (0 <= day_idx < 7) or not (0 <= slot_idx < N_SLOTS):
            self._rebuild_cards()
            return

        appt = next((a for a in self._appointments if a.id == appt_id), None)
        if not appt:
            self._rebuild_cards()
            return

        new_date   = self._week_start + timedelta(days=day_idx)
        new_hour   = HOUR_START + slot_idx // 2
        new_minute = 30 if slot_idx % 2 else 0
        new_dt     = datetime(new_date.year, new_date.month, new_date.day, new_hour, new_minute)

        try:
            appointment_controller.update(
                appt_id, new_dt, appt.duration_minutes,
                appt.staff_name or "", appt.notes or "", appt.status,
            )
        except Exception:
            pass

        self.appointment_dropped.emit()

    # ── Painting ──────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        total_h = N_SLOTS * SLOT_H
        dw      = self._day_w
        dsw     = self._days_w
        total_w = self.width()

        # Day area background (alternating rows)
        for i in range(N_SLOTS):
            y     = i * SLOT_H
            color = QColor("#f8f9fb") if i % 2 == 0 else QColor("#ffffff")
            p.fillRect(0, y, dsw, SLOT_H, color)

        # Time column background (right side)
        p.fillRect(dsw, 0, TIME_W, total_h, QColor("#f5f6fa"))

        # Horizontal lines (full width)
        for i in range(N_SLOTS + 1):
            y   = i * SLOT_H
            pen = QPen(QColor("#d0d0d0") if i % 2 == 0 else QColor("#ebebeb"))
            pen.setWidth(1)
            p.setPen(pen)
            p.drawLine(0, y, total_w, y)

        # Vertical day separators
        p.setPen(QPen(QColor("#d0d0d0")))
        for d in range(8):
            p.drawLine(d * dw, 0, d * dw, total_h)

        # Time-column left border
        p.setPen(QPen(QColor("#b0b4bc")))
        p.drawLine(dsw, 0, dsw, total_h)

        # Time labels — match day header: 12px, bold, #2c3e50
        p.setPen(QPen(QColor("#2c3e50")))
        font = p.font()
        font.setPixelSize(12)
        font.setBold(True)
        p.setFont(font)
        for i in range(0, N_SLOTS, 2):
            hour = HOUR_START + i // 2
            y    = i * SLOT_H
            p.drawText(
                dsw + 4, y + 8, TIME_W - 8, SLOT_H,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                f"{hour:02d}:00",
            )

        # Current-time red line
        now = datetime.now()
        if (self._week_start <= now.date() < self._week_start + timedelta(days=7)
                and HOUR_START <= now.hour < HOUR_END):
            day_offset      = (now.date() - self._week_start).days
            mins_from_start = (now.hour - HOUR_START) * 60 + now.minute
            y_now           = int(mins_from_start * SLOT_H / 30)
            x0              = day_offset * dw
            pen = QPen(QColor("#e74c3c"))
            pen.setWidth(2)
            p.setPen(pen)
            p.setBrush(QColor("#e74c3c"))
            p.drawEllipse(x0 - 4, y_now - 4, 8, 8)
            p.drawLine(x0, y_now, x0 + dw, y_now)

    # ── Mouse (clicking empty slots) ──────────────────────────

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x, y = event.position().x(), event.position().y()
        if x >= self._days_w:   # clicked in the time column — ignore
            return
        day_idx  = int(x // self._day_w)
        slot_idx = int(y // SLOT_H)
        if not (0 <= day_idx < 7) or not (0 <= slot_idx < N_SLOTS):
            return
        click_date = self._week_start + timedelta(days=day_idx)
        hour       = HOUR_START + slot_idx // 2
        minute     = 30 if slot_idx % 2 else 0
        self.slot_clicked.emit(
            datetime(click_date.year, click_date.month, click_date.day, hour, minute)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Month view
# ─────────────────────────────────────────────────────────────────────────────

class _MonthView(QWidget):
    appointment_clicked = pyqtSignal(int)
    day_clicked         = pyqtSignal(date)   # click a day → switch to week view

    _CELL_H = 100

    def __init__(self, parent=None):
        super().__init__(parent)
        self._month_date:    date            = date.today().replace(day=1)
        self._appointments:  list            = []
        self._customer_names: dict[int, str] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._cells_widget: QWidget | None = None

    def set_month(self, month_date: date, appointments: list, customer_names: dict):
        self._month_date     = month_date
        self._appointments   = appointments
        self._customer_names = customer_names
        self._rebuild()

    def _rebuild(self):
        if self._cells_widget:
            self._layout.removeWidget(self._cells_widget)
            self._cells_widget.deleteLater()

        container = QWidget()
        container.setStyleSheet("background: white;")
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # Day-name header row
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet("background: #eef2f7; border-bottom: 1px solid #dde1e7;")
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(0)
        for day_name in _HEB_DAYS:
            lbl = QLabel(day_name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50; border: none; background: transparent;")
            header_row.addWidget(lbl)
        vbox.addWidget(header)

        # Build appointment index: date → [appointment, ...]
        appt_map: dict[date, list] = {}
        for a in self._appointments:
            d = a.date.date()
            appt_map.setdefault(d, []).append(a)

        # Calendar grid
        grid_start = _month_grid_start(self._month_date)
        grid_end   = _month_grid_end(self._month_date)
        cur = grid_start
        today = date.today()
        while cur < grid_end:
            week_row = QHBoxLayout()
            week_row.setContentsMargins(0, 0, 0, 0)
            week_row.setSpacing(0)
            for _ in range(7):
                cell = self._make_cell(cur, appt_map.get(cur, []), today)
                week_row.addWidget(cell)
                cur += timedelta(days=1)
            row_widget = QWidget()
            row_widget.setLayout(week_row)
            row_widget.setFixedHeight(self._CELL_H)
            vbox.addWidget(row_widget)

        vbox.addStretch()
        self._cells_widget = container
        self._layout.addWidget(container)

    def _make_cell(self, d: date, appts: list, today: date) -> QFrame:
        is_today    = (d == today)
        is_cur_month = (d.month == self._month_date.month)

        cell = QFrame()
        cell.setFrameShape(QFrame.Shape.Box)
        cell.setStyleSheet(
            "QFrame { border: 1px solid #e0e0e0; background: "
            + ("#fffbf0" if is_today else ("white" if is_cur_month else "#f9f9f9"))
            + "; }"
        )
        cell_layout = QVBoxLayout(cell)
        cell_layout.setContentsMargins(4, 3, 4, 2)
        cell_layout.setSpacing(2)

        # Date number
        date_lbl = QLabel(str(d.day))
        date_style = "font-size: 12px; border: none; background: transparent; "
        if is_today:
            date_style += "color: white; background: #3498db; border-radius: 10px; padding: 1px 5px; font-weight: bold;"
        elif is_cur_month:
            date_style += "color: #2c3e50; font-weight: bold;"
        else:
            date_style += "color: #bbb;"
        date_lbl.setStyleSheet(date_style)
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cell_layout.addWidget(date_lbl)

        # Appointment chips (up to 3)
        shown = appts[:3]
        for appt in shown:
            border_c, bg_c = _STATUS_STYLE.get(appt.status, ("#2980b9", "#dbeeff"))
            name = self._customer_names.get(appt.customer_id, "לקוח")
            text = f"{appt.date.strftime('%H:%M')} {name}"
            chip = QLabel(text)
            chip.setStyleSheet(
                f"background:{bg_c}; color:{border_c}; border:1px solid {border_c}; "
                f"border-radius:3px; font-size:10px; padding:1px 4px;"
            )
            chip.setWordWrap(False)
            # Store appt_id for click
            chip.setProperty("appt_id", appt.id)
            chip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            # We can't easily connect a QLabel click; wrap in QPushButton-style
            cell_layout.addWidget(chip)

        overflow = len(appts) - 3
        if overflow > 0:
            more_lbl = QLabel(f"+{overflow} נוספים")
            more_lbl.setStyleSheet("font-size:10px; color:#888; border:none; background:transparent;")
            cell_layout.addWidget(more_lbl)

        cell_layout.addStretch()

        # Make cell clickable for day navigation
        cell.mousePressEvent = lambda e, _d=d: self.day_clicked.emit(_d)

        # Connect chip clicks via event filter on chips
        for i in range(cell_layout.count()):
            item = cell_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                aid = w.property("appt_id")
                if aid is not None:
                    w.mousePressEvent = lambda e, _id=aid: (
                        e.accept(),
                        self.appointment_clicked.emit(_id),
                    )
        return cell


# ─────────────────────────────────────────────────────────────────────────────
# Main calendar screen
# ─────────────────────────────────────────────────────────────────────────────

class CalendarScreen(QWidget):
    _HEADER_H = 52

    def __init__(self):
        super().__init__()
        self._view_mode  = "week"
        self._week_start = _week_sunday(date.today())
        self._month_date = date.today().replace(day=1)
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Top bar ───────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(8)

        title = QLabel("לוח תורים")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50;")
        top.addWidget(title)
        top.addStretch()

        # View toggle
        self._btn_week = QPushButton("שבועי")
        self._btn_week.setFixedHeight(34)
        self._btn_week.setStyleSheet(_ACTIVE_TOGGLE)
        self._btn_week.clicked.connect(lambda: self._set_view("week"))
        top.addWidget(self._btn_week)

        self._btn_month = QPushButton("חודשי")
        self._btn_month.setFixedHeight(34)
        self._btn_month.setStyleSheet(_INACTIVE_TOGGLE)
        self._btn_month.clicked.connect(lambda: self._set_view("month"))
        top.addWidget(self._btn_month)

        top.addSpacing(8)

        # Navigation
        self._btn_prev = QPushButton("<")
        self._btn_prev.setFixedSize(36, 34)
        self._btn_prev.setStyleSheet(_NAV_BTN)
        self._btn_prev.clicked.connect(self._prev_period)
        top.addWidget(self._btn_prev)

        self._period_lbl = QLabel()
        self._period_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._period_lbl.setMinimumWidth(240)
        self._period_lbl.setStyleSheet("font-size: 14px; color: #2c3e50; font-weight: bold;")
        top.addWidget(self._period_lbl)

        self._btn_next = QPushButton(">")
        self._btn_next.setFixedSize(36, 34)
        self._btn_next.setStyleSheet(_NAV_BTN)
        self._btn_next.clicked.connect(self._next_period)
        top.addWidget(self._btn_next)

        btn_today = QPushButton("היום")
        btn_today.setFixedHeight(34)
        btn_today.setStyleSheet(_SOFT_BTN)
        btn_today.clicked.connect(self._go_today)
        top.addWidget(btn_today)

        btn_add = QPushButton("＋ תור חדש")
        btn_add.setFixedHeight(34)
        btn_add.setStyleSheet(_ADD_BTN)
        btn_add.clicked.connect(lambda: self._open_add(None))
        top.addWidget(btn_add)

        layout.addLayout(top)

        # ── Content card (header + stacked views) ─────────────
        card = QWidget()
        card.setStyleSheet(
            "QWidget { background: white; border: 1px solid #e0e0e0; border-radius: 8px; }"
        )
        card_vbox = QVBoxLayout(card)
        card_vbox.setContentsMargins(0, 0, 0, 0)
        card_vbox.setSpacing(0)

        # ── Week view: fixed day headers + scrollable grid ─────
        self._week_widget = QWidget()
        self._week_widget.setStyleSheet("QWidget { border: none; }")
        week_vbox = QVBoxLayout(self._week_widget)
        week_vbox.setContentsMargins(0, 0, 0, 0)
        week_vbox.setSpacing(0)

        week_header = QWidget()
        week_header.setFixedHeight(self._HEADER_H)
        week_header.setStyleSheet(
            "QWidget { background: #eef2f7; border-bottom: 1px solid #dde1e7; border-radius: 0; }"
        )
        wh_row = QHBoxLayout(week_header)
        wh_row.setContentsMargins(0, 0, 0, 0)
        wh_row.setSpacing(0)

        self._day_labels: list[QLabel] = []
        for _ in range(7):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                "font-size: 12px; color: #2c3e50; font-weight: bold; border: none; background: transparent;"
            )
            wh_row.addWidget(lbl, 1)   # stretch=1 → equal width, fills dynamically
            self._day_labels.append(lbl)

        time_spacer = QWidget()
        time_spacer.setFixedWidth(TIME_W)
        time_spacer.setStyleSheet("background: #eef2f7; border: none;")
        wh_row.addWidget(time_spacer, 0)   # fixed width, no stretch

        week_vbox.addWidget(week_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)   # grid fills available width automatically
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: white; }")

        self._grid = _CalendarGrid()
        self._grid.slot_clicked.connect(self._open_add)
        self._grid.appointment_clicked.connect(self._open_edit)
        self._grid.appointment_dropped.connect(self._load_current)
        scroll.setWidget(self._grid)

        week_vbox.addWidget(scroll)

        # ── Month view ────────────────────────────────────────
        month_scroll = QScrollArea()
        month_scroll.setWidgetResizable(True)
        month_scroll.setFrameShape(QFrame.Shape.NoFrame)
        month_scroll.setStyleSheet("QScrollArea { border: none; background: white; }")

        self._month_view = _MonthView()
        self._month_view.appointment_clicked.connect(self._open_edit)
        self._month_view.day_clicked.connect(self._jump_to_week)
        month_scroll.setWidget(self._month_view)

        # ── Stack ─────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QStackedWidget { border: none; }")
        self._stack.addWidget(self._week_widget)    # index 0
        self._stack.addWidget(month_scroll)          # index 1

        card_vbox.addWidget(self._stack)
        layout.addWidget(card)

    # ── View toggle ───────────────────────────────────────────

    def _set_view(self, mode: str):
        self._view_mode = mode
        self._btn_week.setStyleSheet(_ACTIVE_TOGGLE if mode == "week" else _INACTIVE_TOGGLE)
        self._btn_month.setStyleSheet(_ACTIVE_TOGGLE if mode == "month" else _INACTIVE_TOGGLE)
        self._stack.setCurrentIndex(0 if mode == "week" else 1)
        self._load_current()

    # ── Navigation ────────────────────────────────────────────

    def _prev_period(self):
        if self._view_mode == "week":
            self._week_start -= timedelta(days=7)
        else:
            first = self._month_date.replace(day=1)
            self._month_date = (first - timedelta(days=1)).replace(day=1)
        self._load_current()

    def _next_period(self):
        if self._view_mode == "week":
            self._week_start += timedelta(days=7)
        else:
            last = self._month_date.replace(day=28)
            self._month_date = (last + timedelta(days=4)).replace(day=1)
        self._load_current()

    def _go_today(self):
        self._week_start = _week_sunday(date.today())
        self._month_date = date.today().replace(day=1)
        self._load_current()

    def _jump_to_week(self, d: date):
        self._week_start = _week_sunday(d)
        self._set_view("week")

    # ── Data loading ──────────────────────────────────────────

    def _load_current(self):
        if self._view_mode == "week":
            self._load_week()
        else:
            self._load_month()

    def _load_week(self):
        ws_dt = datetime(self._week_start.year, self._week_start.month, self._week_start.day)
        appointments = appointment_controller.get_by_week(ws_dt)
        customer_names = self._fetch_customer_names(appointments)
        self._grid.set_week(self._week_start, appointments, customer_names)
        self._update_day_headers()
        we = self._week_start + timedelta(days=6)
        self._period_lbl.setText(
            f"{self._week_start.strftime('%d/%m')} — {we.strftime('%d/%m/%Y')}"
        )

    def _load_month(self):
        gs = _month_grid_start(self._month_date)
        ge = _month_grid_end(self._month_date)
        gs_dt = datetime(gs.year, gs.month, gs.day)
        ge_dt = datetime(ge.year, ge.month, ge.day)
        appointments = appointment_controller.get_by_date_range(gs_dt, ge_dt)
        customer_names = self._fetch_customer_names(appointments)
        self._month_view.set_month(self._month_date, appointments, customer_names)
        self._period_lbl.setText(
            f"{_HEB_MONTHS[self._month_date.month]} {self._month_date.year}"
        )

    def _fetch_customer_names(self, appointments: list) -> dict[int, str]:
        names: dict[int, str] = {}
        for cid in {a.customer_id for a in appointments}:
            c = customer_controller.get_by_id(cid)
            if c:
                names[cid] = f"{c.name} {c.surname}"
        return names

    def _update_day_headers(self):
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
                    "font-size: 12px; color: #2c3e50; font-weight: bold; "
                    "border: none; background: transparent;"
                )

    # ── Dialogs ───────────────────────────────────────────────

    def _open_add(self, prefill_dt: datetime | None):
        from ui.screens.add_appointment_dialog import AddAppointmentDialog
        dlg = AddAppointmentDialog(prefill_dt=prefill_dt, parent=self)
        dlg.saved.connect(self._load_current)
        dlg.exec()

    def _open_edit(self, appt_id: int):
        from ui.screens.add_appointment_dialog import AddAppointmentDialog
        dlg = AddAppointmentDialog(appointment_id=appt_id, parent=self)
        dlg.saved.connect(self._load_current)
        dlg.exec()
