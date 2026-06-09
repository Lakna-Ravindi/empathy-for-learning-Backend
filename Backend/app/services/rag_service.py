"""
RAG (Retrieval-Augmented Generation) service.
Retrieves relevant PDF knowledge from a persistent vector index.
"""

from typing import List, Dict, Any, Optional
import os

from app.rag.embedder import Embedder
from app.rag.faiss_index import FAISSIndex

class RAGService:
    """Service for retrieving relevant knowledge from ingested PDF chunks."""

    def __init__(self, index_dir: Optional[str] = None):
        """Initialize the RAG service and load persisted index data."""
        base_dir = os.path.dirname(__file__)
        self.index_dir = index_dir or os.path.abspath(
            os.path.join(base_dir, "../../data/vector_index")
        )
        self.embedder = Embedder()
        self.index = FAISSIndex(dimension=self.embedder.embedding_dim, metric="l2")
        self._load_index()

    def _load_index(self) -> None:
        """Load FAISS index and chunk metadata from disk."""
        if not os.path.exists(self.index_dir):
            print(
                "RAG index not found. Run `python scripts/ingest_pdfs.py` "
                "to build the PDF knowledge index."
            )
            return
        self.index.load(self.index_dir)

    def search(
        self,
        query: str,
        skill: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge chunks.
        
        Args:
            query: Search query
            skill: Optional skill to filter by
            top_k: Number of results to return
            
        Returns:
            List of relevant knowledge chunks
        """
        if not self.index.documents:
            return []

        query_embedding = self.embedder.embed(query)
        # Pull a wider candidate set, then apply skill-aware reranking.
        candidate_k = max(top_k * 4, top_k)
        distances, docs = self.index.search(query_embedding, k=candidate_k)

        ranked: List[tuple[float, Dict[str, Any]]] = []
        for distance, doc in zip(distances, docs):
            chunk_skill = str(doc.get("skill", "")).lower()
            score = float(distance)
            if skill and skill.lower() not in chunk_skill:
                continue  # HARD FILTER OUT

            ranked.append((score, doc))

        ranked.sort(key=lambda x: x[0])
        return [doc for _, doc in ranked[:top_k]]
