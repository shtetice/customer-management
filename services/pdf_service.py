import os
import platform
import re
from datetime import datetime

from fpdf import FPDF
from bidi.algorithm import get_display
from PIL import Image as _PILImage

from services.settings_service import settings_service

_APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_LOGO_MAX_W = 60   # mm — max logo width
_LOGO_MAX_H = 45   # mm — max logo height
_LABEL_W = 52      # mm  — right column (Hebrew label)
_ROW_H = 8         # mm

_HEB_RE = re.compile(r'[\u0590-\u05FF]')


def _logo_size(path: str) -> tuple[float, float]:
    """Return (w_mm, h_mm) scaled to fit within _LOGO_MAX_W × _LOGO_MAX_H, preserving aspect ratio."""
    try:
        with _PILImage.open(path) as img:
            px_w, px_h = img.size
        if px_w == 0 or px_h == 0:
            return _LOGO_MAX_W, _LOGO_MAX_H
        scale = min(_LOGO_MAX_W / px_w, _LOGO_MAX_H / px_h)
        return px_w * scale, px_h * scale
    except Exception:
        return _LOGO_MAX_W, _LOGO_MAX_H


def _find_font() -> str | None:
    bundled = os.path.join(_APP_ROOT, "assets", "fonts", "NotoSansHebrew.ttf")
    if os.path.exists(bundled):
        return bundled
    if platform.system() == "Darwin":
        for path in [
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ]:
            if os.path.exists(path):
                return path
    elif platform.system() == "Windows":
        windir = os.environ.get("WINDIR", "C:/Windows")
        for name in ["arialu.ttf", "arial.ttf"]:
            path = os.path.join(windir, "Fonts", name)
            if os.path.exists(path):
                return path
    return None


def _rtl(text: str) -> str:
    """Apply bidi for correct RTL visual display in a LTR PDF renderer."""
    return get_display(text) if text else ""


def _rtl_if_hebrew(text: str) -> str:
    """Apply bidi only when the string contains Hebrew characters."""
    return get_display(text) if (_HEB_RE.search(text) and text) else text


def generate_receipt_pdf(
    receipt_id: int,
    date: datetime,
    customer_name: str,
    amount: str,
    description: str,
) -> bytes:
    """
    Generate a receipt PDF and return its bytes.
    Raises RuntimeError if no Hebrew-capable font is found.
    """
    font_path = _find_font()
    if not font_path:
        raise RuntimeError(
            "לא נמצא גופן תומך עברית.\n"
            "הוסף קובץ NotoSansHebrew.ttf לתיקיית assets/fonts/"
        )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("Heb", fname=font_path)

    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    value_w = page_w - _LABEL_W

    # ── Logo ──────────────────────────────────────────────────────────────
    logo_path = settings_service.get("clinic_logo_path", "")
    logo_bottom_y = pdf.t_margin

    if logo_path and os.path.isfile(logo_path):
        logo_w, logo_h = _logo_size(logo_path)
        pdf.image(logo_path, x=pdf.l_margin, y=pdf.t_margin, w=logo_w, h=logo_h)
        logo_bottom_y = pdf.t_margin + logo_h

    pdf.set_y(max(logo_bottom_y, pdf.t_margin) + 4)

    # ── Title ─────────────────────────────────────────────────────────────
    pdf.set_font("Heb", size=20)
    pdf.cell(page_w, 12, _rtl("קבלה"), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # ── Divider ───────────────────────────────────────────────────────────
    pdf.set_draw_color(180, 180, 180)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + page_w, pdf.get_y())
    pdf.ln(5)

    # ── Fields: left cell = value | right cell = Hebrew label ─────────────
    # Keeping label and value in separate cells prevents LTR number reversal
    # in mixed Hebrew+number strings.
    pdf.set_font("Heb", size=12)

    def field_row(label: str, value: str):
        y = pdf.get_y()
        # Value — left column, right-aligned so it sits flush against the label
        pdf.set_xy(pdf.l_margin, y)
        pdf.cell(value_w, _ROW_H, _rtl_if_hebrew(value), align="R")
        # Label — right column, right-aligned, bidi applied
        pdf.set_xy(pdf.l_margin + value_w, y)
        pdf.cell(_LABEL_W, _ROW_H, _rtl(f"{label}:"), align="R",
                 new_x="LMARGIN", new_y="NEXT")

    field_row("מספר קבלה", str(receipt_id))
    field_row("תאריך", date.strftime("%d/%m/%Y"))
    field_row("לקוח", customer_name)
    field_row("סכום", amount)

    if description:
        pdf.ln(2)
        pdf.set_font("Heb", size=11)
        # Description label on its own line
        pdf.set_xy(pdf.l_margin + value_w, pdf.get_y())
        pdf.cell(_LABEL_W, _ROW_H, _rtl("תיאור:"), align="R",
                 new_x="LMARGIN", new_y="NEXT")
        # Description text — full width, right-aligned
        pdf.multi_cell(page_w, 6, _rtl(description), align="R")

    pdf.ln(4)

    # ── Bottom divider ────────────────────────────────────────────────────
    pdf.set_draw_color(180, 180, 180)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + page_w, pdf.get_y())

    return bytes(pdf.output())
