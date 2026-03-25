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
- **Activity logging** — `services/activity_service.py` with `log_action`, `get_logs`, `delete_all_logs`, `has_activity_since`, `purge_old_logs`; `ActivityLog` model in `database/models.py`; migration in `database/db.py`
- **Activity log screen** — `ui/screens/activity_log_screen.py`; admin-only nav button in sidebar; refresh + delete-all with confirmation
- **Auto-backup on close** — `services/backup_service.py` (openpyxl + msoffcrypto password-protected Excel); `_run_autobackup()` in `ui/main_window.py`; skips backup if no activity since last run; saves `last_backup_time` to settings
- **Reveal backup password** — Settings screen: admin must re-enter login password via `_ConfirmPasswordDialog` before password is shown
- **Log retention setting** — configurable via Settings screen (`log_retention_days`); `purge_old_logs()` called on startup
- **Remember Me fix** — root cause: logout called `session_service.clear()` then `close()` which triggered `closeEvent → app.quit()`, killing the new login screen. Fix: `_logging_out` flag in `MainWindow` suppresses `app.quit()` during logout. Also added `app.setQuitOnLastWindowClosed(False)` in `main.py`
- **Customer profile photo** — `profile_photo_path` column on Customer; `CustomerController.set_profile_photo()`; clickable avatar circle in `CustomerDetailScreen`; left-click enlarges photo (`_PhotoViewerDialog`, 600×600 max); right-click shows context menu (הגדל/שנה/הסר); circular crop via `QPainter`+`QPainterPath`; photo stored in `uploads/photos/<id>/profile.<ext>`

**Key files:**
- `services/activity_service.py` — audit log (all CRUD)
- `services/backup_service.py` — Excel backup with password encryption
- `ui/screens/activity_log_screen.py` — admin log viewer
- `ui/screens/settings_screen.py` — backup folder/password/reveal, log retention setting
- `ui/main_window.py` — `_run_autobackup()` (line ~186), `_logging_out` flag (line ~24), `_logout()` (line ~214)
- `ui/screens/customer_detail_screen.py` — `_avatar_mouse_press` (line ~221), `_make_circular_photo` (line ~267), `_PhotoViewerDialog` (line ~1080)
- `database/models.py` — `ActivityLog` model (line ~158), `profile_photo_path` on Customer (line ~50)

**Next steps:**
1. Add tests for `activity_service`, `backup_service`, `session_service`, and profile photo flow — currently no coverage
2. Add `settings.json` to `.gitignore` explicitly (it contains local folder paths and the backup password)
3. Consider encrypting the backup password at rest in `settings.json` — currently stored in plain text
4. Compile to Windows `.exe` via PyInstaller (add `msoffcrypto`, `openpyxl` to spec)
5. Receipt file format: currently plain `.txt` — consider PDF in the future
6. Verify `updated_at` fires correctly on partial updates in SQLite

**Open questions / blockers:**
- Backup password is stored in plain text in `settings.json` — acceptable for now but worth addressing before wider deployment
- `uploads/photos/` directory is not in `.gitignore` — profile photos could be committed accidentally

**Important context:**
- `_DatePickerButton` is defined in `add_customer_screen.py` and imported by both `add_treatment_screen.py` and `add_receipt_screen.py` — shared widget living in a screen file
- `QMenu` dropdown style is duplicated across `customer_list_screen.py` and `customer_detail_screen.py`
- Global `QTableWidget::item` stylesheet must NOT set `color` or `background-color` — doing so overrides all item data roles silently
- `app.setQuitOnLastWindowClosed(False)` is essential — without it, closing the login window kills the app before the main window appears
- `_logging_out` flag pattern must be preserved in `MainWindow` — removing it will break "Remember Me" on logout
