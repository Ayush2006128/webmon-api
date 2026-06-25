from langchain_cohere import CohereEmbeddings
from cohere import client, AsyncClient
from src.core.config import COHERE_API_KEY

cohere_client = client.Client(COHERE_API_KEY or "dummy_key")
async_cohere_client = AsyncClient(COHERE_API_KEY or "dummy_key")

embeddings = CohereEmbeddings(client=cohere_client, async_client=async_cohere_client, model="embed-english-v3.0")
