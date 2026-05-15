import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    body: str
    href: str


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise e


class WebSearchService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        try:
            results = self.circuit_breaker.call(self._do_search, query, max_results)
            return results
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    def _do_search(self, query: str, max_results: int) -> list[SearchResult]:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            return [
                SearchResult(
                    title=r.get("title", ""),
                    body=r.get("body", ""),
                    href=r.get("href", "")
                )
                for r in results
            ]
