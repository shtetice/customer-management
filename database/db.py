from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base, Feature

DATABASE_URL = "sqlite:///customer_management.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Create all tables and seed default features."""
    Base.metadata.create_all(bind=engine)
    _seed_features()


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
