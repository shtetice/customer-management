from datetime import date
from sqlalchemy import extract
from sqlalchemy.orm import Session
from database.db import get_session
from database.models import Customer, CustomerStatus, Gender


class CustomerController:

    def get_all(
        self,
        status: CustomerStatus | None = None,
        birth_month: int | None = None,
        birth_year: int | None = None,
        city: str | None = None,
    ) -> list[Customer]:
        session = get_session()
        try:
            q = session.query(Customer)
            if status:
                q = q.filter(Customer.status == status)
            if birth_month:
                q = q.filter(extract("month", Customer.date_of_birth) == birth_month)
            if birth_year:
                q = q.filter(extract("year", Customer.date_of_birth) == birth_year)
            if city:
                q = q.filter(Customer.city == city)
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

    def search(
        self,
        query: str,
        birth_month: int | None = None,
        birth_year: int | None = None,
        city: str | None = None,
    ) -> list[Customer]:
        if not query or not query.strip():
            return self.get_all(birth_month=birth_month, birth_year=birth_year, city=city)
        session = get_session()
        try:
            qp = f"%{query.strip()}%"
            q = session.query(Customer).filter(
                Customer.name.ilike(qp) |
                Customer.surname.ilike(qp) |
                Customer.phone.ilike(qp) |
                Customer.phone2.ilike(qp) |
                Customer.phone3.ilike(qp) |
                Customer.email.ilike(qp)
            )
            if birth_month:
                q = q.filter(extract("month", Customer.date_of_birth) == birth_month)
            if birth_year:
                q = q.filter(extract("year", Customer.date_of_birth) == birth_year)
            if city:
                q = q.filter(Customer.city == city)
            customers = q.order_by(Customer.surname, Customer.name).all()
            for c in customers:
                session.expunge(c)
            return customers
        finally:
            session.close()

    def get_distinct_cities(self) -> list[str]:
        session = get_session()
        try:
            rows = (
                session.query(Customer.city)
                .filter(Customer.city != None, Customer.city != "")
                .distinct()
                .order_by(Customer.city)
                .all()
            )
            return [r[0] for r in rows]
        finally:
            session.close()

    def get_distinct_birth_years(self) -> list[int]:
        session = get_session()
        try:
            rows = (
                session.query(extract("year", Customer.date_of_birth).label("yr"))
                .filter(Customer.date_of_birth != None)
                .distinct()
                .order_by("yr")
                .all()
            )
            return sorted([int(r[0]) for r in rows], reverse=True)
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
        city: str = "",
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
                city=city.strip() if city else None,
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
        city: str = "",
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
            customer.city = city.strip() if city else None
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
