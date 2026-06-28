from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from pydantic import BaseModel
from src.core.database import Base

# SQLAlchemy Models
class User(Base):
    """SQLAlchemy model representing a user in the database.

    Attributes:
        id: Primary key identifier for the user.
        email: The user's email address (must be unique).
        hashed_password: The bcrypt-hashed representation of the user's password.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    credits = Column(Float, default=5.0, nullable=False)
    last_refill_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class PaymentTransaction(Base):
    """SQLAlchemy model representing a Razorpay payment transaction."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    razorpay_order_id = Column(String, unique=True, index=True, nullable=False)
    razorpay_payment_id = Column(String, nullable=True)
    amount_inr = Column(Integer, nullable=False)
    credits_added = Column(Float, nullable=False)
    status = Column(String, default="created", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

# Pydantic Schemas
class UserCreate(BaseModel):
    """Schema for creating a new user.

    Attributes:
        email: The email address for the new user.
        password: The plaintext password for the new user.
    """
    email: str
    password: str

class PasswordUpdate(BaseModel):
    """Schema for updating a user's password.
    
    Attributes:
        old_password: The current password.
        new_password: The new password to set.
    """
    old_password: str
    new_password: str

class UserResponse(BaseModel):
    """Schema for returning user data in API responses.

    Attributes:
        id: The user's database ID.
        email: The user's email address.
    """
    id: int
    email: str
    credits: float

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema for returning an OAuth2 token.

    Attributes:
        access_token: The encoded JWT string.
        token_type: The type of the token (e.g., 'bearer').
    """
    access_token: str
    token_type: str
