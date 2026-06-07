import os

from typing import Literal, List
from langchain_core.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_cohere import CohereEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from cohere import client, AsyncClient

load_dotenv()

cohere_key = os.environ["COHERE_API_KEY"]
tavily_key = os.environ["TAVILY_API_KEY"]

cohere_client = client.Client(cohere_key)
async_cohere_client = AsyncClient(cohere_key)
tavily_client = TavilyClient(api_key=tavily_key)

# Global Chroma setup
embeddings = CohereEmbeddings(client=client, async_client=async_cohere_client, model="embed-english-v3.0")
vector_store = Chroma(
    collection_name="web_pages",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

@tool
def search_web(query: str, search_depth: Literal["basic", "advanced", "fast", "ultra-fast"], num_results: int = 5, include_domains: List[str] = None, exclude_domains: List[str] = None) -> dict:
    """
    Search the web for the given query and return the results.

    Args:
        query (str): The search query.
        num_results (int): The number of search results to return.
        search_depth (Literal["basic", "advanced", "fast", "ultra-fast"]): The depth to search.
        include_domains (List[str], optional): Domain names to include in the search.
        exclude_domains (List[str], optional): Domain names to exclude from the search.

    Returns:
        dict: A string containing the search results.
    """
    
    results = tavily_client.search(query=query, num_results=num_results, search_depth=search_depth, include_domains=include_domains, exclude_domains=exclude_domains)
    return results

@tool
def read_and_store_url(urls: List[str] | str, depth: Literal["basic", "advanced"] = "basic") -> str:
    """
    Extract the main content from web pages using Tavily and store them in the vector database for later searching.
    Use this tool to read a webpage. After reading, use search_stored_pages to find specific information.

    Args:
        urls (List[str] | str): A list of URLs or a single URL to read and store.
        depth (Literal["basic", "advanced"]): The depth of content extraction.
    """
    
    content = tavily_client.extract(urls=urls, extract_depth=depth)
    
    results = content.get("results", [])
    if not results:
        return "No content extracted."

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = []
    
    for result in results:
        raw_text = result.get("raw_content", "")
        if not raw_text:
            continue
        url = result.get("url", "")
        
        chunks = splitter.split_text(raw_text)
        for chunk in chunks:
            docs.append(Document(page_content=chunk, metadata={"url": url}))
            
    if docs:
        vector_store.add_documents(docs)
        return f"Successfully read and stored {len(docs)} chunks from {len(results)} pages. You can now use search_stored_pages to query this content."
    return "No text content found to store."


@tool
def get_url_map(base_url: str, instructions: str) -> list:
    """
    This tool can traverse websites like a graph
    and can explore hundreds of paths in parallel
    with intelligent discovery to generate comprehensive site maps.

    Use this tool if you don't know what pages are available on website.

    Args:
        base_url (str): Base URL of website.
        instructions (str): Natural language instructions for the crawler.

    Returns:
       A list containing URLs
    """

    results = tavily_client.map(url=base_url, instructions=instructions)
    urls = results["results"]

    return urls


@tool
def search_stored_pages(query: str, num_results: int = 3) -> str:
    """
    Search the stored web pages for specific information.
    Only use this after you have stored pages using read_and_store_url.
    
    Args:
        query (str): The search query to look for in the stored pages.
        num_results (int): Number of matching chunks to return.
    """
    results = vector_store.similarity_search(query, k=num_results)
    if not results:
        return "No relevant information found in the stored pages."
        
    formatted = []
    for i, doc in enumerate(results):
        formatted.append(f"Source [{i+1}] ({doc.metadata.get('url')}):\n{doc.page_content}\n")
        
    return "\\n".join(formatted)
