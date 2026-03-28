import os
import shutil
from datetime import datetime
from database.db import get_session
from database.models import Receipt
from services.activity_service import log_action
from services.auth_service import auth_service


def _cname(customer_id: int) -> str:
    from controllers.customer_controller import customer_controller
    c = customer_controller.get_by_id(customer_id)
    return f"{c.name} {c.surname}" if c else f"לקוח #{customer_id}"

RECEIPTS_UPLOAD_DIR = os.path.join("uploads", "receipts")


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
        pdf_source_path: str | None = None,
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
            if pdf_source_path:
                receipt.pdf_path = self._store_pdf(pdf_source_path, receipt.id, date)
                session.commit()
                session.refresh(receipt)
            session.expunge(receipt)
            if auth_service.current_user:
                log_action(auth_service.current_user.username,
                           f"הוספת קבלה: {_cname(customer_id)} — ₪{amount.strip()}")
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
        pdf_source_path: str | None = None,
        clear_pdf: bool = False,
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
            if clear_pdf:
                r.pdf_path = None
            elif pdf_source_path:
                r.pdf_path = self._store_pdf(pdf_source_path, r.id, date)
            session.commit()
            session.refresh(r)
            session.expunge(r)
            if auth_service.current_user:
                log_action(auth_service.current_user.username,
                           f"עדכון קבלה: {_cname(r.customer_id)} — ₪{r.amount}")
            return r
        finally:
            session.close()

    def _store_pdf(self, source_path: str, receipt_id: int, date: datetime) -> str:
        os.makedirs(RECEIPTS_UPLOAD_DIR, exist_ok=True)
        filename = f"receipt_{receipt_id}_{date.strftime('%Y%m%d')}.pdf"
        dest = os.path.join(RECEIPTS_UPLOAD_DIR, filename)
        shutil.copy2(source_path, dest)
        return dest

    def delete(self, receipt_id: int):
        session = get_session()
        try:
            r = session.query(Receipt).filter_by(id=receipt_id).first()
            if not r:
                raise ValueError(f"קבלה עם מזהה {receipt_id} לא נמצאה")
            _log_cid, _log_amount = r.customer_id, r.amount
            session.delete(r)
            session.commit()
            if auth_service.current_user:
                log_action(auth_service.current_user.username,
                           f"מחיקת קבלה: {_cname(_log_cid)} — ₪{_log_amount}")
        finally:
            session.close()

    def _validate(self, amount: str):
        if not amount or not amount.strip():
            raise ValueError("סכום הוא שדה חובה")


receipt_controller = ReceiptController()
