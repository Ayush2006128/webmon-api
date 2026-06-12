from sqlalchemy import Column, Integer, String
from pydantic import BaseModel
from db import Base

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

# Pydantic Schemas
class UserCreate(BaseModel):
    """Schema for creating a new user.

    Attributes:
        email: The email address for the new user.
        password: The plaintext password for the new user.
    """
    email: str
    password: str

class UserResponse(BaseModel):
    """Schema for returning user data in API responses.

    Attributes:
        id: The user's database ID.
        email: The user's email address.
    """
    id: int
    email: str

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
