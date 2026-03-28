from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Feature, ContactLog, ActivityLog, Appointment, NotificationLog

DATABASE_URL = "sqlite:///customer_management.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def init_db():
    """Create all tables, run migrations, and seed default features."""
    Base.metadata.create_all(bind=engine)
    _migrate()
    _seed_features()


def _migrate():
    """Add new columns to existing tables if they don't exist yet."""
    with engine.connect() as conn:
        existing = [row[1] for row in conn.execute(
            text("PRAGMA table_info(customers)")
        )]
        for col, typedef in [
            ("phone2",             "VARCHAR(30)"),
            ("phone3",             "VARCHAR(30)"),
            ("address",            "VARCHAR(300)"),
            ("city",               "VARCHAR(100)"),
            ("date_of_birth",      "DATE"),
            ("profile_photo_path", "VARCHAR(500)"),
        ]:
            if col not in existing:
                conn.execute(text(
                    f"ALTER TABLE customers ADD COLUMN {col} {typedef}"
                ))

        receipts_cols = [row[1] for row in conn.execute(
            text("PRAGMA table_info(receipts)")
        )]
        if "pdf_path" not in receipts_cols:
            conn.execute(text("ALTER TABLE receipts ADD COLUMN pdf_path VARCHAR(500)"))

        users_cols = [row[1] for row in conn.execute(
            text("PRAGMA table_info(users)")
        )]
        if "is_active" not in users_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            conn.execute(text("UPDATE users SET is_active = 1 WHERE is_active IS NULL"))

        # treatments.appointment_id — links auto-created treatments back to their source appointment
        tables = [row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))]
        if "treatments" in tables:
            treatments_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(treatments)"))]
            if "appointment_id" not in treatments_cols:
                conn.execute(text("ALTER TABLE treatments ADD COLUMN appointment_id INTEGER REFERENCES appointments(id)"))

        if "appointments" in tables:
            appt_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(appointments)"))]
            if "google_event_id" not in appt_cols:
                conn.execute(text("ALTER TABLE appointments ADD COLUMN google_event_id VARCHAR(200)"))

        conn.commit()

    # Seed NotificationLog for appointments already sent via the old flag-based system,
    # so the new rule-based scheduler doesn't re-send them.
    _seed_notification_log()


def _seed_notification_log():
    """One-time migration: populate NotificationLog from legacy reminder_sent/followup_sent flags."""
    session = get_session()
    try:
        # Only run if the log is completely empty (fresh migration)
        if session.query(NotificationLog).count() > 0:
            return
        from database.models import Appointment
        for appt in session.query(Appointment).filter(Appointment.reminder_sent == True).all():
            session.add(NotificationLog(
                appointment_id=appt.id,
                rule_key="reminder_24h",
            ))
        for appt in session.query(Appointment).filter(Appointment.followup_sent == True).all():
            session.add(NotificationLog(
                appointment_id=appt.id,
                rule_key="followup_72h",
            ))
        session.commit()
    finally:
        session.close()


def get_session() -> Session:
    return SessionLocal()


# Feature keys that map to app sections — used by permission system
DEFAULT_FEATURES = [
    ("customers.view",      "צפייה בלקוחות",          "גישה לרשימת הלקוחות"),
    ("customers.add",       "הוספת לקוח",              "יצירת לקוח חדש"),
    ("customers.edit",      "עריכת לקוח",              "עדכון פרטי לקוח"),
    ("customers.delete",    "מחיקת לקוח",              "מחיקת לקוח מהמערכת"),
    ("leads.view",          "צפייה בלידים",            "גישה לרשימת הלידים"),
    ("retention.view",      "צפייה ב-Retention",       "גישה ללקוחות ב-Retention"),
    ("vip.view",            "צפייה ב-VIP",             "גישה ללקוחות VIP"),
    ("treatments.view",     "צפייה בהיסטוריית טיפולים","גישה להיסטוריית הטיפולים"),
    ("treatments.add",      "הוספת טיפול",             "הוספת טיפול חדש ללקוח"),
    ("receipts.view",       "צפייה בקבלות",            "גישה לרשימת הקבלות"),
    ("receipts.add",        "הוספת קבלה",              "הוספת קבלה חדשה ללקוח"),
    ("files.view",          "צפייה בקבצים",            "גישה לקבצים מצורפים"),
    ("files.upload",        "העלאת קבצים",             "העלאת קבצים ללקוח"),
    ("users.manage",        "ניהול משתמשים",           "יצירה ועריכה של משתמשים (מנהל בלבד)"),
    ("settings.view",       "הגדרות",                  "גישה למסך ההגדרות"),
    ("logs.view",           "יומן פעילות",             "צפייה ביומן הפעילות (מנהל בלבד)"),
    ("calendar.view",       "לוח תורים",               "גישה ללוח התורים"),
    ("calendar.add",        "הוספת תור",               "הוספת תור חדש ללוח"),
]


def _seed_features():
    session = get_session()
    try:
        for key, label, description in DEFAULT_FEATURES:
            exists = session.query(Feature).filter_by(key=key).first()
            if not exists:
                session.add(Feature(key=key, label=label, description=description))
        session.commit()
    finally:
        session.close()
