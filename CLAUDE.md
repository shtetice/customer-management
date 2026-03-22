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
| phone | String |
| email | String |
| status | Enum (lead/customer/retention/vip) |
| treatment_history | Relationship → TreatmentHistory |
| notes | Text |
| receipts | Relationship → Receipt |
| files | Relationship → CustomerFile |
| created_at | DateTime |
| updated_at | DateTime |

### User Roles
- **Manager** — full access to all data and features
- **User** — access controlled per-feature by Manager via Settings

## Features Planned
- [ ] Customer list & management (Leads, Customers, Retention, VIP)
- [ ] Add / Edit / Delete customer
- [ ] Treatment history
- [ ] Notes
- [ ] Receipts
- [ ] File attachments (PDF, DOCX, CSV)
- [ ] User authentication (login/logout)
- [ ] User management (Manager creates/manages users)
- [ ] Role-based permissions (Manager configures per-feature access)
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
**Status:** Project initialized. Tech stack decided. Starting with Customer model and Add/List customer UI.
**Next steps:**
1. Set up project folder structure and virtual environment
2. Create SQLAlchemy database models (Customer, User, Role, Permissions)
3. Build the main window with navigation
4. Build the Customer List screen (filterable by status)
5. Build the Add New Customer screen
