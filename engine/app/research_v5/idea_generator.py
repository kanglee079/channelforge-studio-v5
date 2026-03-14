"""Idea Generator — Convert scored trends into video ideas.

Takes a scored trend + channel context and generates 3-5 video ideas
with unique angles, titles, and hook suggestions.
"""

from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)


async def generate_ideas_from_trend(
    trend_title: str,
    channel_name: str,
    max_ideas: int = 5,
) -> list[dict]:
    """Generate video ideas from a trend using AI."""
    from ..db import get_conn

    conn = get_conn()
    profile_row = conn.execute("SELECT json FROM profiles WHERE name=?", (channel_name,)).fetchone()
    profile = json.loads(profile_row["json"]) if profile_row else {}
    niche = profile.get("niche", "")
    language = profile.get("language", "en")

    prompt = f"""You are a YouTube content strategist.

Given this trending topic: "{trend_title}"
Channel niche: {niche or 'general'}
Content language: {language}

Generate {max_ideas} unique video ideas. For each idea provide:
- title: catchy YouTube title (max 60 chars)
- angle: unique perspective or approach
- hook: first 3-second hook line
- format: shorts or long-form
- estimated_views_potential: low/medium/high
- notes: brief production notes

Return ONLY a JSON array of idea objects."""

    try:
        from ..openai_api import chat
        raw = chat(prompt, model=None)
        result = raw if isinstance(raw, str) else str(raw)
        ideas = _extract_json_array(result)

        # Save ideas to content_ideas
        from ..utils import utc_now_iso
        now = utc_now_iso()
        saved_ideas = []
        for idea in ideas[:max_ideas]:
            try:
                cur = conn.execute(
                    """INSERT INTO content_ideas
                       (channel_name, title, angle, source, status, priority, notes, research_ids, created_at, updated_at)
                       VALUES (?, ?, ?, ?, 'inbox', 100, ?, '[]', ?, ?)""",
                    (channel_name, idea.get("title", ""), idea.get("angle", ""),
                     f"trend:{trend_title}", idea.get("notes", ""), now, now),
                )
                conn.commit()
                saved_ideas.append({
                    "id": cur.lastrowid,
                    **idea,
                })
            except Exception as e:
                logger.warning("Failed to save idea: %s", e)

        logger.info("Generated %d ideas from trend '%s'", len(saved_ideas), trend_title)
        return saved_ideas
    except Exception as e:
        logger.error("Idea generation failed: %s", e)
        return []


async def generate_research_pack(idea_id: int, channel_name: str) -> dict:
    """Generate a research pack for an idea — key facts, sources, hooks, CTAs."""
    from ..db import get_conn
    conn = get_conn()

    idea = conn.execute("SELECT * FROM content_ideas WHERE id=?", (idea_id,)).fetchone()
    if not idea:
        return {"error": "Idea not found"}

    profile_row = conn.execute("SELECT json FROM profiles WHERE name=?", (channel_name,)).fetchone()
    profile = json.loads(profile_row["json"]) if profile_row else {}

    prompt = f"""Create a comprehensive research pack for this video idea:
Title: {idea['title']}
Angle: {idea['angle']}
Channel niche: {profile.get('niche', '')}

Return a JSON object with:
- key_facts: list of 5-8 verifiable facts with sources
- source_urls: list of reference URLs
- visual_opportunities: list of visual moments for B-roll
- risk_notes: any claims that need fact-checking
- hook_options: 3 different hook suggestions
- cta_suggestion: best CTA for this topic
- estimated_script_words: target word count"""

    try:
        from ..openai_api import chat
        raw = chat(prompt, model=None)
        result = raw if isinstance(raw, str) else str(raw)
        pack = _extract_json_object(result)

        # Save to research_packs
        from ..utils import utc_now_iso
        now = utc_now_iso()
        conn.execute(
            """INSERT INTO research_packs
               (channel_name, idea_id, summary_json, source_refs_json, fact_blocks_json,
                visual_opportunities_json, risk_notes_json, hook_suggestion, cta_suggestion, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (channel_name, idea_id,
             json.dumps(pack),
             json.dumps(pack.get("source_urls", [])),
             json.dumps(pack.get("key_facts", [])),
             json.dumps(pack.get("visual_opportunities", [])),
             json.dumps(pack.get("risk_notes", [])),
             json.dumps(pack.get("hook_options", [])),
             pack.get("cta_suggestion", ""),
             now, now),
        )
        conn.commit()

        return {"ok": True, "pack": pack}
    except Exception as e:
        logger.error("Research pack generation failed: %s", e)
        return {"error": str(e)}


def _extract_json_array(text: str) -> list[dict]:
    import re
    match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return []


def _extract_json_object(text: str) -> dict:
    import re
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return {}
