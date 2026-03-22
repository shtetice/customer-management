from datetime import datetime
from database.db import get_session
from database.models import Treatment


class TreatmentController:

    def get_by_customer(self, customer_id: int) -> list[Treatment]:
        session = get_session()
        try:
            treatments = (
                session.query(Treatment)
                .filter_by(customer_id=customer_id)
                .order_by(Treatment.date.desc())
                .all()
            )
            for t in treatments:
                session.expunge(t)
            return treatments
        finally:
            session.close()

    def get_by_id(self, treatment_id: int) -> Treatment | None:
        session = get_session()
        try:
            t = session.query(Treatment).filter_by(id=treatment_id).first()
            if t:
                session.expunge(t)
            return t
        finally:
            session.close()

    def create(
        self,
        customer_id: int,
        date: datetime,
        description: str,
        performed_by: str,
        notes: str,
    ) -> Treatment:
        if not description or not description.strip():
            raise ValueError("תיאור הטיפול הוא שדה חובה")
        session = get_session()
        try:
            treatment = Treatment(
                customer_id=customer_id,
                date=date,
                description=description.strip(),
                performed_by=performed_by.strip() if performed_by else None,
                notes=notes.strip() if notes else None,
            )
            session.add(treatment)
            session.commit()
            session.refresh(treatment)
            session.expunge(treatment)
            return treatment
        finally:
            session.close()

    def update(
        self,
        treatment_id: int,
        date: datetime,
        description: str,
        performed_by: str,
        notes: str,
    ) -> Treatment:
        if not description or not description.strip():
            raise ValueError("תיאור הטיפול הוא שדה חובה")
        session = get_session()
        try:
            t = session.query(Treatment).filter_by(id=treatment_id).first()
            if not t:
                raise ValueError(f"טיפול עם מזהה {treatment_id} לא נמצא")
            t.date = date
            t.description = description.strip()
            t.performed_by = performed_by.strip() if performed_by else None
            t.notes = notes.strip() if notes else None
            session.commit()
            session.refresh(t)
            session.expunge(t)
            return t
        finally:
            session.close()

    def delete(self, treatment_id: int):
        session = get_session()
        try:
            t = session.query(Treatment).filter_by(id=treatment_id).first()
            if not t:
                raise ValueError(f"טיפול עם מזהה {treatment_id} לא נמצא")
            session.delete(t)
            session.commit()
        finally:
            session.close()


treatment_controller = TreatmentController()
