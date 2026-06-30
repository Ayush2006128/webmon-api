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

import re

async def ainvoke_agent(thread_id: str, message: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=message)]}
    response = await graph.ainvoke(inputs, config=config)
    
    import json
    sources = set()
    for msg in response["messages"]:
        msg_name = getattr(msg, "name", None)
        content = getattr(msg, "content", "")
        if not isinstance(content, str):
            continue
            
        if msg_name == "search_stored_pages":
            matches = re.findall(r"Source \[\d+\] \((.*?)\):", content)
            for m in matches:
                sources.add(m)
        elif msg_name == "search_web":
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "results" in parsed:
                    for r in parsed["results"]:
                        if "url" in r:
                            sources.add(r["url"])
            except Exception:
                pass
                    
    return {
        "content": response["messages"][-1].content,
        "sources": list(sources)
    }

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(get_api_key)])
async def chat(request: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Send a message to the AI agent and receive a response.
    
    This endpoint consumes credits per request. It checks if the user has sufficient credits,
    deducts the cost, and then processes the message using the configured AI model.
    """
    check_and_refill_credits(user, db)
    
    if user.credits < 0.5:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    try:
        user.credits -= 0.5
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database transaction failed")

    try:
        agent_result = await ainvoke_agent(thread_id=request.thread_id, message=request.message)
        return ChatResponse(response=agent_result["content"], sources=agent_result["sources"])
    except Exception as e:
        user.credits += 0.5
        try:
            db.commit()
        except Exception as commit_err:
            db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models", response_model=List[str], dependencies=[Depends(get_api_key), Depends(get_current_user)])
def get_models():
    """
    Retrieve a list of available AI models.
    
    Fetches the available models dynamically using the Groq API. Falls back to a predefined
    list of standard models in case of an error retrieving the dynamic list.
    """
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
    """
    Select the AI model to be used for subsequent chat interactions.
    
    Updates the agent's configuration to utilize the specified model.
    Requires the target model name to be provided.
    """
    try:
        from src.domains.agents.graph.nodes import set_agent_model
        set_agent_model(selection.model_name)
        return {"status": "success", "message": f"Model successfully changed to {selection.model_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
