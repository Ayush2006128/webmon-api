from src.domains.agents.graph.state import GraphState
from langgraph.graph import END

def should_continue(state: GraphState) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.tool_calls: # type: ignore
        return "tools"
    
    if len(messages) > 6:
        return "summarize_conversation"
        
    return END
