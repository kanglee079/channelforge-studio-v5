"""Multi-source Trend Ingestion — Fetch trends from multiple sources.

Sources: Google Trends, NewsAPI, GDELT, RSS feeds.
Each source returns normalized TrendItem objects.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def ingest_trends(
    sources: list[str] | None = None,
    query: str = "",
    region: str = "US",
    max_per_source: int = 10,
) -> list[dict]:
    """Ingest trends from multiple sources and save to DB."""
    if sources is None:
        sources = ["google_trends", "newsapi"]

    all_items: list[dict] = []
    for source in sources:
        try:
            if source == "google_trends":
                items = await _fetch_google_trends(query, region, max_per_source)
            elif source == "newsapi":
                items = await _fetch_newsapi(query, region, max_per_source)
            elif source == "gdelt":
                items = await _fetch_gdelt(query, region, max_per_source)
            elif source == "rss":
                items = await _fetch_rss(query, max_per_source)
            else:
                continue
            all_items.extend(items)
            logger.info("Fetched %d trends from %s", len(items), source)
        except Exception as e:
            logger.warning("Source %s failed: %s", source, e)

    # Save to DB
    from ..db_v5 import insert_trend_item
    saved = 0
    for item in all_items:
        nhash = _normalize_hash(item.get("title", ""))
        try:
            insert_trend_item(
                source_type=item.get("source_type", "unknown"),
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                url=item.get("url", ""),
                region=item.get("region", region),
                raw_json=item.get("raw", {}),
                normalized_hash=nhash,
            )
            saved += 1
        except Exception:
            pass  # Likely duplicate hash

    logger.info("Saved %d/%d trend items", saved, len(all_items))
    return all_items


def _normalize_hash(text: str) -> str:
    """Create a normalized hash for deduplication."""
    normalized = " ".join(text.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()[:16]


async def _fetch_google_trends(query: str, region: str, limit: int) -> list[dict]:
    """Fetch trending topics from Google Trends via pytrends."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="en-US", tz=360)

        if query:
            pytrends.build_payload([query], timeframe="now 7-d", geo=region)
            related = pytrends.related_queries()
            items = []
            for kw, data in related.items():
                if data and "top" in data and data["top"] is not None:
                    for _, row in data["top"].head(limit).iterrows():
                        items.append({
                            "source_type": "google_trends",
                            "title": row.get("query", ""),
                            "snippet": f"Related to '{kw}', value: {row.get('value', 0)}",
                            "url": "",
                            "region": region,
                            "raw": {"query": kw, "value": int(row.get("value", 0))},
                        })
            return items
        else:
            trending = pytrends.trending_searches(pn=region.lower() if len(region) == 2 else "united_states")
            items = []
            for _, row in trending.head(limit).iterrows():
                items.append({
                    "source_type": "google_trends",
                    "title": row[0],
                    "snippet": "Trending now",
                    "url": "",
                    "region": region,
                    "raw": {},
                })
            return items
    except ImportError:
        logger.warning("pytrends not installed")
        return []
    except Exception as e:
        logger.warning("Google Trends fetch failed: %s", e)
        return []


async def _fetch_newsapi(query: str, region: str, limit: int) -> list[dict]:
    """Fetch news headlines from NewsAPI."""
    from ..config import Settings
    settings = Settings()
    api_key = getattr(settings, "NEWSAPI_KEY", "") or ""
    if not api_key:
        return []

    import aiohttp
    try:
        url = "https://newsapi.org/v2/top-headlines" if not query else "https://newsapi.org/v2/everything"
        params: dict[str, Any] = {"apiKey": api_key, "pageSize": limit, "language": "en"}
        if query:
            params["q"] = query
        else:
            params["country"] = region.lower() if len(region) == 2 else "us"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()

        items = []
        for art in data.get("articles", [])[:limit]:
            items.append({
                "source_type": "newsapi",
                "title": art.get("title", ""),
                "snippet": art.get("description", ""),
                "url": art.get("url", ""),
                "region": region,
                "raw": {"source": art.get("source", {}).get("name", ""), "publishedAt": art.get("publishedAt", "")},
            })
        return items
    except Exception as e:
        logger.warning("NewsAPI fetch failed: %s", e)
        return []


async def _fetch_gdelt(query: str, region: str, limit: int) -> list[dict]:
    """Fetch events from GDELT API."""
    import aiohttp
    q = query or "youtube"
    try:
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={q}&mode=artlist&maxrecords={limit}&format=json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                data = await resp.json()
        items = []
        for art in data.get("articles", [])[:limit]:
            items.append({
                "source_type": "gdelt",
                "title": art.get("title", ""),
                "snippet": art.get("seendate", ""),
                "url": art.get("url", ""),
                "region": region,
                "raw": {"domain": art.get("domain", ""), "language": art.get("language", "")},
            })
        return items
    except Exception as e:
        logger.warning("GDELT fetch failed: %s", e)
        return []


async def _fetch_rss(query: str, limit: int) -> list[dict]:
    """Fetch from RSS feeds (default YouTube trending RSS)."""
    try:
        import feedparser
        feeds = [
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
        ]
        items = []
        for feed_url in feeds:
            d = feedparser.parse(feed_url)
            for entry in d.entries[:limit]:
                items.append({
                    "source_type": "rss",
                    "title": entry.get("title", ""),
                    "snippet": entry.get("summary", "")[:200],
                    "url": entry.get("link", ""),
                    "region": "US",
                    "raw": {},
                })
        return items
    except ImportError:
        logger.warning("feedparser not installed")
        return []
    except Exception as e:
        logger.warning("RSS fetch failed: %s", e)
        return []
