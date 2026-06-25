from typing import Literal, List
from langchain_core.tools import tool
from tavily import TavilyClient
from src.core.config import TAVILY_API_KEY
from src.domains.agents.storage.chroma import vector_store
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

tavily_client = TavilyClient(api_key=TAVILY_API_KEY or "dummy_key")

@tool
def search_web(query: str, search_depth: Literal["basic", "advanced", "fast", "ultra-fast"], num_results: int = 5, include_domains: List[str] = None, exclude_domains: List[str] = None) -> dict:
    """Search the web for real-time information using the Tavily search API.

    Use this tool when you need up-to-date information from the internet that
    is not available in the locally stored pages.

    Args:
        query: The search query string.
        search_depth: Controls the thoroughness of the search. Use ``"basic"`` or
            ``"fast"`` for quick lookups and ``"advanced"`` or ``"ultra-fast"``
            for more comprehensive results.
        num_results: Maximum number of search results to return. Defaults to 5.
        include_domains: Optional list of domains to restrict the search to.
        exclude_domains: Optional list of domains to exclude from results.

    Returns:
        A dictionary containing the search results with titles, URLs, and content
        snippets.
    """
    results = tavily_client.search(query=query, num_results=num_results, search_depth=search_depth, include_domains=include_domains, exclude_domains=exclude_domains)
    return results

@tool
def read_and_store_url(urls: List[str] | str, depth: Literal["basic", "advanced"] = "basic") -> str:
    """Extract content from one or more URLs and store them in the vector database.

    Fetches the raw text content of the given web pages, splits it into chunks,
    and persists the chunks in ChromaDB so they can later be queried with
    ``search_stored_pages``. Use this tool when you need to deeply read and
    remember the full content of a web page for future reference.

    Args:
        urls: A single URL string or a list of URLs to extract content from.
        depth: Extraction depth — ``"basic"`` for a fast, shallow extraction or
            ``"advanced"`` for a more thorough content extraction. Defaults to
            ``"basic"``.

    Returns:
        A status message indicating how many chunks were stored, or an error
        message if no content could be extracted.
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
    """Discover and map all linked URLs on a given web page.

    Crawls the provided base URL and returns a list of linked pages found on it,
    filtered by the given natural-language instructions. Use this tool when you
    need to understand the structure of a website or find specific sub-pages
    before reading their content.

    Args:
        base_url: The starting URL whose outbound links should be mapped.
        instructions: Natural-language instructions describing which types of
            links or pages to focus on (e.g., ``"find all blog post links"``).

    Returns:
        A list of discovered URLs matching the provided instructions.
    """
    results = tavily_client.map(url=base_url, instructions=instructions)
    return results["results"]
