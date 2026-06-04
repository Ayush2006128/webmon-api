import sys
sys.stdout.reconfigure(encoding='utf-8')
from ai.agent.react_agent import graph, GraphState
from langchain_core.messages import RemoveMessage
from langchain_core.runnables import RunnableConfig
def main():
    # Example conversation
    initial_messages = [
        "Which Spider-Man movie is about to release starring Tom Holand? USE THE TOOLS",
    ]
    config = RunnableConfig(configurable={"thread_id": 1})
    # Run the graph with the initial messages
    result = graph.invoke(input=GraphState(messages=initial_messages), config=config)
    
    # Print the final output (summary and any remaining messages)
    print("Final Summary:", result.get("summary", "No summary generated."))
    print("Remaining Messages to Keep:")
    for msg in result.get("messages", []):
        if isinstance(msg, RemoveMessage):
            print(f" - Message ID {msg.id} marked for deletion.")
        else:
            print(f" - {msg.content}")

if __name__ == "__main__":
    main()