from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.5,
    max_retries=2
)

messages = [
    ("system", "You are a playful math teacher, who explains math concepts with real-world examples"),
    ("user", "Explain LCM and HCF")
]

response = llm.invoke(messages)
print(response.content)