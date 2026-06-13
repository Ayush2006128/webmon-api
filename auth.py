import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db import get_db
from models import User

# Authentication constants
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-please-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plaintext password provided by the user.
        hashed_password: The hashed password stored in the database.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash for a given password.

    Args:
        password: The plaintext password to hash.

    Returns:
        The resulting bcrypt hashed password as a string.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new JWT access token.

    Args:
        data: A dictionary containing the payload data to encode in the JWT.
        expires_delta: An optional timedelta representing the token's validity duration. 
                       If not provided, defaults to 15 minutes.

    Returns:
        The encoded JWT token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Retrieve the current authenticated user based on the JWT token.

    Decodes the provided JWT token to extract the user's email, and fetches
    the corresponding user from the database.

    Args:
        token: The JWT access token (extracted from the Bearer header).
        db: The database session dependency.

    Returns:
        The authenticated User model instance.

    Raises:
        HTTPException: If the token is invalid, expired, or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub") # type: ignore
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
