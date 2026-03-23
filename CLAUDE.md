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
- [x] SQLAlchemy models (Customer, User, Feature, UserPermission, Treatment, Receipt, CustomerFile)
- [x] Database migration system (adds new columns to existing DBs without data loss)
- [x] Customer list screen (filterable by status: Lead/Customer/Retention/VIP)
- [x] Add / Edit / Delete customer (with name, surname, phones ×3, email, gender, status, address, DOB, notes)
- [x] Custom date picker widget (LTR calendar popup with month+year dropdowns, RTL-safe)
- [x] Main window with sidebar navigation
- [x] Login screen
- [x] Customer detail screen
- [x] Treatment history screen
- [x] Add receipt screen
- [x] Role-based permission model (Feature + UserPermission tables seeded)
- [ ] User authentication (login/logout — UI exists, backend not wired up)
- [ ] User management screen (Manager creates/manages users)
- [ ] Role-based permissions UI (Manager configures per-feature access)
- [ ] Backup / Export
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

**Last session:** 2026-03-23

**Completed today:**
- Fixed login button invisible — card's `QWidget { background: white }` was overriding global QPushButton style (`ui/screens/login_screen.py`)
- Status badges redesigned: bold colored `● text` items with per-status background tint instead of QLabel cell-widgets (`ui/screens/customer_list_screen.py`, `ui/styles.py`)
  - Fixed root cause: removed `color`/`background-color` from `QTableWidget::item` in global stylesheet — these were silently overriding item data roles
- Added `STATUS_BG_COLORS` dict to `ui/styles.py` (pastel tints per status)
- Created `services/settings_service.py` — reads/writes `settings.json` at project root
- Created `ui/screens/settings_screen.py` — settings UI with receipts folder picker
- Added ⚙️ הגדרות nav button to sidebar (`ui/main_window.py`)
- Receipt dialog (`ui/screens/add_receipt_screen.py`):
  - Replaced `QDateEdit` with custom `_DatePickerButton`
  - Added `customer_name` param
  - Added green "שמור + ייצא קובץ" button — saves `.txt` receipt to configured folder
- Calendar popup: added `WindowStaysOnTopHint` so it renders above modal dialogs
- Status badge min-width fix (later superseded by full redesign)
- Replaced all action button rows with single **"פעולות ▾"** dropdown (`QMenu`):
  - Customer list: 👁 פרטים / ✎ עריכה / ✕ מחק (`ui/screens/customer_list_screen.py`)
  - Treatment rows: + הוסף קבלה / ✎ עריכה / ✕ מחק (`ui/screens/customer_detail_screen.py`)
  - Receipt rows: ✎ עריכה / ✕ מחק (`ui/screens/customer_detail_screen.py`)
- Pre-approved `Bash(cd * && git *)` in `.claude/settings.local.json`
- All 46 tests passing

**Key files:**
- `ui/screens/customer_list_screen.py` — status badges (line ~158), dropdown (line ~171)
- `ui/screens/customer_detail_screen.py` — `_treatment_actions` (line ~155), `_receipt_actions` (line ~190)
- `ui/screens/add_receipt_screen.py` — `_export_file` method, date picker, save buttons
- `ui/screens/settings_screen.py` — new settings screen
- `services/settings_service.py` — new settings persistence service
- `ui/main_window.py` — settings nav button + `_show_settings()`
- `ui/styles.py` — `STATUS_COLORS`, `STATUS_BG_COLORS`, `STATUS_LABELS`

**Next steps:**
1. Wire up authentication — login screen exists but auth backend not connected to app launch flow
2. Build User Management screen (Manager creates/edits/deactivates users)
3. Build Permissions UI (Manager toggles feature access per user)
4. Add more settings (e.g. clinic name for receipt header, default status for new customers)
5. Verify `updated_at` fires correctly on partial updates in SQLite

**Open questions / blockers:**
- Auth flow: should login be required on every app launch, or persist session (already have session_service)?
- Receipt file format: currently plain `.txt` — should it be PDF in the future?

**Important context:**
- `_DatePickerButton` is defined in `add_customer_screen.py` and imported by both `add_treatment_screen.py` and `add_receipt_screen.py` — it's a shared widget living in a screen file (not ideal long-term, but works)
- `QMenu` dropdown style is duplicated across `customer_list_screen.py` and `customer_detail_screen.py` — could be extracted to a helper if it diverges
- `settings.json` is gitignored-by-convention (not in .gitignore yet) — contains local folder paths, should not be committed
- Global `QTableWidget::item` stylesheet must NOT set `color` or `background-color` — doing so overrides all item data roles silently
