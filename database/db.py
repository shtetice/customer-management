from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Feature, ContactLog

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
            ("phone2",        "VARCHAR(30)"),
            ("phone3",        "VARCHAR(30)"),
            ("address",       "VARCHAR(300)"),
            ("date_of_birth", "DATE"),
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

        conn.commit()


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
