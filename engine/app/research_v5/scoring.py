"""Trend Scoring — Score trends per channel for relevance and contentability.

Scoring formula:
  final = 0.30*freshness + 0.25*niche_relevance + 0.20*contentability + 0.15*source_confidence + 0.10*monetization_potential
"""

from __future__ import annotations

import json
import logging
import time

logger = logging.getLogger(__name__)


def score_trend_for_channel(trend_item: dict, channel_profile: dict) -> dict:
    """Score a single trend item against a channel profile."""
    niche = channel_profile.get("niche", "").lower()
    tags = [t.lower() for t in channel_profile.get("tags", [])]
    language = channel_profile.get("language", "en")

    title = (trend_item.get("title", "") or "").lower()
    snippet = (trend_item.get("snippet", "") or "").lower()
    combined = title + " " + snippet

    # 1. Freshness (based on fetch time)
    freshness = 0.8  # Default high — items just fetched are fresh

    # 2. Niche relevance
    niche_words = niche.split()
    niche_score = 0.0
    if niche_words:
        matches = sum(1 for w in niche_words if w in combined)
        niche_score = min(1.0, matches / max(len(niche_words), 1) * 1.5)
    if tags:
        tag_matches = sum(1 for t in tags if t in combined)
        niche_score = max(niche_score, min(1.0, tag_matches / len(tags) * 1.5))

    # 3. Contentability (can this become a video?)
    contentability = 0.5
    content_signals = ["how", "why", "what", "top", "best", "facts", "history", "explained", "mystery", "secret"]
    if any(sig in title for sig in content_signals):
        contentability = 0.8
    if len(title.split()) >= 4:  # More specific titles are more contentable
        contentability += 0.1

    # 4. Source confidence
    source_confidence_map = {
        "google_trends": 0.9,
        "newsapi": 0.8,
        "gdelt": 0.7,
        "rss": 0.6,
        "manual": 1.0,
    }
    source_confidence = source_confidence_map.get(trend_item.get("source_type", ""), 0.5)

    # 5. Monetization potential (simple heuristic)
    monetization = 0.5
    high_cpm_keywords = ["finance", "investment", "tech", "health", "insurance", "lawyer", "software", "crypto"]
    if any(kw in combined for kw in high_cpm_keywords):
        monetization = 0.8

    # 6. Risk / sensitivity check
    risk = 0.0
    risky_keywords = ["death", "murder", "terrorist", "graphic", "nsfw", "controversial"]
    if any(kw in combined for kw in risky_keywords):
        risk = 0.3

    # Final score
    final = (
        0.30 * freshness +
        0.25 * niche_score +
        0.20 * contentability +
        0.15 * source_confidence +
        0.10 * monetization -
        risk * 0.5
    )
    final = round(max(0.0, min(1.0, final)), 3)

    # Determine recommended action
    if final >= 0.70:
        action = "produce"
    elif final >= 0.50:
        action = "research"
    elif final >= 0.30:
        action = "watch"
    else:
        action = "skip"

    return {
        "relevance_score": round(niche_score, 3),
        "monetization_score": round(monetization, 3),
        "contentability_score": round(contentability, 3),
        "risk_score": round(risk, 3),
        "final_score": final,
        "recommended_action": action,
    }


def score_trends_for_channel(channel_name: str) -> list[dict]:
    """Score all recent trends for a specific channel."""
    from ..db import get_conn
    from ..db_v5 import list_trend_items
    from ..utils import utc_now_iso

    conn = get_conn()

    # Get channel profile
    profile_row = conn.execute("SELECT json FROM profiles WHERE name=?", (channel_name,)).fetchone()
    if not profile_row:
        return []
    profile = json.loads(profile_row["json"])

    # Get recent trends
    trends = list_trend_items(limit=100)

    results = []
    now = utc_now_iso()

    for trend in trends:
        scores = score_trend_for_channel(trend, profile)

        # Save to channel_trend_scores
        try:
            conn.execute(
                """INSERT INTO channel_trend_scores
                   (channel_name, trend_item_id, relevance_score, monetization_score,
                    contentability_score, risk_score, final_score, recommended_action, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (channel_name, trend["id"], scores["relevance_score"], scores["monetization_score"],
                 scores["contentability_score"], scores["risk_score"], scores["final_score"],
                 scores["recommended_action"], now),
            )
        except Exception:
            pass

        results.append({**trend, **scores})

    conn.commit()
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results
