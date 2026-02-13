"""Vector service for embedding and retrieval."""
import os
import pickle
import numpy as np
import faiss
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from core.config import settings
from domain.models import Document
from domain.exceptions import ExternalServiceError


class VectorService:
    """
    Handles text chunking, embedding generation, and semantic search.
    Optimized for performance with caching and efficient chunking.
    """
    
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.indices = {}
        self.documents = {}

    def chunk_text(self, text: str) -> List[str]:
        """
        Smart text chunking using sliding window with overlap.
        Respects sentence boundaries where possible.
        """
        chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP
        
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            
            # If we are not at the end of text, try to find a sentence break
            if end < text_len:
                # Look for the last period in the chunk
                last_period = text.rfind('.', start, end)
                if last_period != -1 and last_period > start + (chunk_size // 2):
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            
        return chunks

    def _get_index_path(self, kb_id: int) -> str:
        return str(settings.VECTOR_DIR / f"kb_{kb_id}.index")

    def _get_docs_path(self, kb_id: int) -> str:
        return str(settings.VECTOR_DIR / f"kb_{kb_id}_docs.pkl")

    def _load_index(self, kb_id: int):
        """Lazy load index for a KB."""
        if kb_id in self.indices:
            return

        index_path = self._get_index_path(kb_id)
        docs_path = self._get_docs_path(kb_id)

        if os.path.exists(index_path) and os.path.exists(docs_path):
            self.indices[kb_id] = faiss.read_index(index_path)
            with open(docs_path, 'rb') as f:
                self.documents[kb_id] = pickle.load(f)
        else:
            self.indices[kb_id] = faiss.IndexFlatL2(self.dimension)
            self.documents[kb_id] = []

    def _save_index(self, kb_id: int):
        """Persist index to disk."""
        faiss.write_index(self.indices[kb_id], self._get_index_path(kb_id))
        with open(self._get_docs_path(kb_id), 'wb') as f:
            pickle.dump(self.documents[kb_id], f)

    def add_document(self, kb_id: int, doc: Document):
        """Generate embeddings and add document to index."""
        self._load_index(kb_id)
        
        chunks = self.chunk_text(doc.content)
        if not chunks:
            return

        try:
            embeddings = self.model.encode(chunks, convert_to_numpy=True)
            self.indices[kb_id].add(embeddings.astype('float32'))
            
            # Store metadata
            for i, chunk in enumerate(chunks):
                self.documents[kb_id].append({
                    'text': chunk,
                    'doc_id': doc.id,
                    'source': doc.name,
                    'chunk_index': i
                })
            
            self._save_index(kb_id)
        except Exception as e:
            raise ExternalServiceError(f"Embedding generation failed: {e}")

    def search(self, kb_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Perform semantic search."""
        self._load_index(kb_id)
        
        if self.indices[kb_id].ntotal == 0:
            return []

        query_vector = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.indices[kb_id].search(query_vector.astype('float32'), limit)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.documents[kb_id]):
                doc = self.documents[kb_id][idx].copy()
                doc['score'] = float(1 / (1 + distances[0][i]))
                results.append(doc)
                
        return results

    def delete_kb_index(self, kb_id: int):
        """Delete index files for a KB."""
        if kb_id in self.indices:
            del self.indices[kb_id]
        if kb_id in self.documents:
            del self.documents[kb_id]
            
        index_path = self._get_index_path(kb_id)
        docs_path = self._get_docs_path(kb_id)
        
        if os.path.exists(index_path):
            os.remove(index_path)
        if os.path.exists(docs_path):
            os.remove(docs_path)
