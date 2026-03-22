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

**Last session:** 2026-03-22

**Completed today:**
- Added `address` (String 300) and `date_of_birth` (Date) fields to `Customer` model (`database/models.py`)
- Extended `db._migrate()` to ADD COLUMN for both new fields on existing databases (`database/db.py`)
- Updated `CustomerController.create()` and `.update()` to accept and persist the new fields (`controllers/customer_controller.py`)
- Built `_DatePickerButton` custom calendar popup in `ui/screens/add_customer_screen.py`:
  - Fully LTR-forced to avoid RTL corruption in Hebrew layout
  - Custom nav bar: month dropdown + year dropdown (1920–today) + ◀▶ buttons
  - Built-in calendar hidden nav, max date = today, default = 30 years ago
  - Popup positioned at button's bottom-left edge
- Added address + DOB fields to the Add/Edit Customer form (row 4, side by side)

**Key files:**
- `ui/screens/add_customer_screen.py` — `_DatePickerButton` (line 75), form (line 241)
- `database/models.py` — Customer model (line 34)
- `database/db.py` — migration (line 18)
- `controllers/customer_controller.py` — create/update (line 52, 90)

**Next steps:**
1. Add tests for `address` and `date_of_birth` in `tests/test_customer_controller.py`
2. Wire up authentication — login screen exists (`ui/screens/login_screen.py`) but auth backend not connected
3. Build User Management screen (Manager creates/edits users)
4. Build Permissions UI (Manager toggles feature access per user)
5. Fix `__import__("sqlalchemy")` in `db.py:32` — import `text` from sqlalchemy at top of file

**Open questions / blockers:**
- Calendar popup may render off-screen if DOB field is near the bottom of the window — no bounds checking yet
- `updated_at` relies on SQLAlchemy's `onupdate` hook; verify this fires correctly for partial updates in SQLite

**Important context:**
- The DB migration in `_migrate()` uses hardcoded column names in an f-string — not a real injection risk since values are literals, but looks like one
- Tests use in-memory SQLite (`conftest.py`) — `_migrate()` is NOT called in tests, so migration logic itself is untested
- Calendar is built as a `QDialog` with `Popup | FramelessWindowHint` flags; on some macOS window managers it may flicker — tested okay on dev machine
