import os
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

from ai.helpers import ainvoke_agent
from ai.agent.react_agent import set_agent_model

load_dotenv()

app = FastAPI(title="Webmon API")

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

class ModelSelection(BaseModel):
    model_name: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Use async helper to not block the event loop
        response = await ainvoke_agent(thread_id=request.thread_id, message=request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models", response_model=List[str])
def get_models():
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        models = client.models.list()
        # Filter and sort IDs for convenience if desired, here we just return the full list
        return [m.id for m in models.data]
    except Exception as e:
        print(f"Error fetching models: {e}")
        # Fallback list if request fails
        return [
            "llama3-8b-8192",
            "llama3-70b-8192",
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]

@app.post("/model")
def select_model(selection: ModelSelection):
    try:
        set_agent_model(selection.model_name)
        return {"status": "success", "message": f"Model successfully changed to {selection.model_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)