"""Document summarization module."""

from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)


class Summarizer:
    """Document summarization using LLM."""

    def __init__(self, model: str = "openai/gpt-oss-120b"):
        self.model = model

    def summarize_text(self, text: str, api_key: str = None, max_length: int = 500) -> Dict[str, Any]:
        """Summarize raw text."""
        api_key = api_key or os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return {"error": "GROQ_API_KEY not configured"}

        # Truncate text if too long
        text = text[:10000] if len(text) > 10000 else text

        try:
            # Try LangChain first
            try:
                from langchain_groq import ChatGroq
                from langchain.chains.summarize import load_summarize_chain
                from langchain_core.documents import Document

                llm = ChatGroq(temperature=0.3, model_name=self.model, groq_api_key=api_key)
                chain = load_summarize_chain(llm, chain_type="stuff")
                docs = [Document(page_content=text)]
                summary_res = chain.invoke(docs)
                summary = summary_res.get('output_text') or str(summary_res)
            except Exception as lc_err:
                logger.warning(f"LangChain summarization failed, falling back to direct call: {lc_err}")
                # Fallback to direct GroqService call if available
                try:
                    from ...services.groq_service import GroqService, ChatMessage
                    gs = GroqService(api_key=api_key)
                    prompt = f"Summarize the following text in about {max_length} words:\n\n{text}"
                    summary = gs.chat_completion([ChatMessage(role="user", content=prompt)])
                except Exception as gs_err:
                    raise Exception(f"Both LangChain and Direct LLM failed. LC: {lc_err}, GS: {gs_err}")

            # Extract key points
            key_points = self._extract_key_points(summary)

            return {
                "summary": summary,
                "key_points": key_points,
                "original_length": len(text),
                "summary_length": len(summary),
            }
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return {"error": str(e)}

    def summarize_document(self, document_id: int, content: str) -> Dict[str, Any]:
        """Summarize a document."""
        return self.summarize_text(content)

    def _extract_key_points(self, summary: str) -> List[str]:
        """Extract key points from summary."""
        # Simple extraction - split by sentences or bullet points
        lines = summary.split("\n")
        key_points = []

        for line in lines:
            line = line.strip()
            # Remove bullet points and numbers
            line = line.lstrip("-*•").lstrip("0123456789.").strip()
            if line and len(line) > 20:
                key_points.append(line)

        # If no bullet points, create key points from sentences
        if not key_points:
            sentences = summary.split(".")
            for sentence in sentences[:5]:
                sentence = sentence.strip()
                if len(sentence) > 20:
                    key_points.append(sentence)

        return key_points[:5]  # Limit to 5 key points


class ChunkProcessor:
    """Process and chunk documents for indexing."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
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

    def chunk_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Chunk a file based on its type."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
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
