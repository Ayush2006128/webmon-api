from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.core.database import get_db
from src.core.security import get_current_user, get_api_key
from src.models import User
from src.schemas import ChatRequest, ChatResponse, ModelSelection
from src.domains.billing.routers import check_and_refill_credits
from src.domains.agents.graph.react_agent import graph
from langchain_core.messages import HumanMessage
import os
from groq import Groq

router = APIRouter(tags=["Agents"])

async def ainvoke_agent(thread_id: str, message: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=message)]}
    response = await graph.ainvoke(inputs, config=config)
    return response["messages"][-1].content

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(get_api_key)])
async def chat(request: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    check_and_refill_credits(user, db)
    
    if user.credits < 0.5:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    try:
        user.credits -= 0.5
        db.commit()
        db.refresh(user)

        response = await ainvoke_agent(thread_id=request.thread_id, message=request.message)
        return ChatResponse(response=response)
    except Exception as e:
        user.credits += 0.5
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models", response_model=List[str], dependencies=[Depends(get_api_key), Depends(get_current_user)])
def get_models():
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        models = client.models.list()
        return [m.id for m in models.data]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "qwen/qwen-32b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b"
        ]

@router.post("/model", dependencies=[Depends(get_api_key), Depends(get_current_user)])
def select_model(selection: ModelSelection):
    try:
        from src.domains.agents.graph.nodes import set_agent_model
        set_agent_model(selection.model_name)
        return {"status": "success", "message": f"Model successfully changed to {selection.model_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
