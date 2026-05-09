"""LangGraph nodes for RAG orchestration."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class IntentType(Enum):
    QA = "qa"  # Question answering with knowledge base
    SEARCH = "search"  # Web search
    SUMMARIZE = "summarize"  # Document summarization
    CHAT = "chat"  # General conversation
    GENERAL = "general"  # Uncategorized


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    reasoning: str


@dataclass
class QueryResult:
    refined_query: str
    original_query: str
    corrections_applied: List[str]
    is_valid: bool


@dataclass
class EvaluationResult:
    confidence: float
    relevance: float
    is_valid: bool
    needs_correction: bool
    feedback: str


class IntentEvaluatorNode:
    """LangGraph node: Evaluates user intent from query."""

    QA_KEYWORDS = ["what", "how", "why", "explain", "tell me", "define", "describe"]
    SEARCH_KEYWORDS = ["find", "search", "look up", "google", "browse"]
    SUMMARIZE_KEYWORDS = ["summarize", "summary", "brief", "overview", "tldr"]

    def evaluate(self, query: str, kb_available: bool = True) -> IntentResult:
        """Evaluate user intent from query."""
        query_lower = query.lower()

        # Check for summarize intent
        if any(kw in query_lower for kw in self.SUMMARIZE_KEYWORDS):
            return IntentResult(
                intent=IntentType.SUMMARIZE,
                confidence=0.9,
                reasoning="Query contains summarize keywords",
            )

        # Check for search intent
        if any(kw in query_lower for kw in self.SEARCH_KEYWORDS):
            return IntentResult(
                intent=IntentType.SEARCH,
                confidence=0.85,
                reasoning="Query contains search keywords",
            )

        # Check for QA intent (if KB available)
        if kb_available and any(kw in query_lower for kw in self.QA_KEYWORDS):
            return IntentResult(
                intent=IntentType.QA,
                confidence=0.8,
                reasoning="Query appears to be a question",
            )

        # Default to chat if no KB, otherwise QA
        default_intent = IntentType.CHAT if not kb_available else IntentType.QA
        return IntentResult(
            intent=default_intent,
            confidence=0.6,
            reasoning="Default intent based on no keyword match",
        )


class QueryEvaluatorNode:
    """LangGraph node: Self-correcting RAG query refinement."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def evaluate(self, query: str, kb_context: Dict[str, Any] = None) -> QueryResult:
        """Refine and validate user query for retrieval."""
        kb_context = kb_context or {}
        corrections = []

        # Step 1: Query decomposition
        refined = self._decompose_query(query)
        if refined != query:
            corrections.append("query_decomposition")

        # Step 2: Expand with synonyms
        refined = self._expand_query(refined)
        if refined != query:
            corrections.append("synonym_expansion")

        # Step 3: Self-correction validation loop
        for attempt in range(self.max_retries):
            if self._validate_query(refined, kb_context):
                break
            refined = self._retry_correction(refined, attempt)
            corrections.append(f"retry_{attempt + 1}")

        return QueryResult(
            refined_query=refined,
            original_query=query,
            corrections_applied=corrections,
            is_valid=len(refined) > 0,
        )

    def _decompose_query(self, query: str) -> str:
        """Break down complex queries."""
        # Remove filler words
        filler_words = ["please", "could you", "would you", "kindly"]
        result = query.lower()
        for word in filler_words:
            result = result.replace(word, "")
        return result.strip()

    def _expand_query(self, query: str) -> str:
        """Expand query with relevant synonyms."""
        expansions = {
            "python": "python programming language",
            "js": "javascript",
            "ai": "artificial intelligence",
            "ml": "machine learning",
        }
        result = query
        for abbr, full in expansions.items():
            if abbr in result:
                result = result.replace(abbr, full)
        return result

    def _validate_query(self, query: str, context: Dict) -> bool:
        """Validate query is answerable."""
        if len(query) < 3:
            return False
        # Check for obvious non-questions that might indicate confusion
        return True

    def _retry_correction(self, query: str, attempt: int) -> str:
        """Apply correction on retry."""
        # Simple reformatting on retry
        return query.strip()


