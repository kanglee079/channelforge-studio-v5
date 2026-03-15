"""Index Store — Vector index for semantic retrieval.

Preferred: FAISS (if installed). Fallback: brute-force cosine similarity using pure Python.
Index lưu trên disk, metadata song song trong JSON.
No hard dependencies on numpy or faiss — works in pure Python mode.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class IndexStore:
    """Build, save, load, and query a vector index."""

    def __init__(self, index_dir: str = "engine/data/media_cache/index"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._vectors: list[list[float]] = []
        self._metadata: list[dict] = []

    @property
    def size(self) -> int:
        return len(self._metadata)

    @property
    def engine(self) -> str:
        return "brute_force"

    def add(self, vector: list[float], metadata: dict):
        """Add a vector + metadata to the index."""
        self._vectors.append(list(vector))
        self._metadata.append(metadata)

    def build(self):
        """Build the index (no-op for brute force)."""
        logger.info("Index built: %d vectors", len(self._vectors))

    def query(self, query_vector: list[float], top_k: int = 10) -> list[dict]:
        """Search index for most similar vectors using cosine similarity."""
        if not self._vectors:
            return []

        similarities = []
        for i, vec in enumerate(self._vectors):
            sim = self._cosine_similarity(query_vector, vec)
            similarities.append((sim, i))

        similarities.sort(reverse=True)
        top_k = min(top_k, len(similarities))

        results = []
        for sim, idx in similarities[:top_k]:
            results.append({**self._metadata[idx], "similarity": sim})
        return results

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Pure Python cosine similarity."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a)) or 1e-9
        norm_b = math.sqrt(sum(x * x for x in b)) or 1e-9
        return dot / (norm_a * norm_b)

    def save(self, name: str = "default"):
        """Save index and metadata to disk as JSON."""
        if not self._vectors:
            return

        with open(self.index_dir / f"{name}_vectors.json", "w", encoding="utf-8") as f:
            json.dump(self._vectors, f)
        with open(self.index_dir / f"{name}_metadata.json", "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False)

        logger.info("Index saved: %s (%d vectors)", name, len(self._metadata))

    def load(self, name: str = "default") -> bool:
        """Load index from disk."""
        vectors_path = self.index_dir / f"{name}_vectors.json"
        meta_path = self.index_dir / f"{name}_metadata.json"

        if not vectors_path.exists() or not meta_path.exists():
            return False

        with open(vectors_path, "r", encoding="utf-8") as f:
            self._vectors = json.load(f)
        with open(meta_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

        logger.info("Index loaded: %s (%d vectors)", name, len(self._metadata))
        return True

    def clear(self):
        """Clear all data from index."""
        self._vectors = []
        self._metadata = []

    def get_stats(self) -> dict:
        """Get index statistics."""
        dim = len(self._vectors[0]) if self._vectors else 0
        return {
            "total_vectors": self.size,
            "vector_dim": dim,
            "engine": self.engine,
            "index_dir": str(self.index_dir),
        }
