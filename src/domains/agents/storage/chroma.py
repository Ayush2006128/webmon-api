from langchain_chroma import Chroma
from langchain_core.tools import tool
from src.domains.agents.embeddings.cohere import embeddings

vector_store = Chroma(
    collection_name="web_pages",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

@tool
def search_stored_pages(query: str, num_results: int = 3) -> str:
    """Search previously stored web pages for information relevant to the query.

    Performs a semantic similarity search against the local ChromaDB vector store
    of pages that were previously read and stored via ``read_and_store_url``.

    Args:
        query: The natural-language search query to match against stored page content.
        num_results: Maximum number of matching chunks to return. Defaults to 3.

    Returns:
        A formatted string containing the matched content chunks along with their
        source URLs, or a message indicating no relevant information was found.
    """
    results = vector_store.similarity_search(query, k=num_results)
    if not results:
        return "No relevant information found in the stored pages."
        
    formatted = []
    for i, doc in enumerate(results):
        formatted.append(f"Source [{i+1}] ({doc.metadata.get('url')}):\n{doc.page_content}\n")
        
    return "\\n".join(formatted)
