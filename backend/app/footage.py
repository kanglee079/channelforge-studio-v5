from __future__ import annotations

import json
import mimetypes
import random
from pathlib import Path
from typing import Any

import requests

from .config import settings
from .models import MediaAsset
from .utils import hardlink_or_copy, save_json, sha1_text


class CacheStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def reserve(self, source_url: str, ext: str) -> Path:
        digest = sha1_text(source_url)
        return self.root / f"{digest}{ext}"

    def store_bytes(self, source_url: str, ext: str, content: bytes) -> Path:
        path = self.reserve(source_url, ext)
        if not path.exists():
            path.write_bytes(content)
        return path


class PexelsClient:
    def __init__(self) -> None:
        if not settings.pexels_api_key:
            raise RuntimeError("PEXELS_API_KEY is missing")
        self.headers = {"Authorization": settings.pexels_api_key}

    def search_videos(self, query: str, per_page: int = 10) -> dict[str, Any]:
        res = requests.get(
            "https://api.pexels.com/v1/videos/search",
            headers=self.headers,
            params={"query": query, "per_page": per_page, "orientation": "portrait" if settings.video_format == "shorts" else "landscape"},
            timeout=120,
        )
        res.raise_for_status()
        return res.json()

    def search_photos(self, query: str, per_page: int = 10) -> dict[str, Any]:
        res = requests.get(
            "https://api.pexels.com/v1/search",
            headers=self.headers,
            params={"query": query, "per_page": per_page, "orientation": "portrait" if settings.video_format == "shorts" else "landscape"},
            timeout=120,
        )
        res.raise_for_status()
        return res.json()


class PixabayClient:
    def __init__(self) -> None:
        if not settings.pixabay_api_key:
            raise RuntimeError("PIXABAY_API_KEY is missing")
        self.key = settings.pixabay_api_key

    def search_videos(self, query: str, per_page: int = 10) -> dict[str, Any]:
        res = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": self.key, "q": query, "per_page": per_page, "safesearch": "true", "orientation": "vertical" if settings.video_format == "shorts" else "horizontal"},
            timeout=120,
        )
        res.raise_for_status()
        return res.json()

    def search_images(self, query: str, per_page: int = 10) -> dict[str, Any]:
        res = requests.get(
            "https://pixabay.com/api/",
            params={"key": self.key, "q": query, "per_page": per_page, "safesearch": "true", "orientation": "vertical" if settings.video_format == "shorts" else "horizontal"},
            timeout=120,
        )
        res.raise_for_status()
        return res.json()


def _download(url: str, cache: CacheStore) -> Path:
    ext = Path(url.split("?")[0]).suffix or mimetypes.guess_extension(requests.utils.urlparse(url).path) or ".bin"
    cached = cache.reserve(url, ext)
    if cached.exists():
        return cached
    res = requests.get(url, timeout=300)
    res.raise_for_status()
    return cache.store_bytes(url, ext, res.content)


def _pexels_video_assets(term: str, cache: CacheStore) -> list[MediaAsset]:
    data = PexelsClient().search_videos(term, per_page=10)
    items = []
    videos = data.get("videos", [])
    random.shuffle(videos)
    for video in videos:
        files = sorted(video.get("video_files", []), key=lambda x: (0 if x.get("quality") == "hd" else 1, abs((x.get("width") or 0) - settings.frame_width)))
        if not files:
            continue
        file = files[0]
        src_url = file.get("link")
        if not src_url:
            continue
        local = _download(src_url, cache)
        user = video.get("user") or {}
        items.append(MediaAsset(kind="video", path=local, source="pexels", source_url=video.get("url") or src_url, attribution=f"{user.get('name','')} on Pexels", meta={"search_term": term, "video_id": video.get("id")}))
    return items


def _pexels_image_assets(term: str, cache: CacheStore) -> list[MediaAsset]:
    data = PexelsClient().search_photos(term, per_page=10)
    items = []
    photos = data.get("photos", [])
    random.shuffle(photos)
    for photo in photos:
        src = photo.get("src") or {}
        url = src.get("large2x") or src.get("large") or src.get("original")
        if not url:
            continue
        local = _download(url, cache)
        photographer = photo.get("photographer", "")
        items.append(MediaAsset(kind="image", path=local, source="pexels", source_url=photo.get("url") or url, attribution=f"{photographer} on Pexels", meta={"search_term": term, "photo_id": photo.get("id")}))
    return items


def _pixabay_video_assets(term: str, cache: CacheStore) -> list[MediaAsset]:
    data = PixabayClient().search_videos(term, per_page=10)
    items = []
    hits = data.get("hits", [])
    random.shuffle(hits)
    for hit in hits:
        videos = hit.get("videos") or {}
        stream = videos.get("medium") or videos.get("small") or videos.get("tiny")
        if not stream or not stream.get("url"):
            continue
        local = _download(stream["url"], cache)
        items.append(MediaAsset(kind="video", path=local, source="pixabay", source_url=hit.get("pageURL") or stream["url"], attribution=f"{hit.get('user','')} on Pixabay", meta={"search_term": term, "video_id": hit.get("id")}))
    return items


def _pixabay_image_assets(term: str, cache: CacheStore) -> list[MediaAsset]:
    data = PixabayClient().search_images(term, per_page=10)
    items = []
    hits = data.get("hits", [])
    random.shuffle(hits)
    for hit in hits:
        url = hit.get("largeImageURL") or hit.get("webformatURL")
        if not url:
            continue
        local = _download(url, cache)
        items.append(MediaAsset(kind="image", path=local, source="pixabay", source_url=hit.get("pageURL") or url, attribution=f"{hit.get('user','')} on Pixabay", meta={"search_term": term, "image_id": hit.get("id")}))
    return items


def fetch_media_assets(search_terms: list[str], clips_dir: Path, credits_path: Path, provider_order: list[str], target_count: int = 6) -> list[MediaAsset]:
    clips_dir.mkdir(parents=True, exist_ok=True)
    cache = CacheStore(settings.cache_root / "media")
    assets: list[MediaAsset] = []
    seen_urls: set[str] = set()

    for term in [t for i, t in enumerate(search_terms) if t and t not in search_terms[:i]]:
        if len(assets) >= target_count:
            break
        for provider in provider_order:
            provider_assets: list[MediaAsset] = []
            try:
                if provider == "pexels":
                    provider_assets.extend(_pexels_video_assets(term, cache))
                    if len(provider_assets) < 2:
                        provider_assets.extend(_pexels_image_assets(term, cache))
                elif provider == "pixabay":
                    provider_assets.extend(_pixabay_video_assets(term, cache))
                    if len(provider_assets) < 2:
                        provider_assets.extend(_pixabay_image_assets(term, cache))
            except Exception:
                continue
            random.shuffle(provider_assets)
            for asset in provider_assets:
                if len(assets) >= target_count:
                    break
                if asset.source_url in seen_urls:
                    continue
                seen_urls.add(asset.source_url)
                out = clips_dir / f"asset_{len(assets)+1}{asset.path.suffix}"
                hardlink_or_copy(asset.path, out)
                asset.path = out
                assets.append(asset)
            if len(assets) >= target_count:
                break
    save_json(credits_path, {"credits": [asset.__dict__ | {"path": str(asset.path)} for asset in assets]})
    return assets
