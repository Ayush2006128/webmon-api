from langchain_core.messages import HumanMessage
from langgraph.graph.state import RunnableConfig
from .agent.react_agent import graph

def invoke_agent(thread_id: str, message: str) -> str:
    """
    Invokes the LangGraph agent with a given thread_id and message.
    
    Args:
        thread_id (str): The unique identifier for the conversation thread.
        message (str): The user's input message.
        
    Returns:
        str: The agent's response text.
    """
    config = RunnableConfig({"configurable": {"thread_id": thread_id}})
    inputs = {"messages": [HumanMessage(content=message)]}
    
    # Execute the graph
    response = graph.invoke(inputs, config=config)
    
    # Return the content of the last message (which should be from the agent)
    return response["messages"][-1].content

async def ainvoke_agent(thread_id: str, message: str) -> str:
    """
    Asynchronously invokes the LangGraph agent with a given thread_id and message.
    
    Args:
        thread_id (str): The unique identifier for the conversation thread.
        message (str): The user's input message.
        
    Returns:
        str: The agent's response text.
    """
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=message)]}
    
    # Execute the graph asynchronously
    response = await graph.ainvoke(inputs, config=config)
    
    return response["messages"][-1].content