class ResultEvaluatorNode:
    """LangGraph node: Validates and scores final results."""

    def __init__(self, min_confidence: float = 0.5, min_relevance: float = 0.3):
        self.min_confidence = min_confidence
        self.min_relevance = min_relevance

    def evaluate(
        self, results: List[Dict[str, Any]], answer: str, original_query: str
    ) -> EvaluationResult:
        """Evaluate and score final results."""
        confidence = self._calculate_confidence(results, answer)
        relevance = self._check_relevance(answer, original_query, results)

        needs_correction = (
            confidence < self.min_confidence or relevance < self.min_relevance
        )

        feedback = ""
        if needs_correction:
            if confidence < self.min_confidence:
                feedback += "Low confidence - "
            if relevance < self.min_relevance:
                feedback += "Low relevance - "
            feedback = feedback.rstrip(" - ")

        return EvaluationResult(
            confidence=confidence,
            relevance=relevance,
            is_valid=confidence >= self.min_confidence
            and relevance >= self.min_relevance,
            needs_correction=needs_correction,
            feedback=feedback,
        )

    def _calculate_confidence(self, results: List[Dict], answer: str) -> float:
        """Calculate confidence score based on retrieved sources."""
        if not results:
            return 0.0

        # Average of source scores
        scores = [r.get("score", 0) for r in results]
        avg_score = sum(scores) / len(scores)

        # Penalize empty answers
        if not answer or len(answer) < 10:
            return 0.0

        # Check answer consistency with sources
        answer_words = set(re.findall(r"\w+", answer.lower()))
        consistent_sources = 0

        for result in results[:3]:
            source_text = result.get("text", "").lower()
            source_words = set(re.findall(r"\w+", source_text))
            overlap = len(answer_words & source_words)
            if overlap > len(answer_words) * 0.2:
                consistent_sources += 1

        consistency = consistent_sources / min(3, len(results))

        return min((avg_score * 0.6) + (consistency * 0.4), 1.0)

    def _check_relevance(
        self, answer: str, original_query: str, results: List[Dict]
    ) -> float:
        """Check if answer is relevant to the query."""
        if not results:
            return 0.0

        query_words = set(re.findall(r"\w+", original_query.lower()))
        answer_words = set(re.findall(r"\w+", answer.lower()))

        overlap = len(query_words & answer_words)
        relevance = overlap / len(query_words) if query_words else 0

        return min(relevance + 0.3, 1.0)  # Base score of 0.3


