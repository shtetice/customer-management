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

**Last session:** 2026-03-26

**Completed today:**
- **Code review fixes** — `settings.json` added to `.gitignore`; `profile_photo_path` cached in `CustomerDetailScreen` (no per-click DB query); photo save path resolved against `_APP_ROOT`; `import shutil` moved to top; `_PhotoViewerDialog.mousePressEvent` only fires on background
- **Backup password encryption** — `services/crypto_service.py` using Fernet (AES-128-CBC + HMAC-SHA256, PBKDF2 key derivation, random salt per value); `set_secret()`/`get_secret()` added to `SettingsService`; backwards-compatible with plain-text values; 10 tests in `tests/test_crypto_service.py`
- **Tests** — `tests/test_activity_service.py` (10 tests), `tests/test_backup_service.py` (8 tests), `tests/test_crypto_service.py` (10 tests) — all green; total suite 72 passing
- **Logout quit fix** — removed `_logging_out` flag and `show_login()` call from logout flow; `closeEvent` now always calls `app.quit()`; clicking logout cleanly exits the Python process; `LoginScreen.closeEvent` also quits when login window is closed with X

**Key files:**
- `services/crypto_service.py` — Fernet encrypt/decrypt (new)
- `services/settings_service.py` — `set_secret()`/`get_secret()` (line ~37)
- `ui/main_window.py` — `closeEvent` always quits (line ~179), `_logout()` simplified (line ~210)
- `ui/screens/login_screen.py` — `closeEvent` calls `app.quit()` unless `_logging_in` (line ~108)
- `ui/screens/customer_detail_screen.py` — `_APP_ROOT` constant (line ~6), `_profile_photo_path` cache (line ~178)
- `tests/test_activity_service.py`, `tests/test_backup_service.py`, `tests/test_crypto_service.py` — new test files

**Next steps (priority order for next session):**
1. **Shared calendar** — new feature requested; design TBD (appointments/availability per staff member? per customer?)
2. Compile to Windows `.exe` via PyInstaller — add `msoffcrypto`, `openpyxl`, `cryptography` to spec
3. Receipt format — currently plain `.txt`; consider PDF
4. Verify `updated_at` fires correctly on partial updates in SQLite

**Open questions / blockers:**
- Shared calendar scope: per-staff appointments? customer booking? which view (day/week/month)?

**Important context:**
- `app.setQuitOnLastWindowClosed(False)` must stay — without it, closing the login window before the main window appears kills the app prematurely
- `LoginScreen._logging_in = True` must be set before `login_successful.emit()` — otherwise `login.close()` in `on_login()` triggers `closeEvent → app.quit()` mid-login
- `closeEvent` on `MainWindow` always calls `app.quit()` — do NOT add conditional logic back; session is cleared in `_logout()` before close
- `MainWindow` has NO `logout_requested` signal — it was removed; logout is handled entirely by `closeEvent`
- `_DatePickerButton` lives in `add_customer_screen.py` and is imported by `add_treatment_screen.py` and `add_receipt_screen.py`
- Global `QTableWidget::item` stylesheet must NOT set `color` or `background-color` — silently overrides item data roles
- All 74 tests passing (zero pre-existing failures remain)
