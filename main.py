import os
from typing import List
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Security, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from groq import Groq

from ai.helpers import ainvoke_agent
from ai.agent.react_agent import set_agent_model

from db import engine, Base, get_db
from models import User, UserCreate, UserResponse, Token
from auth import get_password_hash, verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

load_dotenv()

API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "your-super-secret-key") # You should set API_KEY in your hosting provider environment variables
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """Validate the incoming API key from the request header.

    Raises HTTPException(403) if the provided API key is invalid.
    """
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Invalid API Key")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if engine:
        Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Webmon API", lifespan=lifespan)

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

class ModelSelection(BaseModel):
    model_name: str

@app.post("/register", response_model=UserResponse, dependencies=[Depends(get_api_key)])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with an email and password.

    Validates that the email is not already in use, hashes the provided password,
    and stores the new user in the database.

    Args:
        user: The UserCreate schema containing the email and plaintext password.
        db: The database session dependency.

    Returns:
        The newly created User instance (serialized via UserResponse schema).

    Raises:
        HTTPException: If the email is already registered (400 Bad Request).
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT access token.

    Verifies the provided email (mapped to `username` in the OAuth2 form) and
    password against the stored credentials in the database. If successful,
    generates and returns a JWT access token valid for a specified duration.

    Args:
        form_data: The OAuth2 form data containing the username (email) and password.
        db: The database session dependency.

    Returns:
        A dictionary containing the access token and the token type.

    Raises:
        HTTPException: If the email or password is incorrect (401 Unauthorized).
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password): # type: ignore
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

@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(get_api_key), Depends(get_current_user)])
async def chat(request: ChatRequest):
    """Accept a chat request and invoke the AI agent for a response.

    Args:
        request: ChatRequest containing a thread identifier and user message.

    Returns:
        ChatResponse with the agent-generated message.
    """
    try:
        # Use async helper to not block the event loop
        response = await ainvoke_agent(thread_id=request.thread_id, message=request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models", response_model=List[str], dependencies=[Depends(get_api_key), Depends(get_current_user)])
def get_models():
    """Return the list of available Groq models or a fallback set on error."""
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        models = client.models.list()
        # Filter and sort IDs for convenience if desired, here we just return the full list
        return [m.id for m in models.data]
    except Exception as e:
        print(f"Error fetching models: {e}")
        # Fallback list if request fails
        return [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "qwen/qwen-32b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b"
        ]

@app.post("/model", dependencies=[Depends(get_api_key), Depends(get_current_user)])
def select_model(selection: ModelSelection):
    """Set the currently active agent model for subsequent chat requests."""
    try:
        set_agent_model(selection.model_name)
        return {"status": "success", "message": f"Model successfully changed to {selection.model_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)