class RAGOrchestrator:
    """Main orchestrator combining all LangGraph nodes."""

    def __init__(self, llm_service=None):
        """Initialize with any LLM service (GroqService or OllamaService)."""
        self.llm_service = llm_service
        self.intent_evaluator = IntentEvaluatorNode()
        self.query_evaluator = QueryEvaluatorNode()
        self.result_evaluator = ResultEvaluatorNode()

    def chat(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a chat query through the RAG pipeline."""
        context = context or {}
        kb_ids = context.get("kb_ids", [])
        if context.get("kb_id") and context.get("kb_id") not in kb_ids:
            kb_ids.append(context.get("kb_id"))
            
        web_results = context.get("web_results", [])

        # Get conversation history context
        history = context.get("history", [])

        # Step 1: Intent Evaluation
        kb_available = len(kb_ids) > 0
        intent_result = self.intent_evaluator.evaluate(query, kb_available)

        # Step 2: Query Evaluation (only for QA)
        query_result = None
        refined_query = query
        if intent_result.intent == IntentType.QA:
            query_result = self.query_evaluator.evaluate(query, context)
            refined_query = query_result.refined_query if query_result else query

        # Step 3: Build prompt with context
        prompt_context, all_retrieved_snippets = self._build_context(refined_query, kb_ids, web_results, history)

        # Step 4: Generate response if LLM service is available
        response_text = ""
        if self.llm_service:
            response_text = self._generate_response(query, prompt_context, intent_result)
        else:
            response_text = "No LLM provider configured. Add a GROQ API key or install Ollama."

        # Step 5: Evaluate result
        evaluation = self.result_evaluator.evaluate(
            all_retrieved_snippets, response_text, query
        )

        return {
            "response": response_text,
            "intent": intent_result.intent.value,
            "confidence": str(round(evaluation.confidence * 100, 1)) + "%",
            "sources": all_retrieved_snippets
        }

    def _build_context(self, query: str, kb_ids: List[int], web_results: List[Dict], history: List[Dict]) -> Tuple[str, List[Dict]]:
        """Build context string from various sources and return source list."""
        context_parts = []
        all_sources = []

        # 1. Search Knowledge Bases
        if kb_ids:
            from ..search.dynamic_index import IndexManager
            from ...infrastructure.database.database import Database
            from ...domain.models import Document
            from ...core.settings import get_settings
            
            db_url = get_settings().db_url
            db = Database(db_url)
            
            with db.session() as session:
                for kb_id in kb_ids:
                    # Get all indexed documents for this KB
                    docs = session.query(Document).filter(
                        Document.kb_id == kb_id, 
                        Document.index_status == "indexed"
                    ).all()
                    
                    if not docs:
                        continue
                        
                    doc_ids = [d.id for d in docs]
                    index_mgr = IndexManager(kb_id)
                    
                    try:
                        results = index_mgr.search_kb(query, doc_ids, top_k=5)
                        for r in results:
                            # Find the doc title for better context
                            doc_title = next((d.title for d in docs if str(d.id) == str(r["doc_id"])), "Document")
                            all_sources.append({
                                "title": doc_title,
                                "text": r["text"],
                                "score": r.get("combined_score", 0.5),
                                "kb_id": kb_id
                            })
                    except Exception as e:
                        logger.error(f"Search failed for KB {kb_id}: {e}")

            if all_sources:
                # Sort by score and take top 5
                all_sources.sort(key=lambda x: x["score"], reverse=True)
                top_sources = all_sources[:5]
                kb_context = "\n\n".join([
                    f"--- Source: {s['title']} ---\n{s['text']}"
                    for s in top_sources
                ])
                context_parts.append(f"[Knowledge Base Context]\n{kb_context}")

        # Add web results
        if web_results:
            web_context = "\n".join([
                f"- {r.get('title', '')}: {r.get('body', '')[:200]}..."
                for r in web_results[:3]
            ])
            context_parts.append(f"[Web Search Results]\n{web_context}")

        # Add conversation history
        if history:
            history_text = "\n".join([
                f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')[:200]}"
                for m in history[-5:]
            ])
            context_parts.append(f"[Conversation History]\n{history_text}")

        return "\n\n".join(context_parts) if context_parts else "[No context available]", all_sources

    def _generate_response(self, query: str, context: str, intent_result: IntentResult) -> str:
        """Generate response using LLM with context."""
        if not self.llm_service:
            return "No LLM service configured."

        system_prompt = """You are a helpful AI assistant. Use the provided context to answer questions accurately.
If the context doesn't contain relevant information, say so and provide your best general answer.
Always be concise and helpful."""

        user_prompt = f"""Context:
{context}

User Question: {query}

Provide a helpful, accurate response based on the context if available."""

        # Build messages using a simple dataclass compatible with both services
        from dataclasses import dataclass

        @dataclass
        class _ChatMsg:
            role: str
            content: str

        messages = [
            _ChatMsg(role="system", content=system_prompt),
            _ChatMsg(role="user", content=user_prompt),
        ]

        try:
            return self.llm_service.chat_completion(
                messages,
                temperature=0.3,
                max_tokens=1024,
            )
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return f"I apologize, but I encountered an error generating a response: {str(e)}"

    def process(
        self,
        query: str,
        kb_context: Dict[str, Any] = None,
        use_web_search: bool = False,
    ) -> Dict[str, Any]:
        """Process query through all LangGraph nodes (legacy method)."""
        kb_available = kb_context.get("has_kb", False) if kb_context else False

        # Step 1: Intent Evaluation
        intent_result = self.intent_evaluator.evaluate(query, kb_available)

        # Step 2: Query Evaluation (only for QA)
        query_result = None
        if intent_result.intent == IntentType.QA:
            query_result = self.query_evaluator.evaluate(query, kb_context)

        # Step 3: Return processing info for downstream
        return {
            "intent": intent_result.intent.value,
            "intent_confidence": intent_result.confidence,
            "intent_reasoning": intent_result.reasoning,
            "refined_query": query_result.refined_query if query_result else query,
            "query_corrections": query_result.corrections_applied
            if query_result
            else [],
            "query_valid": query_result.is_valid if query_result else True,
        }

    def evaluate_result(
        self, results: List[Dict], answer: str, original_query: str
    ) -> EvaluationResult:
        """Evaluate final results."""
        return self.result_evaluator.evaluate(results, answer, original_query)
