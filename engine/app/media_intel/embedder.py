"""Embedder — Text and image embedding for semantic retrieval.

Hỗ trợ multilingual CLIP / sentence-transformers. Graceful fallback nếu chưa cài.
numpy + sentence-transformers are optional — app still works without them (heuristic mode).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Embedder:
    """Generate text and image embeddings for semantic search."""

    def __init__(self, model_name: str = "auto", cache_dir: str = "engine/data/media_cache/embeddings"):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._model = None
        self._available = None

    @property
    def is_available(self) -> bool:
        if self._available is None:
            self._available = self._check_availability()
        return self._available

    @property
    def active_model_name(self) -> str:
        return self.model_name if self.is_available else "heuristic"

    def _check_availability(self) -> bool:
        try:
            import sentence_transformers  # noqa: F401
            return True
        except ImportError:
            pass
        logger.info("No semantic embedding library found — heuristic mode active")
        return False

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text query. Returns list of floats."""
        cache_key = self._hash(f"text:{text}")
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached

        if self.is_available:
            vec = self._embed_text_model(text)
        else:
            vec = self._embed_text_heuristic(text)

        self._save_cache(cache_key, vec)
        return vec

    def embed_image(self, image_path: str) -> list[float]:
        """Generate embedding for an image."""
        cache_key = self._hash(f"img:{image_path}")
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached

        if self.is_available:
            vec = self._embed_image_model(image_path)
        else:
            vec = self._embed_image_heuristic(image_path)

        self._save_cache(cache_key, vec)
        return vec

    def similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1e-9
        norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1e-9
        return dot / (norm_a * norm_b)

    # ── Model-based embedding ─────────────────────────────────

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("clip-ViT-B-32")
                self.model_name = "clip-ViT-B-32"
            except Exception:
                try:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer("all-MiniLM-L6-v2")
                    self.model_name = "all-MiniLM-L6-v2"
                except Exception:
                    self._available = False
                    return None
        return self._model

    def _embed_text_model(self, text: str) -> list[float]:
        model = self._get_model()
        if model is None:
            return self._embed_text_heuristic(text)
        result = model.encode(text, normalize_embeddings=True)
        return result.tolist() if hasattr(result, 'tolist') else list(result)

    def _embed_image_model(self, image_path: str) -> list[float]:
        model = self._get_model()
        if model is None:
            return self._embed_image_heuristic(image_path)
        try:
            from PIL import Image
            img = Image.open(image_path)
            result = model.encode(img, normalize_embeddings=True)
            return result.tolist() if hasattr(result, 'tolist') else list(result)
        except Exception:
            return self._embed_image_heuristic(image_path)

    # ── Heuristic fallback (TF-IDF-like, pure Python) ─────────

    def _embed_text_heuristic(self, text: str) -> list[float]:
        """Simple bag-of-words hash-based embedding (128-dim)."""
        dim = 128
        vec = [0.0] * dim
        words = text.lower().split()
        for w in words:
            h = int(hashlib.md5(w.encode()).hexdigest(), 16) % dim
            vec[h] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1e-9
        return [v / norm for v in vec]

    def _embed_image_heuristic(self, image_path: str) -> list[float]:
        return self._embed_text_heuristic(Path(image_path).stem.replace("_", " ").replace("-", " "))

    # ── Cache (JSON-based, no numpy dependency) ───────────────

    def _hash(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _save_cache(self, key: str, vec: list[float]):
        path = self.cache_dir / f"{key}.json"
        try:
            path.write_text(json.dumps(vec))
        except Exception:
            pass

    def _load_cache(self, key: str) -> list[float] | None:
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                pass
        return None
