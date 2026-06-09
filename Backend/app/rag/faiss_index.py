"""
FAISS index management for vector similarity search.
Handles creation, loading, and searching of FAISS indices.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
import os
import json


class FAISSIndex:
    """FAISS index wrapper for similarity search."""
    
    def __init__(self, dimension: int = 384, metric: str = "l2"):
        """
        Initialize FAISS index.
        
        Args:
            dimension: Dimension of embeddings
            metric: Distance metric (l2 or inner_product)
        """
        self.dimension = dimension
        self.metric = metric
        self.index = None
        self.id_map = []
        self.documents = []
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize the FAISS index."""
        try:
            import faiss
            
            if self.metric == "l2":
                self.index = faiss.IndexFlatL2(self.dimension)
            else:
                self.index = faiss.IndexFlatIP(self.dimension)
            
            self.faiss_available = True
        except ImportError:
            print("FAISS not installed. Using basic list-based index.")
            self.faiss_available = False
            self.vectors = []
    
    def add(
        self,
        embeddings: np.ndarray,
        documents: List[Dict],
        start_id: int = 0
    ):
        """
        Add vectors to index.
        
        Args:
            embeddings: Array of embeddings
            documents: Corresponding documents/metadata
            start_id: Starting ID for documents
        """
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        
        if self.faiss_available:
            self.index.add(embeddings.astype('float32'))
        else:
            self.vectors.extend(embeddings.tolist())
        
        for i, doc in enumerate(documents):
            doc_id = start_id + i
            self.id_map.append(doc_id)
            self.documents.append(doc)
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        threshold: Optional[float] = None
    ) -> Tuple[List[float], List[Dict]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results
            threshold: Optional distance threshold
            
        Returns:
            Tuple of (distances, documents)
        """
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        if self.faiss_available:
            distances, indices = self.index.search(
                query_embedding.astype('float32'),
                min(k, len(self.documents))
            )
            distances = distances[0].tolist()
            indices = indices[0].tolist()
        else:
            distances, indices = self._naive_search(query_embedding[0], k)
        
        results = []
        for dist, idx in zip(distances, indices):
            if idx >= 0 and (threshold is None or dist <= threshold):
                if idx < len(self.documents):
                    results.append(self.documents[idx])
        
        return distances, results
    
    def _naive_search(
        self,
        query: np.ndarray,
        k: int
    ) -> Tuple[List[float], List[int]]:
        """
        Naive search implementation without FAISS.
        
        Args:
            query: Query vector
            k: Number of results
            
        Returns:
            Tuple of (distances, indices)
        """
        if not self.vectors:
            return [], []
        
        vectors = np.array(self.vectors)
        distances = np.linalg.norm(vectors - query, axis=1)
        indices = np.argsort(distances)[:k]
        
        return distances[indices].tolist(), indices.tolist()
    
    def save(self, path: str):
        """
        Save index to disk.
        
        Args:
            path: Path to save index
        """
        try:
            os.makedirs(path, exist_ok=True)
            if self.faiss_available:
                import faiss
                faiss.write_index(self.index, os.path.join(path, "index.faiss"))
            else:
                np.save(os.path.join(path, "vectors.npy"), np.array(self.vectors, dtype="float32"))

            with open(os.path.join(path, "documents.json"), "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=True, indent=2)
            with open(os.path.join(path, "id_map.json"), "w", encoding="utf-8") as f:
                json.dump(self.id_map, f)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def load(self, path: str):
        """
        Load index from disk.
        
        Args:
            path: Path to load index from
        """
        try:
            if self.faiss_available:
                import faiss
                index_path = os.path.join(path, "index.faiss")
                if os.path.exists(index_path):
                    self.index = faiss.read_index(index_path)
            else:
                vectors_path = os.path.join(path, "vectors.npy")
                if os.path.exists(vectors_path):
                    vectors = np.load(vectors_path)
                    self.vectors = vectors.tolist()

            documents_path = os.path.join(path, "documents.json")
            id_map_path = os.path.join(path, "id_map.json")
            if os.path.exists(documents_path):
                with open(documents_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
            if os.path.exists(id_map_path):
                with open(id_map_path, "r", encoding="utf-8") as f:
                    self.id_map = json.load(f)
        except Exception as e:
            print(f"Error loading index: {e}")
