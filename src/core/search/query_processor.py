import logging
from typing import List, Optional
from src.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)

class QueryProcessor:
    """Handles advanced query transformations like HyDE and Query Expansion."""

    def __init__(self, llm: LLMPort):
        self.llm = llm

    async def generate_hypothetical_document(self, query: str) -> str:
        """HyDE: Generate a hypothetical answer to improve vector search."""
        logger.info(f"Generating HyDE document for query: {query[:50]}...")
        prompt = (
            "Given the following question, please write a brief, hypothetical answer "
            "that contains the key information needed to address it. Do not include "
            "introductory phrases like 'Here is a hypothetical answer'. Just provide the answer content.\n\n"
            f"Question: {query}\n\n"
            "Hypothetical Answer:"
        )
        
        messages = [{"role": "user", "content": prompt}]
        try:
            # We use the direct chat method
            response = self.llm.chat(messages)
            return response.strip()
        except Exception as e:
            logger.error(f"HyDE generation failed: {e}")
            return query # Fallback to original query

    async def expand_query(self, query: str, num_variations: int = 3) -> List[str]:
        """Query Expansion: Generate multiple variations of the query."""
        logger.info(f"Expanding query: {query[:50]}...")
        prompt = (
            "You are an AI search assistant. Your task is to expand the user's query into "
            f"{num_variations} distinct variations that capture different nuances and potential keywords "
            "related to the topic. These variations will be used to improve document retrieval. "
            "Output only the queries, one per line, with no numbering or bullets.\n\n"
            f"Query: {query}\n\n"
            "Expanded Queries:"
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            response = self.llm.chat(messages)
            variations = [line.strip() for line in response.split("\n") if line.strip()]
            # Ensure we include the original query
            if query not in variations:
                variations.insert(0, query)
            return variations[:num_variations + 1]
        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return [query]
