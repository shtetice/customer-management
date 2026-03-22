from datetime import datetime
from database.db import get_session
from database.models import Receipt


class ReceiptController:

    def get_by_customer(self, customer_id: int) -> list[Receipt]:
        session = get_session()
        try:
            receipts = (
                session.query(Receipt)
                .filter_by(customer_id=customer_id)
                .order_by(Receipt.date.desc())
                .all()
            )
            for r in receipts:
                session.expunge(r)
            return receipts
        finally:
            session.close()

    def get_by_id(self, receipt_id: int) -> Receipt | None:
        session = get_session()
        try:
            r = session.query(Receipt).filter_by(id=receipt_id).first()
            if r:
                session.expunge(r)
            return r
        finally:
            session.close()

    def create(
        self,
        customer_id: int,
        date: datetime,
        amount: str,
        description: str,
        treatment_id: int | None = None,
    ) -> Receipt:
        self._validate(amount)
        session = get_session()
        try:
            receipt = Receipt(
                customer_id=customer_id,
                treatment_id=treatment_id,
                date=date,
                amount=amount.strip(),
                description=description.strip() if description else None,
            )
            session.add(receipt)
            session.commit()
            session.refresh(receipt)
            session.expunge(receipt)
            return receipt
        finally:
            session.close()

    def update(
        self,
        receipt_id: int,
        date: datetime,
        amount: str,
        description: str,
        treatment_id: int | None = None,
    ) -> Receipt:
        self._validate(amount)
        session = get_session()
        try:
            r = session.query(Receipt).filter_by(id=receipt_id).first()
            if not r:
                raise ValueError(f"קבלה עם מזהה {receipt_id} לא נמצאה")
            r.date = date
            r.amount = amount.strip()
            r.description = description.strip() if description else None
            r.treatment_id = treatment_id
            session.commit()
            session.refresh(r)
            session.expunge(r)
            return r
        finally:
            session.close()

    def delete(self, receipt_id: int):
        session = get_session()
        try:
            r = session.query(Receipt).filter_by(id=receipt_id).first()
            if not r:
                raise ValueError(f"קבלה עם מזהה {receipt_id} לא נמצאה")
            session.delete(r)
            session.commit()
        finally:
            session.close()

    def _validate(self, amount: str):
        if not amount or not amount.strip():
            raise ValueError("סכום הוא שדה חובה")


receipt_controller = ReceiptController()
