"""Pexels Video Fetcher — Download stock video clips for Shorts.

Uses Pexels API to search and download portrait/vertical HD clips.
Caches clips locally to avoid re-downloading.
"""

from __future__ import annotations

import logging
import hashlib
import httpx
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PEXELS_API = "https://api.pexels.com"


class PexelsFetcher:
    """Fetch stock video clips from Pexels API."""

    def __init__(self, api_key: str, cache_dir: str = "data/stock_cache"):
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {"Authorization": api_key}

    def search_videos(self, query: str, orientation: str = "portrait",
                      per_page: int = 5, min_duration: int = 5,
                      max_duration: int = 30) -> list[dict]:
        """Search Pexels for video clips."""
        params = {
            "query": query,
            "orientation": orientation,
            "per_page": per_page,
            "size": "medium",
        }
        try:
            resp = httpx.get(
                f"{PEXELS_API}/videos/search",
                headers=self.headers,
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for video in data.get("video_files", []) if "video_files" in data else []:
                pass  # Handled below

            for item in data.get("videos", []):
                duration = item.get("duration", 0)
                if duration < min_duration or duration > max_duration:
                    continue

                # Find best HD file (portrait preferred)
                best_file = self._pick_best_file(item.get("video_files", []))
                if not best_file:
                    continue

                results.append({
                    "id": item["id"],
                    "url": item.get("url", ""),
                    "duration": duration,
                    "width": best_file.get("width", 0),
                    "height": best_file.get("height", 0),
                    "download_url": best_file["link"],
                    "quality": best_file.get("quality", ""),
                    "user": item.get("user", {}).get("name", "Pexels"),
                })

            logger.info("Pexels search '%s': %d results", query, len(results))
            return results

        except Exception as e:
            logger.error("Pexels search failed: %s", e)
            return []

    def _pick_best_file(self, files: list[dict]) -> dict | None:
        """Pick the best video file — prefer HD, portrait orientation."""
        # Sort by quality: prefer hd > sd, then by height (taller = better for Shorts)
        scored = []
        for f in files:
            w = f.get("width", 0)
            h = f.get("height", 0)
            q = f.get("quality", "")
            # Score: prefer tall (portrait), HD
            score = 0
            if h > w:
                score += 100  # Portrait bonus
            if q == "hd":
                score += 50
            if h >= 720:
                score += 20
            score += min(h, 1920) / 100  # Taller = better
            scored.append((score, f))

        scored.sort(reverse=True)
        return scored[0][1] if scored else None

    def download_clip(self, download_url: str, video_id: int | str) -> Path | None:
        """Download a clip, using cache if available."""
        # Cache key from video ID
        cache_key = hashlib.md5(str(video_id).encode()).hexdigest()[:12]
        cache_path = self.cache_dir / f"pexels_{cache_key}.mp4"

        if cache_path.exists() and cache_path.stat().st_size > 10000:
            logger.info("Using cached clip: %s", cache_path.name)
            return cache_path

        try:
            logger.info("Downloading clip %s...", video_id)
            with httpx.stream("GET", download_url, timeout=60, follow_redirects=True) as resp:
                resp.raise_for_status()
                with open(cache_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=8192):
                        f.write(chunk)

            size_mb = cache_path.stat().st_size / (1024 * 1024)
            logger.info("Downloaded: %s (%.1f MB)", cache_path.name, size_mb)
            return cache_path

        except Exception as e:
            logger.error("Download failed for %s: %s", video_id, e)
            if cache_path.exists():
                cache_path.unlink()
            return None

    def fetch_clips_for_topic(self, topic: str, num_clips: int = 4,
                              keywords: list[str] | None = None) -> list[Path]:
        """Fetch multiple clips for a topic. Tries topic first, then individual keywords."""
        downloaded = []

        # Search by main topic
        results = self.search_videos(topic, per_page=num_clips)
        for r in results[:num_clips]:
            path = self.download_clip(r["download_url"], r["id"])
            if path:
                downloaded.append(path)

        # If not enough, search by individual keywords
        if keywords and len(downloaded) < num_clips:
            for kw in keywords:
                if len(downloaded) >= num_clips:
                    break
                extra = self.search_videos(kw, per_page=2)
                for r in extra:
                    if len(downloaded) >= num_clips:
                        break
                    path = self.download_clip(r["download_url"], r["id"])
                    if path:
                        downloaded.append(path)

        logger.info("Fetched %d clips for topic '%s'", len(downloaded), topic)
        return downloaded
