from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.domains.agents.graph.state import GraphState
from src.domains.agents.graph.nodes import call_model, tool_node, summarize_conversation
from src.domains.agents.graph.edges import should_continue

builder = StateGraph(GraphState)

builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)
builder.add_node("summarize_conversation", summarize_conversation)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue)
builder.add_edge("tools", "agent")
builder.add_edge("summarize_conversation", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
