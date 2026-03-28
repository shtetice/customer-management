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

**Last session:** 2026-03-28

**Completed today:**
- **Hebrew spell checker** — real-time underline via `_HebrewSpellHighlighter(QSyntaxHighlighter)` + right-click suggestions in `_SpellTextEdit`; uses pyenchant/enchant `he` dict; graceful fallback if unavailable
- **Campaign name field** — mandatory internal-use name added to compose tab (`QLineEdit`), history table (first column "שם קמפיין"), detail dialog title, Campaign model + DB migration
- **Typed send confirmation** — `_TypeConfirmDialog` shows message preview + customer list; "שלח" button locked until user types exactly `אישור`; this runs before the repeat-customer check
- **Spelling warning in confirmation** — if message has misspelled Hebrew words, a yellow warning banner lists them inside the confirmation dialog

**Key files:**
- `ui/screens/marketing_screen.py` — all marketing UI; spell checker at top of file (~line 18–75); `_TypeConfirmDialog` (~line 399–485); `_on_send` flow (~line 244–311)
- `database/models.py` — `Campaign.name` column (~line 205)
- `database/db.py` — migration for `campaigns.name` column (~line 58–62)
- `controllers/campaign_controller.py` — `send_campaign()` accepts `name` param (~line 47)

**Next steps (priority order for next session):**
1. **Twilio production** — switch from sandbox to production WhatsApp number (Facebook Business Manager, Meta approval, pre-approved templates); waiting for user to initiate
2. **Compile to Windows `.exe`** — PyInstaller spec needs `msoffcrypto`, `openpyxl`, `cryptography`, `Pillow`, `pyenchant`; user is on Mac; enchant C lib must be bundled
3. **Manual export** — auto-backup done; manual CSV/Excel export not yet implemented
4. **Tests for marketing/campaign features** — no tests written for `campaign_controller`, `MarketingScreen`, or the new name/spell flows

**Open questions / blockers:**
- Twilio: waiting on user to initiate Meta Business Manager setup
- pyenchant on Windows: enchant C library needs to be present; may need to bundle hunspell DLL in PyInstaller build

**Important context:**
- `app.setQuitOnLastWindowClosed(False)` must stay — without it, closing the login window kills the app prematurely
- `LoginScreen._logging_in = True` must be set before `login_successful.emit()`
- `closeEvent` on `MainWindow` always calls `app.quit()` — do NOT add conditional logic back
- `_DatePickerButton` lives in `add_customer_screen.py` and is imported by `add_treatment_screen.py`, `add_receipt_screen.py`, `add_appointment_dialog.py`
- Global `QTableWidget::item` stylesheet must NOT set `color` or `background-color`
- Campaign name column migration: checks `if "campaigns" in tables` before altering — safe for fresh installs
- `_TypeConfirmDialog` uses `text.strip() == "אישור"` — strips whitespace so user can't accidentally type a space; intentional
- All 78 tests passing
