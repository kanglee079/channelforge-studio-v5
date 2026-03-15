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

# Detect FAISS availability at module level
_FAISS_AVAILABLE = False
_NUMPY_AVAILABLE = False

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
    try:
        import faiss
        _FAISS_AVAILABLE = True
        logger.info("FAISS engine available — using accelerated vector search")
    except ImportError:
        logger.info("FAISS not available — using numpy cosine similarity")
except ImportError:
    logger.info("numpy not available — using pure Python brute-force mode")


class IndexStore:
    """Build, save, load, and query a vector index.

    Engine priority: FAISS (GPU/CPU accelerated) → numpy cosine → pure Python brute-force.
    """

    def __init__(self, index_dir: str = "engine/data/media_cache/index"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._vectors: list[list[float]] = []
        self._metadata: list[dict] = []
        self._faiss_index = None  # FAISS index object (if available)

    @property
    def size(self) -> int:
        return len(self._metadata)

    @property
    def engine(self) -> str:
        if _FAISS_AVAILABLE and self._faiss_index is not None:
            return "faiss"
        if _NUMPY_AVAILABLE:
            return "numpy"
        return "brute_force"

    def add(self, vector: list[float], metadata: dict):
        """Add a vector + metadata to the index."""
        self._vectors.append(list(vector))
        self._metadata.append(metadata)

    def build(self):
        """Build the index. For FAISS, creates IndexFlatIP for cosine similarity."""
        if not self._vectors:
            logger.info("Index build: no vectors to index")
            return

        if _FAISS_AVAILABLE:
            import numpy as np
            import faiss

            dim = len(self._vectors[0])
            # Normalize vectors for cosine similarity via inner product
            vectors_np = np.array(self._vectors, dtype="float32")
            faiss.normalize_L2(vectors_np)
            self._faiss_index = faiss.IndexFlatIP(dim)
            self._faiss_index.add(vectors_np)
            logger.info("FAISS index built: %d vectors, dim=%d", len(self._vectors), dim)
        else:
            logger.info("Index built (brute-force): %d vectors", len(self._vectors))

    def query(self, query_vector: list[float], top_k: int = 10) -> list[dict]:
        """Search index for most similar vectors."""
        if not self._vectors:
            return []

        top_k = min(top_k, len(self._vectors))

        if _FAISS_AVAILABLE and self._faiss_index is not None:
            return self._query_faiss(query_vector, top_k)
        if _NUMPY_AVAILABLE:
            return self._query_numpy(query_vector, top_k)
        return self._query_brute_force(query_vector, top_k)

    def _query_faiss(self, query_vector: list[float], top_k: int) -> list[dict]:
        """FAISS accelerated search."""
        import numpy as np
        import faiss

        qv = np.array([query_vector], dtype="float32")
        faiss.normalize_L2(qv)
        scores, indices = self._faiss_index.search(qv, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append({**self._metadata[idx], "similarity": float(score)})
        return results

    def _query_numpy(self, query_vector: list[float], top_k: int) -> list[dict]:
        """Numpy vectorized cosine similarity."""
        import numpy as np

        qv = np.array(query_vector, dtype="float32")
        qv_norm = np.linalg.norm(qv) or 1e-9
        qv = qv / qv_norm

        mat = np.array(self._vectors, dtype="float32")
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        mat = mat / norms

        scores = mat @ qv
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({**self._metadata[idx], "similarity": float(scores[idx])})
        return results

    def _query_brute_force(self, query_vector: list[float], top_k: int) -> list[dict]:
        """Pure Python cosine similarity (fallback)."""
        similarities = []
        for i, vec in enumerate(self._vectors):
            sim = self._cosine_similarity(query_vector, vec)
            similarities.append((sim, i))

        similarities.sort(reverse=True)
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
        """Save index and metadata to disk."""
        if not self._vectors:
            return

        # Save FAISS index binary if available
        if _FAISS_AVAILABLE and self._faiss_index is not None:
            import faiss
            faiss.write_index(self._faiss_index, str(self.index_dir / f"{name}.faiss"))

        # Always save JSON backup (for portability)
        with open(self.index_dir / f"{name}_vectors.json", "w", encoding="utf-8") as f:
            json.dump(self._vectors, f)
        with open(self.index_dir / f"{name}_metadata.json", "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False)

        logger.info("Index saved: %s (%d vectors, engine=%s)", name, len(self._metadata), self.engine)

    def load(self, name: str = "default") -> bool:
        """Load index from disk. Tries FAISS binary first, then JSON."""
        meta_path = self.index_dir / f"{name}_metadata.json"
        if not meta_path.exists():
            return False

        with open(meta_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

        # Try FAISS binary
        faiss_path = self.index_dir / f"{name}.faiss"
        if _FAISS_AVAILABLE and faiss_path.exists():
            import faiss
            self._faiss_index = faiss.read_index(str(faiss_path))
            # Also load vectors JSON for backup
            vectors_path = self.index_dir / f"{name}_vectors.json"
            if vectors_path.exists():
                with open(vectors_path, "r", encoding="utf-8") as f:
                    self._vectors = json.load(f)
            logger.info("Index loaded (FAISS): %s (%d vectors)", name, len(self._metadata))
            return True

        # Fallback to JSON vectors
        vectors_path = self.index_dir / f"{name}_vectors.json"
        if vectors_path.exists():
            with open(vectors_path, "r", encoding="utf-8") as f:
                self._vectors = json.load(f)
            logger.info("Index loaded (JSON): %s (%d vectors)", name, len(self._metadata))
            return True

        return False

    def clear(self):
        """Clear all data from index."""
        self._vectors = []
        self._metadata = []
        self._faiss_index = None

    def get_stats(self) -> dict:
        """Get index statistics."""
        dim = len(self._vectors[0]) if self._vectors else 0
        return {
            "total_vectors": self.size,
            "vector_dim": dim,
            "engine": self.engine,
            "faiss_available": _FAISS_AVAILABLE,
            "numpy_available": _NUMPY_AVAILABLE,
            "index_dir": str(self.index_dir),
        }
