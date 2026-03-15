"""Retriever — Query vector index + provider APIs for candidate assets.

Trộn local cache + Pexels/Pixabay + diversify candidate set.
"""

from __future__ import annotations

import logging
from typing import Any

from ..db import get_conn
from ..utils import utc_now_iso
from .embedder import Embedder
from .index_store import IndexStore
from .scene_spec_builder import SceneSpec

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieve candidate assets for scenes using semantic search + providers."""

    def __init__(self, embedder: Embedder, index: IndexStore):
        self.embedder = embedder
        self.index = index

    def retrieve_for_scene(self, spec: SceneSpec, top_k: int = 10) -> list[dict]:
        """Retrieve candidate assets for a scene spec.

        Strategy:
        1. Semantic vector search (if index is loaded)
        2. DB keyword search on local assets
        3. Provider API search (Pexels/Pixabay) via existing pipeline

        Returns list of candidates with similarity scores.
        """
        candidates = []

        # 1. Vector search from index
        if self.index.size > 0:
            for query in spec.search_queries[:3]:
                query_vec = self.embedder.embed_text(query)
                results = self.index.query(query_vec, top_k=top_k)
                for r in results:
                    r["source"] = "vector_index"
                    r["query_used"] = query
                candidates.extend(results)

        # 2. DB keyword search
        db_results = self._search_db_assets(spec.search_queries, top_k)
        candidates.extend(db_results)

        # 3. Deduplicate by asset_key
        seen = set()
        unique = []
        for c in candidates:
            key = c.get("asset_key") or c.get("asset_id") or f"{c.get('provider','')}-{c.get('source_id','')}"
            if key not in seen:
                seen.add(key)
                unique.append(c)

        # Sort by similarity descending
        unique.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return unique[:top_k]

    def _search_db_assets(self, queries: list[str], limit: int) -> list[dict]:
        """Search local asset DB by tags/keywords."""
        conn = get_conn()
        results = []
        for query in queries[:2]:
            words = query.lower().split()[:5]
            for word in words:
                if len(word) < 3:
                    continue
                rows = conn.execute(
                    "SELECT * FROM media_assets_v2 WHERE tags_json LIKE ? OR asset_key LIKE ? LIMIT ?",
                    (f"%{word}%", f"%{word}%", limit),
                ).fetchall()
                for r in rows:
                    item = dict(r)
                    item["source"] = "local_db"
                    item["similarity"] = 0.3  # Base score for keyword match
                    results.append(item)
        return results
