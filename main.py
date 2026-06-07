from ai.helpers import invoke_agent

response = invoke_agent(thread_id="user_123", message="Hello, what can you do?")
print(response)