"""All third-party search tool imports live here."""
from duckduckgo_search import DDGS
from wikipedia import summary as wiki_summary


class WebSearchAdapter:
    """Wraps DuckDuckGo search. Swap provider by changing only this file."""

    def search(self, query: str, max_results: int = 3) -> list[dict]:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            return [r for r in results]


class WikipediaAdapter:
    """Wraps Wikipedia lookup."""

    def get_summary(self, topic: str, sentences: int = 3) -> str:
        try:
            return wiki_summary(topic, sentences=sentences)
        except Exception:
            return ""
