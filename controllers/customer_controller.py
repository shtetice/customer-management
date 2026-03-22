from datetime import date
from sqlalchemy.orm import Session
from database.db import get_session
from database.models import Customer, CustomerStatus, Gender


class CustomerController:

    def get_all(self, status: CustomerStatus | None = None) -> list[Customer]:
        session = get_session()
        try:
            q = session.query(Customer)
            if status:
                q = q.filter(Customer.status == status)
            customers = q.order_by(Customer.surname, Customer.name).all()
            for c in customers:
                session.expunge(c)
            return customers
        finally:
            session.close()

    def get_by_id(self, customer_id: int) -> Customer | None:
        session = get_session()
        try:
            customer = session.query(Customer).filter_by(id=customer_id).first()
            if customer:
                session.expunge(customer)
            return customer
        finally:
            session.close()

    def search(self, query: str) -> list[Customer]:
        if not query or not query.strip():
            return self.get_all()
        session = get_session()
        try:
            q = f"%{query.strip()}%"
            customers = session.query(Customer).filter(
                Customer.name.ilike(q) |
                Customer.surname.ilike(q) |
                Customer.phone.ilike(q) |
                Customer.phone2.ilike(q) |
                Customer.phone3.ilike(q) |
                Customer.email.ilike(q)
            ).order_by(Customer.surname, Customer.name).all()
            for c in customers:
                session.expunge(c)
            return customers
        finally:
            session.close()

    def create(
        self,
        name: str,
        surname: str,
        gender: Gender | None,
        phone: str,
        phone2: str,
        phone3: str,
        email: str,
        status: CustomerStatus,
        notes: str,
        address: str = "",
        date_of_birth: date | None = None,
    ) -> Customer:
        self._validate(name, surname, email)
        session = get_session()
        try:
            customer = Customer(
                name=name.strip(),
                surname=surname.strip(),
                gender=gender,
                phone=phone.strip() if phone else None,
                phone2=phone2.strip() if phone2 else None,
                phone3=phone3.strip() if phone3 else None,
                email=email.strip().lower() if email else None,
                status=status,
                notes=notes.strip() if notes else None,
                address=address.strip() if address else None,
                date_of_birth=date_of_birth,
            )
            session.add(customer)
            session.commit()
            session.refresh(customer)
            session.expunge(customer)
            return customer
        finally:
            session.close()

    def update(
        self,
        customer_id: int,
        name: str,
        surname: str,
        gender: Gender | None,
        phone: str,
        phone2: str,
        phone3: str,
        email: str,
        status: CustomerStatus,
        notes: str,
        address: str = "",
        date_of_birth: date | None = None,
    ) -> Customer:
        self._validate(name, surname, email)
        session = get_session()
        try:
            customer = session.query(Customer).filter_by(id=customer_id).first()
            if not customer:
                raise ValueError(f"לקוח עם מזהה {customer_id} לא נמצא")
            customer.name = name.strip()
            customer.surname = surname.strip()
            customer.gender = gender
            customer.phone = phone.strip() if phone else None
            customer.phone2 = phone2.strip() if phone2 else None
            customer.phone3 = phone3.strip() if phone3 else None
            customer.email = email.strip().lower() if email else None
            customer.status = status
            customer.notes = notes.strip() if notes else None
            customer.address = address.strip() if address else None
            customer.date_of_birth = date_of_birth
            session.commit()
            session.refresh(customer)
            session.expunge(customer)
            return customer
        finally:
            session.close()

    def delete(self, customer_id: int):
        session = get_session()
        try:
            customer = session.query(Customer).filter_by(id=customer_id).first()
            if not customer:
                raise ValueError(f"לקוח עם מזהה {customer_id} לא נמצא")
            session.delete(customer)
            session.commit()
        finally:
            session.close()

    def _validate(self, name: str, surname: str, email: str):
        if not name or not name.strip():
            raise ValueError("שם הוא שדה חובה")
        if not surname or not surname.strip():
            raise ValueError("שם משפחה הוא שדה חובה")
        if email and email.strip() and "@" not in email:
            raise ValueError("כתובת האימייל אינה תקינה")


customer_controller = CustomerController()
