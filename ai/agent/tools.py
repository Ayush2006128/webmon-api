import os

from pydantic.aliases import Literal
from typing import List
from langchain_core.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

@tool
def search_web(query: str, search_depth: Literal["basic", "advanced", "fast", "ultra-fast"], num_results: int = 5) -> dict:
    """
    Search the web for the given query and return the results.

    Args:
        query (str): The search query.
        num_results (int): The number of search results to return.
        search_depth (Literal["basic", "advanced", "fast", "ultra-fast"]): The depth to search.

    Returns:
        str: A string containing the search results.
    """
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    results = client.search(query=query, num_results=num_results, search_depth=search_depth)
    return results

@tool
def extract_web_content(urls: List[str] | str, depth: Literal["basic", "advanced"] = "basic") -> dict:
    """
    Extract the main content from a web page given its URL.

    Args:
        urls (List[str] | str): A list of URLs or a single URL of the web pages to extract content from.
        depth (Literal["basic", "advanced"]): The depth of content extraction.

    Returns:
        dict: A dictionary containing the extracted content from the web pages.
    """
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    content = client.extract(urls=urls, extract_depth=depth)
    # Truncate content to avoid token limits
    content_str = str(content)
    return content