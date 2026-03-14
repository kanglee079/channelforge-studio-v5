"""Candidate Retriever — Fetch media candidates from multiple providers.

Retrieves candidates from local cache, Pexels, Pixabay based on scene visual intent.
"""

from __future__ import annotations

import logging
from typing import Any

from .schema import SceneIntent, CandidateAsset

logger = logging.getLogger(__name__)


async def retrieve_candidates(
    scene: SceneIntent,
    providers: list[str] | None = None,
    max_per_provider: int = 5,
) -> list[CandidateAsset]:
    """Retrieve candidate assets for a scene from multiple providers."""
    if providers is None:
        providers = ["local_cache", "pexels", "pixabay"]

    all_candidates: list[CandidateAsset] = []
    query = scene.visual_intent or " ".join(scene.must_have_objects)

    for provider in providers:
        try:
            if provider == "local_cache":
                candidates = _search_local_cache(query, scene, max_per_provider)
            elif provider == "pexels":
                candidates = await _search_pexels(query, scene, max_per_provider)
            elif provider == "pixabay":
                candidates = await _search_pixabay(query, scene, max_per_provider)
            else:
                continue
            all_candidates.extend(candidates)
            logger.info("Retrieved %d candidates from %s for scene %d", len(candidates), provider, scene.scene_index)
        except Exception as e:
            logger.warning("Provider %s failed for scene %d: %s", provider, scene.scene_index, e)

    return all_candidates


def _search_local_cache(query: str, scene: SceneIntent, limit: int) -> list[CandidateAsset]:
    """Search locally cached media assets."""
    from ..db import get_conn
    conn = get_conn()
    try:
        # Search by tags match
        keywords = query.lower().split()[:5]
        results = []
        rows = conn.execute(
            "SELECT * FROM media_assets WHERE embedding_status != 'failed' ORDER BY quality_score DESC LIMIT ?",
            (limit * 3,),
        ).fetchall()
        for r in rows:
            import json
            tags = json.loads(r["tags_json"]) if r["tags_json"] else []
            tag_str = " ".join(tags).lower()
            if any(kw in tag_str or kw in (r.get("local_path", "") or "").lower() for kw in keywords):
                results.append(CandidateAsset(
                    asset_id=r["id"],
                    source_provider="local_cache",
                    source_url=r.get("source_url", ""),
                    local_path=r.get("local_path", ""),
                    asset_type=r.get("asset_type", "video"),
                    width=r.get("width", 0),
                    height=r.get("height", 0),
                    duration_sec=r.get("duration_sec", 0.0),
                    tags=tags,
                    quality_score=r.get("quality_score", 0.0),
                ))
                if len(results) >= limit:
                    break
        return results
    except Exception:
        return []


async def _search_pexels(query: str, scene: SceneIntent, limit: int) -> list[CandidateAsset]:
    """Search Pexels for stock footage."""
    from ..config import Settings
    settings = Settings()
    if not settings.PEXELS_KEY:
        return []

    import aiohttp
    asset_type = "video" if scene.asset_preference != "image" else "image"
    base = "https://api.pexels.com/videos/search" if asset_type == "video" else "https://api.pexels.com/v1/search"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                base,
                params={"query": query[:80], "per_page": limit, "orientation": "landscape"},
                headers={"Authorization": settings.PEXELS_KEY},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await resp.json()

        candidates = []
        if asset_type == "video":
            for v in data.get("videos", [])[:limit]:
                files = v.get("video_files", [])
                best = max(files, key=lambda f: f.get("width", 0)) if files else {}
                candidates.append(CandidateAsset(
                    source_provider="pexels",
                    source_url=best.get("link", ""),
                    source_id=str(v.get("id", "")),
                    asset_type="video",
                    width=best.get("width", 0),
                    height=best.get("height", 0),
                    duration_sec=v.get("duration", 0),
                    tags=[],
                    license_notes="Pexels License — Free for commercial use",
                ))
        else:
            for p in data.get("photos", [])[:limit]:
                candidates.append(CandidateAsset(
                    source_provider="pexels",
                    source_url=p.get("src", {}).get("large2x", ""),
                    source_id=str(p.get("id", "")),
                    asset_type="image",
                    width=p.get("width", 0),
                    height=p.get("height", 0),
                    tags=[],
                    license_notes="Pexels License — Free for commercial use",
                ))
        return candidates
    except Exception as e:
        logger.warning("Pexels search failed: %s", e)
        return []


async def _search_pixabay(query: str, scene: SceneIntent, limit: int) -> list[CandidateAsset]:
    """Search Pixabay for stock footage."""
    from ..config import Settings
    settings = Settings()
    if not settings.PIXABAY_KEY:
        return []

    import aiohttp
    asset_type = "video" if scene.asset_preference != "image" else "image"
    base = "https://pixabay.com/api/videos/" if asset_type == "video" else "https://pixabay.com/api/"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                base,
                params={"key": settings.PIXABAY_KEY, "q": query[:80], "per_page": limit, "orientation": "horizontal"},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await resp.json()

        candidates = []
        for hit in data.get("hits", [])[:limit]:
            if asset_type == "video":
                videos = hit.get("videos", {})
                large = videos.get("large", {}) or videos.get("medium", {})
                candidates.append(CandidateAsset(
                    source_provider="pixabay",
                    source_url=large.get("url", ""),
                    source_id=str(hit.get("id", "")),
                    asset_type="video",
                    width=large.get("width", 0),
                    height=large.get("height", 0),
                    duration_sec=hit.get("duration", 0),
                    tags=hit.get("tags", "").split(", "),
                    license_notes="Pixabay License — Free for commercial use",
                ))
            else:
                candidates.append(CandidateAsset(
                    source_provider="pixabay",
                    source_url=hit.get("largeImageURL", ""),
                    source_id=str(hit.get("id", "")),
                    asset_type="image",
                    width=hit.get("imageWidth", 0),
                    height=hit.get("imageHeight", 0),
                    tags=hit.get("tags", "").split(", "),
                    license_notes="Pixabay License — Free for commercial use",
                ))
        return candidates
    except Exception as e:
        logger.warning("Pixabay search failed: %s", e)
        return []
