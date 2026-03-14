
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import requests
import feedparser
from bs4 import BeautifulSoup

from ..config import settings

CACHE_FILE = settings.cache_root / "trend_cache.json"


@dataclass
class TrendItem:
    title: str
    url: str
    source: str
    score: float
    summary: str = ""
    category: str = ""
    published_at: str = ""
    query: str = ""


def _safe_get(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> str:
    r = requests.get(url, headers=headers or {}, timeout=timeout)
    r.raise_for_status()
    return r.text


def fetch_google_trends_web(geo: str = "VN") -> list[TrendItem]:
    url = f"https://trends.google.com/trending?geo={geo}"
    html = _safe_get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    items: list[TrendItem] = []
    seen = set()
    for line in text.splitlines():
        if not line or len(line) < 3:
            continue
        if line.lower() in {"trends", "search volume", "started", "sort by title", "sort by search volume", "past 24 hours", "all categories"}:
            continue
        if line in seen:
            continue
        if len(items) >= 20:
            break
        seen.add(line)
        items.append(TrendItem(title=line, url=url, source="google_trends_web", score=max(1.0, 25 - len(items)), category="general", query=line))
    return items


def fetch_google_trends_rss(feed_url: str) -> list[TrendItem]:
    parsed = feedparser.parse(feed_url)
    items: list[TrendItem] = []
    for idx, entry in enumerate(parsed.entries[:50]):
        items.append(
            TrendItem(
                title=getattr(entry, "title", "").strip(),
                url=getattr(entry, "link", ""),
                source="google_trends_rss",
                score=max(1.0, 50 - idx),
                summary=getattr(entry, "summary", ""),
                published_at=getattr(entry, "published", ""),
                query=getattr(entry, "title", "").strip(),
            )
        )
    return items


def fetch_newsapi(niche: str, max_items: int = 20) -> list[TrendItem]:
    key = os.getenv("NEWSAPI_KEY", "").strip()
    if not key or not niche:
        return []
    url = f"https://newsapi.org/v2/everything?q={quote_plus(niche)}&sortBy=publishedAt&pageSize={max_items}&apiKey={key}"
    data = requests.get(url, timeout=20).json()
    items = []
    for i, art in enumerate(data.get("articles", [])[:max_items]):
        items.append(
            TrendItem(
                title=art.get("title", ""),
                url=art.get("url", ""),
                source="newsapi",
                score=max(1.0, 30 - i),
                summary=art.get("description", "") or "",
                published_at=art.get("publishedAt", "") or "",
                query=niche,
            )
        )
    return items


def fetch_gdelt(niche: str, max_items: int = 20) -> list[TrendItem]:
    if not niche:
        return []
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": niche,
        "mode": "artlist",
        "maxrecords": str(max_items),
        "format": "json",
        "sort": "DateDesc",
    }
    try:
        data = requests.get(url, params=params, timeout=20).json()
    except Exception:
        return []
    items = []
    for i, art in enumerate(data.get("articles", [])[:max_items]):
        items.append(
            TrendItem(
                title=art.get("title", ""),
                url=art.get("url", ""),
                source="gdelt",
                score=max(1.0, 25 - i),
                summary=art.get("seendate", ""),
                published_at=art.get("seendate", ""),
                query=niche,
            )
        )
    return items


def fetch_serpapi_google_trends(niche: str, geo: str = "VN") -> list[TrendItem]:
    key = os.getenv("SERPAPI_KEY", "").strip()
    if not key or not niche:
        return []
    url = "https://serpapi.com/search.json"
    params = {"engine": "google_trends", "q": niche, "data_type": "RELATED_QUERIES", "geo": geo, "api_key": key}
    try:
        data = requests.get(url, params=params, timeout=20).json()
    except Exception:
        return []
    related = data.get("related_queries") or []
    items = []
    for i, q in enumerate(related[:20]):
        title = q.get("query") or q.get("topic") or ""
        items.append(TrendItem(title=title, url="https://serpapi.com/google-trends", source="serpapi_google_trends", score=max(1.0, 20 - i), summary=str(q), query=title))
    return items


def rank_items(items: list[TrendItem], niche: str | None = None, max_items: int = 50) -> list[TrendItem]:
    niche_terms = [x.strip().lower() for x in (niche or "").split() if x.strip()]
    scored: list[TrendItem] = []
    for item in items:
        bonus = 0.0
        title_l = item.title.lower()
        if niche_terms and any(term in title_l for term in niche_terms):
            bonus += 10.0
        if item.source.startswith("google_trends"):
            bonus += 5.0
        item.score = round(item.score + bonus, 2)
        scored.append(item)
    scored.sort(key=lambda x: x.score, reverse=True)
    seen = set()
    deduped: list[TrendItem] = []
    for item in scored:
        key = item.title.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= max_items:
            break
    return deduped


def scan_trends(niche: str | None = None, geo: str = "VN", max_items: int = 50) -> dict[str, Any]:
    items: list[TrendItem] = []
    rss_url = os.getenv("GOOGLE_TRENDS_RSS_URL", "").strip()
    if rss_url:
        items.extend(fetch_google_trends_rss(rss_url))
    items.extend(fetch_google_trends_web(geo=geo))
    items.extend(fetch_gdelt(niche or "", max_items=max_items))
    items.extend(fetch_newsapi(niche or "", max_items=max_items))
    items.extend(fetch_serpapi_google_trends(niche or "", geo=geo))
    ranked = rank_items(items, niche=niche, max_items=max_items)
    return {
        "generated_at": int(time.time()),
        "geo": geo,
        "niche": niche or "",
        "items": [asdict(i) for i in ranked],
    }


def refresh_trends_cache() -> dict[str, Any]:
    data = scan_trends(geo=os.getenv("DEFAULT_TREND_GEO", "VN"))
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def load_trends_cache() -> dict[str, Any]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return refresh_trends_cache()
