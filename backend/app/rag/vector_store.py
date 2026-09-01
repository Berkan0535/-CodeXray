import json
import math
from typing import List, Dict, Any, Tuple, Optional
from app.core.config import settings
from app.core.logging import logger


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    """
    In-memory / Persistent vector index for fast semantic similarity search across code chunks.
    Compatible with PostgreSQL pgvector and standalone SQLite/memory environments.
    """

    def __init__(self):
        # analysis_id -> list of chunk dicts {id, file_path, symbol_name, start_line, end_line, content, embedding}
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    def index_chunks(self, analysis_id: str, chunks_with_embeddings: List[Dict[str, Any]]) -> None:
        self._store[analysis_id] = chunks_with_embeddings
        logger.info(f"VectorStore: Indexed {len(chunks_with_embeddings)} chunks for analysis {analysis_id}")

    def search(
        self,
        analysis_id: str,
        query_embedding: List[float],
        top_k: int = 6
    ) -> List[Tuple[Dict[str, Any], float]]:
        chunks = self._store.get(analysis_id, [])
        if not chunks:
            return []

        scored: List[Tuple[Dict[str, Any], float]] = []
        for chunk in chunks:
            emb = chunk.get("embedding")
            if not emb:
                continue
            sim = cosine_similarity(query_embedding, emb)
            scored.append((chunk, sim))

        # Sort descending by similarity score
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def has_index(self, analysis_id: str) -> bool:
        return analysis_id in self._store and len(self._store[analysis_id]) > 0


# Global singleton instance
vector_store = VectorStore()
