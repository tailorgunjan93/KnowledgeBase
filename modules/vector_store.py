"""Vector store for semantic search using FAISS and sentence transformers."""
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import pickle
import os
from utils.helpers import chunk_text


class VectorStore:
    """Handles vector embeddings and semantic search using FAISS."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize vector store with embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.indices = {}  # kb_id -> FAISS index
        self.documents = {}  # kb_id -> list of document chunks with metadata
        self.vector_dir = "vector_data"
        
        # Create vector data directory
        os.makedirs(self.vector_dir, exist_ok=True)
    
    def _get_index_path(self, kb_id: int) -> str:
        """Get file path for KB index."""
        return os.path.join(self.vector_dir, f"kb_{kb_id}.index")
    
    def _get_docs_path(self, kb_id: int) -> str:
        """Get file path for KB documents."""
        return os.path.join(self.vector_dir, f"kb_{kb_id}_docs.pkl")
    
    def _load_or_create_index(self, kb_id: int) -> faiss.Index:
        """Load existing index or create new one for KB."""
        index_path = self._get_index_path(kb_id)
        docs_path = self._get_docs_path(kb_id)
        
        if os.path.exists(index_path) and os.path.exists(docs_path):
            # Load existing index
            index = faiss.read_index(index_path)
            with open(docs_path, 'rb') as f:
                self.documents[kb_id] = pickle.load(f)
        else:
            # Create new index
            index = faiss.IndexFlatL2(self.dimension)
            self.documents[kb_id] = []
        
        return index
    
    def _save_index(self, kb_id: int):
        """Save index and documents to disk."""
        if kb_id not in self.indices:
            return
        
        index_path = self._get_index_path(kb_id)
        docs_path = self._get_docs_path(kb_id)
        
        faiss.write_index(self.indices[kb_id], index_path)
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents[kb_id], f)
    
    def add_document(self, kb_id: int, text: str, metadata: Dict):
        """
        Add a document to the vector store.
        
        Args:
            kb_id: Knowledge base ID
            text: Document text content
            metadata: Document metadata (name, file_type, etc.)
        """
        # Load or create index for this KB
        if kb_id not in self.indices:
            self.indices[kb_id] = self._load_or_create_index(kb_id)
        
        # Chunk the text
        chunks = chunk_text(text, chunk_size=1000, overlap=200)
        
        # Generate embeddings for each chunk
        embeddings = self.model.encode(chunks, convert_to_numpy=True)
        
        # Add to FAISS index
        self.indices[kb_id].add(embeddings.astype('float32'))
        
        # Store document chunks with metadata
        for i, chunk in enumerate(chunks):
            self.documents[kb_id].append({
                'text': chunk,
                'metadata': metadata,
                'chunk_index': i
            })
        
        # Save to disk
        self._save_index(kb_id)
    
    def search(self, kb_id: int, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant documents using semantic similarity.
        
        Args:
            kb_id: Knowledge base ID
            query: Search query
            top_k: Number of top results to return
        
        Returns:
            List of document chunks with metadata and scores
        """
        # Load index if not in memory
        if kb_id not in self.indices:
            self.indices[kb_id] = self._load_or_create_index(kb_id)
        
        # Check if index is empty
        if self.indices[kb_id].ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search
        top_k = min(top_k, self.indices[kb_id].ntotal)
        distances, indices = self.indices[kb_id].search(query_embedding.astype('float32'), top_k)
        
        # Prepare results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents[kb_id]):
                doc = self.documents[kb_id][idx].copy()
                doc['score'] = float(1 / (1 + dist))  # Convert distance to similarity score
                doc['rank'] = i + 1
                results.append(doc)
        
        return results
    
    def delete_kb_data(self, kb_id: int):
        """
        Delete all vector data for a knowledge base.
        
        Args:
            kb_id: Knowledge base ID
        """
        # Remove from memory
        if kb_id in self.indices:
            del self.indices[kb_id]
        if kb_id in self.documents:
            del self.documents[kb_id]
        
        # Delete files
        index_path = self._get_index_path(kb_id)
        docs_path = self._get_docs_path(kb_id)
        
        if os.path.exists(index_path):
            os.remove(index_path)
        if os.path.exists(docs_path):
            os.remove(docs_path)
    
    def get_all_documents(self, kb_id: int) -> List[Dict]:
        """
        Get all documents in a knowledge base.
        
        Args:
            kb_id: Knowledge base ID
        
        Returns:
            List of all document chunks
        """
        if kb_id not in self.documents:
            self._load_or_create_index(kb_id)
        
        return self.documents.get(kb_id, [])
