"""
Embedder module for converting text to embeddings.
Uses sentence-transformers or OpenAI embeddings.
"""

from typing import List, Union
import numpy as np


class Embedder:
    """Text to embeddings converter."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedder.
        
        Args:
            model_name: Name of the embedding model
        """
        self.model_name = model_name
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_embedding_dimension()
        except ImportError:
            print("sentence-transformers not installed. Using fallback embedder.")
            self.model = None
            self.embedding_dim = 384
    
    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Embed text to vector.
        
        Args:
            text: Single text or list of texts
            
        Returns:
            Embedding vector or matrix
        """
        if self.model is None:
            return self._fallback_embed(text)
        
        if isinstance(text, str):
            text = [text]
        
        embeddings = self.model.encode(text)
        
        if len(text) == 1:
            return embeddings[0]
        return embeddings
    
    def _fallback_embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Fallback embedding using hash-based method.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if isinstance(text, str):
            text = [text]
        
        embeddings = []
        for t in text:
            # Simple hash-based embedding (not production quality)
            hash_val = hash(t)
            np.random.seed(abs(hash_val) % (2**31))
            embedding = np.random.randn(self.embedding_dim)
            embeddings.append(embedding)
        
        embeddings = np.array(embeddings)
        if embeddings.shape[0] == 1:
            return embeddings[0]
        return embeddings
