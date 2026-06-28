from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langgraph.prebuilt import ToolNode
from src.domains.agents.graph.state import GraphState
from src.domains.agents.tools.search import search_web, read_and_store_url, get_url_map
from src.domains.agents.storage.chroma import search_stored_pages

# Initialize Groq
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.7,
    max_retries=2
)

tools = [search_web, read_and_store_url, search_stored_pages, get_url_map]
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

SYSTEM_PROMPT = """
[IDENTITY START]
You are Webmon, a helpful, engaging, and highly capable research agent.
[IDENTITY END]

[GOAL START]
Always use your provided ${tools} efficiently to gather accurate and up-to-date information.
Whenever the user asks to research on government docs, then use the context from govt domains by setting include_domains appropriately.
Do not hallucinate or make up facts.
[GOAL END]

[BEHAVIOUR START]
Respect the user at all times and maintain a polite, classroom-friendly tone.
Do not sound like a dry robot. Be conversational, engaging, and approachable.
[BEHAVIOUR END]

[RESPONSIBILITY START]
As a research agent, you may be asked to research sensitive topics such as wars, history, or weapons.
You are free to share your objective findings,
but you must NEVER encourage the user to do anything harmful, illegal, or against society.
[RESPONSIBILITY END]
"""

def call_model(state: GraphState):
    summary = state.get("summary", "")
    system_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    if summary:
        system_messages.append(SystemMessage(content=f"Summary of previous conversation: {summary}"))
    messages = system_messages + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def summarize_conversation(state: GraphState):
    summary = state.get("summary", "")
    summary_context = f"Previous summary: {summary}\n\n" if summary else ""
    prompt = (
        f"Distill the following chat messages into a single comprehensive summary. {summary_context}"
        "Include all specific details, user preferences, and unresolved questions."
    )
    messages = state["messages"] + [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    messages_to_keep = 2
    delete_messages = [RemoveMessage(id=m.id or "") for m in state["messages"][:-messages_to_keep]]
    return {"summary": response.content, "messages": delete_messages}
