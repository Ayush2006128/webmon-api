import os
from typing import List
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

from ai.helpers import ainvoke_agent
from ai.agent.react_agent import set_agent_model

load_dotenv()

API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "your-super-secret-key") # You should set API_KEY in your Render environment variables!
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """Validate the incoming API key from the request header.

    Raises HTTPException(403) if the provided API key is invalid.
    """
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Invalid API Key")

app = FastAPI(title="Webmon API")

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

class ModelSelection(BaseModel):
    model_name: str

@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(get_api_key)])
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

@app.get("/models", response_model=List[str], dependencies=[Depends(get_api_key)])
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
            "llama3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "qwen/qwen-32b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b"
        ]

@app.post("/model", dependencies=[Depends(get_api_key)])
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