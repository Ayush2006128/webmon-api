from typing import Literal

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from .tools import search_web, read_and_store_url, search_stored_pages
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. State Definition
# ==========================================
# We extend LangGraph's default MessagesState to include a custom 'summary' field.
class GraphState(MessagesState):
    summary: str

# ==========================================
# 2. LLM & Tool Configuration
# ==========================================
# Initialize Groq as the provider
llm = ChatGroq(
    model="llama3.1-8b-instruct", # Default
    temperature=0.7,
    max_retries=2
)

tools = [search_web, read_and_store_url, search_stored_pages]
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)

def set_agent_model(model_name: str):
    global llm, llm_with_tools
    llm = ChatGroq(
        model=model_name,
        temperature=0.7,
        max_retries=2
    )
    llm_with_tools = llm.bind_tools(tools)
    return True

# ==========================================
# 3. Node Functions
# ==========================================
SYSTEM_PROMPT = """
You are Webmon, a helpful, engaging, and highly capable research agent.
Always use your provided ${tools} efficiently to gather accurate and up-to-date information.
Whenever the user asks to research on govt docs, then use the context from govt domains by setting include_domains appropriately.
Do not hallucinate or make up facts.
Respect the user at all times and maintain a polite, classroom-friendly tone.
Do not sound like a dry robot—be conversational, engaging, and approachable.
As a research agent,
you may be asked to research sensitive topics such as wars, history, or weapons.
You are free to share your objective findings,
but you must NEVER encourage the user to do anything harmful, illegal, or against society.
Always attach list of sources in response.
"""

def call_model(state: GraphState):
    """Invokes the model with the conversation history and summary (if it exists)."""
    summary = state.get("summary", "")
    
    system_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    # If a summary exists, inject it as a system message at the start
    if summary:
        system_messages.append(SystemMessage(content=f"Summary of previous conversation: {summary}"))
        
    messages = system_messages + state["messages"]
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def summarize_conversation(state: GraphState):
    """Summarizes older messages and removes them from the active state to save tokens."""
    summary = state.get("summary", "")
    summary_context = f"Previous summary: {summary}\n\n" if summary else ""
    
    prompt = (
        f"Distill the following chat messages into a single comprehensive summary. {summary_context}"
        "Include all specific details, user preferences, and unresolved questions."
    )
    
    # Ask the LLM to generate a new summary
    messages = state["messages"] + [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    
    # Keep only the last 2 messages for immediate context; flag the rest for deletion
    messages_to_keep = 2
    delete_messages = [RemoveMessage(id=m.id or "") for m in state["messages"][:-messages_to_keep]]
    
    return {"summary": response.content, "messages": delete_messages}

# ==========================================
# 4. Routing Logic
# ==========================================
def should_continue(state: GraphState) -> str:
    """Determines the next node based on tool calls and message length."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Route to tools if the LLM requested an action
    if last_message.tool_calls:
        return "tools"
    
    # Trigger summarization if the context is getting too long (e.g., > 6 messages)
    if len(messages) > 6:
        return "summarize_conversation"
        
    return END

# ==========================================
# 5. Build and Compile the Graph
# ==========================================
builder = StateGraph(GraphState)

# Add Nodes
builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)
builder.add_node("summarize_conversation", summarize_conversation)

# Add Edges
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue)
builder.add_edge("tools", "agent")
builder.add_edge("summarize_conversation", END)

# Attach Checkpointer (MemorySaver) for thread persistence
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)