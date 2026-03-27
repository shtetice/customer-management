# Customer Management — CLAUDE.md

## Project Overview
A desktop application for managing customers at a beauty clinic.
- **Platform:** Developed on macOS, compiled to Windows `.exe` via PyInstaller
- **Language:** Python
- **UI Language:** Hebrew (RTL)
- **User communicates in:** English

## Tech Stack
| Layer | Technology |
|---|---|
| GUI | PyQt6 |
| Database | SQLite + SQLAlchemy |
| Auth | bcrypt |
| Compilation | PyInstaller |

## Architecture
```
customer_management/
├── main.py               # Entry point
├── database/             # SQLAlchemy models and DB setup
├── ui/                   # PyQt6 UI screens/widgets
├── controllers/          # Business logic
├── services/             # Auth, file handling, exports
├── uploads/              # Customer files (PDF, DOCX, CSV) — gitignored
└── tests/                # All tests
```

## Data Model

### Customer
| Field | Type |
|---|---|
| id | Integer (PK) |
| name | String |
| surname | String |
| gender | Enum (male/female/other) |
| phone / phone2 / phone3 | String |
| email | String |
| address | String(300) |
| date_of_birth | Date |
| status | Enum (lead/customer/retention/vip) |
| notes | Text |
| treatments | Relationship → Treatment |
| receipts | Relationship → Receipt |
| files | Relationship → CustomerFile |
| created_at | DateTime |
| updated_at | DateTime |

### User Roles
- **Manager** — full access to all data and features
- **User** — access controlled per-feature by Manager via Settings

## Features Planned
- [x] SQLAlchemy models (Customer, User, Feature, UserPermission, Treatment, Receipt, CustomerFile, ActivityLog)
- [x] Database migration system (adds new columns to existing DBs without data loss)
- [x] Customer list screen (filterable by status: Lead/Customer/Retention/VIP)
- [x] Add / Edit / Delete customer (with name, surname, phones ×3, email, gender, status, address, DOB, notes)
- [x] Custom date picker widget (LTR calendar popup with month+year dropdowns, RTL-safe)
- [x] Main window with sidebar navigation
- [x] Login screen with "Remember Me" (24-hour session persistence)
- [x] Customer detail screen
- [x] Treatment history screen
- [x] Add receipt screen
- [x] Role-based permission model (Feature + UserPermission tables seeded)
- [x] User authentication — login/logout fully wired, session persisted via session_service
- [x] User Management screen (Manager creates/edits/deactivates users + permission toggles)
- [x] Activity logging (audit trail — admin-only log viewer, configurable retention, auto-purge)
- [x] Auto-backup on close — password-protected Excel export, skipped if no activity since last backup
- [x] Customer profile photo — clickable avatar circle, circular crop, photo viewer dialog
- [ ] Backup / Export — auto-backup done; manual export not yet implemented
- [ ] Compile to Windows .exe

## Git Workflow
- Commit after every meaningful change using conventional commit format
- Push to GitHub after every commit — no permission needed
- Commit format: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`

## Code Quality Standards
- Write tests for all code (unit + integration where appropriate)
- All code must be production-ready: validate inputs, handle edge cases
- Check for security vulnerabilities proactively
- Notify immediately if corrections are needed

## End of Day Reminder
If the user says anything like "we're done for today", "let's stop here", "that's enough for today" — remind them to run `/end-of-day`.

---

## Session Memory
*Updated at the end of each working session.*

**Last session:** 2026-03-27

**Completed today:**
- **Calendar feature** — fully built (week + month views, drag-and-drop with confirmation, add/edit/delete, search, daily summary dialog, Saturday warning, past-date block, month view height fix)
- **Sidebar logo — circular avatar** — logo scaled to 140×140px, clipped to circle via `QPainterPath`; background sampled from corner pixel of image to fill full circle; `QPainter`/`QPainterPath` imports added to `ui/main_window.py`
- **PDF logo sizing** — `services/pdf_service.py` now uses `_logo_size()` (Pillow-based) for correct aspect-ratio scaling; `_LOGO_MAX_W/H` bumped to 60×45mm

**Key files:**
- `ui/main_window.py` — circular logo rendering (line ~63–90); `closeEvent` always quits (line ~179)
- `ui/screens/calendar_screen.py` — full calendar feature
- `ui/screens/add_appointment_dialog.py` — new/edit appointment dialog with date validation
- `services/pdf_service.py` — `_logo_size()` function (line ~22)

**Next steps (priority order for next session):**
1. **WhatsApp notification integration** — `notification_service.py` is a stub; waiting for Meta API credentials (`whatsapp_token`, `whatsapp_phone_id`) from clinic
2. **Compile to Windows `.exe`** — PyInstaller spec needs `msoffcrypto`, `openpyxl`, `cryptography`, `Pillow`; user is on Mac
3. **Manual export** — auto-backup done; manual CSV/Excel export not yet implemented
4. **Receipt format** — currently PDF (via fpdf2); verify logo renders correctly on Windows

**Open questions / blockers:**
- WhatsApp: waiting on Meta Business API credentials from clinic

**Important context:**
- `app.setQuitOnLastWindowClosed(False)` must stay — without it, closing the login window before the main window appears kills the app prematurely
- `LoginScreen._logging_in = True` must be set before `login_successful.emit()` — otherwise `login.close()` in `on_login()` triggers `closeEvent → app.quit()` mid-login
- `closeEvent` on `MainWindow` always calls `app.quit()` — do NOT add conditional logic back
- `_DatePickerButton` lives in `add_customer_screen.py` and is imported by `add_treatment_screen.py`, `add_receipt_screen.py`, and `add_appointment_dialog.py`
- Global `QTableWidget::item` stylesheet must NOT set `color` or `background-color` — silently overrides item data roles
- Sidebar logo circle: background fill color is sampled from pixel (0,0) of the scaled source — works correctly when logo has a uniform background
- All 74 tests passing
