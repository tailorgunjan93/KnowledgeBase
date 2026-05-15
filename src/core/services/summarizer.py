"""Document summarization module with LLM provider fallback."""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class Summarizer:
    """Document summarization using LLM (Groq or local Ollama)."""

    def __init__(self, model: str | None = None):
        from ...shared.config import get_settings
        settings = get_settings()
        # Safely get model from settings or fallback
        self.model = model or getattr(settings, "summarizer_model", "llama-3.1-8b-instant")
        self.max_chunk_chars = 12000
        self.max_workers = 3 # Conservative for low rate limits

    def summarize_text(
        self, text: str, api_key: str = None, max_length: int = 500
    ) -> dict[str, Any]:
        """Summarize raw text using best available LLM provider (legacy path)."""
        original_len = len(text)
        try:
            if len(text) > self.max_chunk_chars:
                summary = self._summarize_large_text(text, api_key, max_length)
            else:
                summary = self._generate_summary(text, api_key, max_length)
            key_points = self._extract_key_points(summary)
            return {
                "summary": summary,
                "key_points": key_points,
                "original_length": original_len,
                "summary_length": len(summary),
            }
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return {"error": str(e)}

    def summarize_text_with_llm(
        self, text: str, llm, max_length: int = 500
    ) -> dict[str, Any]:
        """Summarize using an injected LLM adapter (supports all providers)."""
        original_len = len(text)
        try:
            if len(text) > self.max_chunk_chars:
                summary = self._summarize_large_with_llm(text, llm, max_length)
            else:
                summary = self._generate_with_llm(text, llm, max_length)
            key_points = self._extract_key_points(summary)
            return {
                "summary": summary,
                "key_points": key_points,
                "original_length": original_len,
                "summary_length": len(summary),
            }
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return {"error": str(e)}

    def _generate_with_llm(self, text: str, llm, max_length: int) -> str:
        messages = [
            {"role": "system", "content": "You are a precise document summarizer."},
            {"role": "user", "content": (
                f"Summarize the following text in about {max_length} words. "
                f"Be concise, clear, and capture the key points:\n\n{text}"
            )},
        ]
        return llm.chat(messages, max_tokens=max_length * 5)

    def _summarize_large_with_llm(self, text: str, llm, max_length: int) -> str:
        from concurrent.futures import ThreadPoolExecutor
        chunks = [text[i:i + self.max_chunk_chars] for i in range(0, len(text), self.max_chunk_chars)]
        chunks = chunks[:15]
        logger.info(f"Summarizing {len(chunks)} chunks with injected LLM...")

        def _chunk(chunk):
            return self._generate_with_llm(
                f"Provide a brief 2-paragraph technical summary of this section:\n\n{chunk}",
                llm, max_length // 2,
            )

        with ThreadPoolExecutor(max_workers=min(len(chunks), self.max_workers)) as ex:
            chunk_summaries = list(ex.map(_chunk, chunks))

        combined = "\n\n".join(chunk_summaries)
        return self._generate_with_llm(
            f"Below are summaries of different sections. Create a final cohesive summary "
            f"of about {max_length} words covering all key points:\n\n{combined}",
            llm, max_length,
        )

    def _summarize_large_text(self, text: str, api_key: str, max_length: int) -> str:
        """Handle large text by summarizing chunks in parallel."""
        from concurrent.futures import ThreadPoolExecutor

        # Split into chunks
        chunks = [text[i:i + self.max_chunk_chars] for i in range(0, len(text), self.max_chunk_chars)]
        # Limit chunks to prevent excessive API calls
        chunks = chunks[:15] # Max 180k chars (roughly 45k tokens)

        logger.info(f"Summarizing {len(chunks)} chunks in parallel (max_workers={self.max_workers})...")

        def summarize_chunk(chunk):
            chunk_prompt = f"Provide a brief, 2-paragraph technical summary of this document section:\n\n{chunk}"
            return self._generate_summary(chunk_prompt, api_key, max_length // 2)

        with ThreadPoolExecutor(max_workers=min(len(chunks), self.max_workers)) as executor:
            chunk_summaries = list(executor.map(summarize_chunk, chunks))

        # Final combined summary
        combined_text = "\n\n".join(chunk_summaries)
        final_prompt = (
            f"Below are summaries of different sections of a large document. "
            f"Create a final, cohesive summary of about {max_length} words that covers all key points:\n\n"
            f"{combined_text}"
        )
        return self._generate_summary(final_prompt, api_key, max_length)

    def _generate_summary(
        self, text: str, api_key: str | None, max_length: int
    ) -> str:
        """Generate summary using the best available LLM."""
        import sys
        prompt = (
            f"Summarize the following text in about {max_length} words. "
            f"Be concise, clear, and capture the key points:\n\n{text}"
        )
        print(f"DEBUG Summarizer: text_len={len(text)}, max_length={max_length}", file=sys.stderr)

        # Try Groq first (via LangChain)
        if api_key or os.getenv("GROQ_API_KEY"):
            try:
                result = self._summarize_with_groq(prompt, api_key)
                print(f"DEBUG Summarizer: Groq returned len={len(result)}", file=sys.stderr)
                return result
            except Exception as e:
                print(f"DEBUG Summarizer: Groq failed: {e}", file=sys.stderr)

        # Fallback: Ollama (local, free)
        try:
            result = self._summarize_with_ollama(prompt)
            print(f"DEBUG Summarizer: Ollama returned len={len(result)}", file=sys.stderr)
            return result
        except Exception as e:
            print(f"DEBUG Summarizer: Ollama failed: {e}", file=sys.stderr)

        raise Exception(
            "No LLM provider available. Set GROQ_API_KEY or install Ollama."
        )

    def _summarize_with_groq(self, prompt: str, api_key: str | None) -> str:
        """Summarize using Groq cloud LLM."""
        resolved_key = api_key or os.getenv("GROQ_API_KEY", "")
        if not resolved_key:
            raise ValueError("No Groq API key")

        import time
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                from langchain_groq import ChatGroq

                model_name = self.model or "llama-3.1-8b-instant"
                llm = ChatGroq(
                    temperature=0.3,
                    model_name=model_name,
                    groq_api_key=resolved_key,
                )
                messages = [
                    SystemMessage(content="You are a precise document summarizer."),
                    HumanMessage(content=prompt),
                ]
                response = llm.invoke(messages)
                return response.content
            except Exception as lc_err:
                if "rate_limit" in str(lc_err).lower() and attempt < max_retries - 1:
                    logger.warning(f"Rate limit hit, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue

                logger.warning(f"LangChain Groq failed: {lc_err}")
                # Fallback to direct Groq SDK
                from ...services.groq_service import ChatMessage, GroqService
                gs = GroqService(api_key=resolved_key)
                return gs.chat_completion(
                    [ChatMessage(role="user", content=prompt)]
                )

    def _summarize_with_ollama(self, prompt: str) -> str:
        """Summarize using local Ollama LLM (free)."""
        from ...services.ollama_service import ChatMessage, OllamaService

        svc = OllamaService()
        if not svc.is_available():
            raise Exception("Ollama is not running")

        return svc.chat_completion(
            [ChatMessage(role="user", content=prompt)],
            temperature=0.3,
            max_tokens=2048,
        )

    def summarize_document(
        self, document_id: int, content: str
    ) -> dict[str, Any]:
        """Summarize a document."""
        return self.summarize_text(content)

    def _extract_key_points(self, summary: str) -> list[str]:
        """Extract key points from summary."""
        lines = summary.split("\n")
        key_points = []

        # Only attempt bullet/numbered-list parsing when the summary has multiple lines
        if len(lines) > 1:
            for line in lines:
                line = line.strip()
                line = line.lstrip("-*•").lstrip("0123456789.").strip()
                if line and len(line) > 20:
                    key_points.append(line)

        # Fallback: plain-prose input (single line) or no structured points found
        if not key_points:
            sentences = summary.split(".")
            for sentence in sentences[:5]:
                sentence = sentence.strip()
                if len(sentence) > 20:
                    key_points.append(sentence)

        return key_points[:5] if key_points else []


class ChunkProcessor:
    """Process and chunk documents for indexing."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> list[dict[str, Any]]:
        """Split text into overlapping chunks with metadata."""
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i : i + self.chunk_size]
            chunk_text = " ".join(chunk_words)

            if chunk_text:
                chunks.append(
                    {
                        "text": chunk_text,
                        "word_count": len(chunk_words),
                        "start_index": i,
                        "end_index": i + len(chunk_words),
                    }
                )

        return chunks

    def chunk_file(self, file_path: str) -> list[dict[str, Any]]:
        """Chunk a file based on its type."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
        elif ext == ".pdf":
            try:
                import pdfplumber

                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            except Exception as e:
                logger.error(f"Failed to read PDF: {e}")
                return []
        elif ext in [".doc", ".docx"]:
            try:
                from docx import Document

                doc = Document(file_path)
                text = "\n".join(p.text for p in doc.paragraphs)
            except Exception as e:
                logger.error(f"Failed to read DOCX: {e}")
                return []
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return []

        return self.chunk_text(text)
