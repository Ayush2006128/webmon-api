from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from src.core.database import get_db
from src.core.security import get_password_hash, verify_password as verify_hashed_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_api_key
from src.models import User, UserCreate, UserResponse, Token
from src.helper.validators import verify_email, verify_password

router = APIRouter(tags=["Auth"])

@router.post("/register", response_model=UserResponse, dependencies=[Depends(get_api_key)])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user in the system.
    
    This endpoint allows the creation of a new user account with an email and password.
    It verifies that the email is not already registered before creating the account.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if not verify_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if not verify_password(user.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long, alphanumeric, and contain at least one capital letter")
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT access token.
    
    Validates user credentials (email and password) via the OAuth2PasswordRequestForm.
    If valid, it returns an access token which can be used to authorize subsequent requests.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_hashed_password(form_data.password, user.hashed_password): # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
