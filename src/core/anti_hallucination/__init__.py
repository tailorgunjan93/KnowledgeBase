"""Anti-Hallucination mechanisms for RAG."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Source:
    doc_id: str
    text: str
    score: float


@dataclass
class ConfidenceResult:
    answer: str
    confidence: float
    sources: List[Source]
    needs_correction: bool = False
    corrected_answer: Optional[str] = None


class AntiHallucination:
    """Anti-hallucination with source attribution and confidence scoring."""

    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence

    def evaluate(self, answer: str, sources: List[Dict[str, Any]]) -> ConfidenceResult:
        """Evaluate answer against sources for hallucination."""
        source_objs = [
            Source(s["doc_id"], s["text"], s.get("score", 0)) for s in sources
        ]

        source_score = self._calculate_source_score(sources)
        consistency_score = self._check_consistency(answer, sources)

        confidence = (source_score * 0.6) + (consistency_score * 0.4)
        needs_correction = confidence < self.min_confidence

        return ConfidenceResult(
            answer=answer,
            confidence=confidence,
            sources=source_objs,
            needs_correction=needs_correction,
        )

    def _calculate_source_score(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate score based on source relevance."""
        if not sources:
            return 0.0

        scores = [s.get("score", 0) for s in sources]
        return min(sum(scores) / len(scores), 1.0)

    def _check_consistency(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """Check if answer is consistent with sources."""
        if not sources:
            return 0.0

        answer_lower = answer.lower()
        matches = 0

        for source in sources:
            source_text = source.get("text", "").lower()
            answer_words = set(re.findall(r"\w+", answer_lower))

            source_words = set(re.findall(r"\w+", source_text))
            overlap = len(answer_words & source_words)

            if overlap > len(answer_words) * 0.3:
                matches += 1

        return matches / len(sources)


class SelfCorrector:
    """Self-correction loop for refining outputs."""

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    async def correct(
        self,
        answer: str,
        sources: List[Dict[str, Any]],
        llm_client: Any,
        correction_prompt: str,
    ) -> str:
        """Attempt to correct the answer."""
        for attempt in range(self.max_retries):
            prompt = correction_prompt.format(
                original_answer=answer,
                sources="\n\n".join([s["text"] for s in sources[:3]]),
            )

            try:
                response = await llm_client.complete(prompt)
                if not response.choices:
                    logger.warning("Correction attempt returned no choices")
                    continue
                new_answer = response.choices[0].message.content

                if self._is_valid_correction(answer, new_answer):
                    return new_answer

            except Exception as e:
                logger.warning(f"Correction attempt {attempt + 1} failed: {e}")

        return answer

    def _is_valid_correction(self, original: str, corrected: str) -> bool:
        """Check if correction is valid."""
        if not corrected or len(corrected) < 10:
            return False
        if abs(len(corrected) - len(original)) > len(original) * 0.5:
            return False
        return True
