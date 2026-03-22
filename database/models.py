import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Enum, ForeignKey,
    Boolean, Table
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class CustomerStatus(enum.Enum):
    LEAD = "lead"
    CUSTOMER = "customer"
    RETENTION = "retention"
    VIP = "vip"


class UserRole(enum.Enum):
    MANAGER = "manager"
    USER = "user"


# ---------- Customer ----------

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    gender = Column(Enum(Gender), nullable=True)
    phone = Column(String(30), nullable=True)
    phone2 = Column(String(30), nullable=True)
    phone3 = Column(String(30), nullable=True)
    email = Column(String(150), nullable=True)
    address = Column(String(300), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    status = Column(Enum(CustomerStatus), nullable=False, default=CustomerStatus.LEAD)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    treatments = relationship("Treatment", back_populates="customer", cascade="all, delete-orphan")
    receipts = relationship("Receipt", back_populates="customer", cascade="all, delete-orphan")
    files = relationship("CustomerFile", back_populates="customer", cascade="all, delete-orphan")


class Treatment(Base):
    __tablename__ = "treatments"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(Text, nullable=False)
    performed_by = Column(String(150), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="treatments")
    receipt = relationship("Receipt", back_populates="treatment", uselist=False)


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    treatment_id = Column(Integer, ForeignKey("treatments.id"), nullable=True)
    amount = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="receipts")
    treatment = relationship("Treatment", back_populates="receipt")


class CustomerFile(Base):
    __tablename__ = "customer_files"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    filetype = Column(String(10), nullable=True)   # pdf, docx, csv
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="files")


# ---------- Auth & Permissions ----------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")


class Feature(Base):
    """Master list of all features/sections in the app."""
    __tablename__ = "features"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False, unique=True)   # e.g. "customers.view"
    label = Column(String(200), nullable=False)              # Hebrew display label
    description = Column(Text, nullable=True)

    permissions = relationship("UserPermission", back_populates="feature")


class UserPermission(Base):
    """Per-user permission override for a specific feature."""
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False)
    allowed = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="permissions")
    feature = relationship("Feature", back_populates="permissions")
