import logging
from typing import Any

import httpx
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class WebSearchEngine:
    def __init__(self, serper_api_key: str | None = None):
        self.serper_api_key = serper_api_key

    def search(self, query: str, num_results: int = 5) -> list[dict[str, Any]]:
        """Perform web search using Serper (if key available) or DuckDuckGo fallback."""
        results = []

        # 1. Try Serper if key is provided
        if self.serper_api_key:
            try:
                headers = {
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                }
                payload = {"q": query, "num": num_results}
                resp = httpx.post("https://google.serper.dev/search", headers=headers, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("organic", []):
                        results.append({
                            "title": item.get("title", ""),
                            "href": item.get("link", ""),
                            "body": item.get("snippet", "")
                        })
                    if results:
                        logger.info(f"Serper search successful: {len(results)} results")
                        return results
            except Exception as e:
                logger.warning(f"Serper search failed: {e}")

        # 2. Fallback to DuckDuckGo
        try:
            logger.info(f"Falling back to DuckDuckGo for query: {query}")
            with DDGS(timeout=10) as ddgs:
                ddg_results = list(ddgs.text(query, max_results=num_results))
                for r in ddg_results:
                    results.append({
                        "title": r.get("title", ""),
                        "href": r.get("href", ""),
                        "body": r.get("body", "")
                    })
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")

        return results
