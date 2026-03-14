"""Template Packs API — Reusable video production templates."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import get_conn
from ..utils import utc_now_iso

router = APIRouter(prefix="/api/v2/templates", tags=["templates"])


class CreateTemplateRequest(BaseModel):
    name: str
    category: str = "shorts"
    description: str = ""
    config: dict = {}


# ── Default template packs ────────────────────────────────
DEFAULT_TEMPLATES = [
    {
        "name": "shorts_facts",
        "category": "shorts",
        "description": "YouTube Shorts: hook → facts → CTA. 30-60 giây.",
        "config": {
            "duration_range": [30, 60],
            "resolution": "1080x1920",
            "fps": 30,
            "subtitle_style": "bold_center",
            "subtitle_font_size": 42,
            "subtitle_color": "#FFFFFF",
            "subtitle_bg": "#000000AA",
            "footage_style": "stock_video",
            "min_clips": 3,
            "max_clips": 8,
            "hook_duration_sec": 3,
            "cta_placement": "end",
            "voice_pacing": "fast",
            "transition": "cut",
        },
    },
    {
        "name": "documentary_mini",
        "category": "long",
        "description": "Mini documentary: intro → chapters → conclusion. 5-15 phút.",
        "config": {
            "duration_range": [300, 900],
            "resolution": "1920x1080",
            "fps": 30,
            "subtitle_style": "bottom_bar",
            "subtitle_font_size": 28,
            "subtitle_color": "#FFFFFF",
            "subtitle_bg": "#00000088",
            "footage_style": "mixed_stock_slides",
            "min_clips": 10,
            "max_clips": 30,
            "hook_duration_sec": 5,
            "cta_placement": "end",
            "voice_pacing": "moderate",
            "transition": "crossfade",
            "chapter_markers": True,
        },
    },
    {
        "name": "slideshow_top10",
        "category": "long",
        "description": "Top 10 list: countdown hoặc count-up. 5-10 phút.",
        "config": {
            "duration_range": [300, 600],
            "resolution": "1920x1080",
            "fps": 30,
            "subtitle_style": "bottom_bar",
            "footage_style": "images_with_zoom",
            "min_clips": 10,
            "max_clips": 15,
            "hook_duration_sec": 4,
            "list_format": "countdown",
            "item_duration_sec": 30,
            "transition": "slide",
            "number_overlay": True,
        },
    },
    {
        "name": "infographic_explainer",
        "category": "shorts",
        "description": "Infographic: text overlays + animations. 30-90 giây.",
        "config": {
            "duration_range": [30, 90],
            "resolution": "1080x1920",
            "fps": 30,
            "subtitle_style": "bold_center",
            "subtitle_font_size": 48,
            "footage_style": "solid_bg_with_text",
            "min_clips": 3,
            "max_clips": 6,
            "bg_colors": ["#1a1a2e", "#16213e", "#0f3460"],
            "text_animation": "fade_in",
            "voice_pacing": "measured",
        },
    },
    {
        "name": "talking_head_faceless",
        "category": "long",
        "description": "Faceless talking head: voiceover + B-roll + subtitles. 3-10 phút.",
        "config": {
            "duration_range": [180, 600],
            "resolution": "1920x1080",
            "fps": 30,
            "subtitle_style": "bottom_bar",
            "subtitle_font_size": 30,
            "footage_style": "stock_video_broll",
            "min_clips": 8,
            "max_clips": 25,
            "hook_duration_sec": 5,
            "broll_change_interval_sec": 5,
            "voice_pacing": "conversational",
            "transition": "cut",
        },
    },
]


def seed_default_templates() -> int:
    """Tạo các template mặc định nếu chưa có."""
    conn = get_conn()
    count = 0
    for t in DEFAULT_TEMPLATES:
        existing = conn.execute("SELECT id FROM template_packs WHERE name=?", (t["name"],)).fetchone()
        if not existing:
            now = utc_now_iso()
            conn.execute(
                """INSERT INTO template_packs (name, category, description, config_json, is_builtin, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 1, ?, ?)""",
                (t["name"], t["category"], t["description"], json.dumps(t["config"]), now, now),
            )
            count += 1
    conn.commit()
    return count


# ── API Endpoints ─────────────────────────────────────────

@router.get("")
def list_templates(category: str | None = None):
    conn = get_conn()
    if category:
        rows = conn.execute("SELECT * FROM template_packs WHERE category=? ORDER BY name", (category,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM template_packs ORDER BY category, name").fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d["config"] = json.loads(d.get("config_json", "{}"))
        items.append(d)
    return {"items": items}


@router.get("/{tpl_id}")
def get_template(tpl_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM template_packs WHERE id=?", (tpl_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Template not found")
    d = dict(row)
    d["config"] = json.loads(d.get("config_json", "{}"))
    return d


@router.post("")
def create_template(req: CreateTemplateRequest):
    conn = get_conn()
    now = utc_now_iso()
    try:
        conn.execute(
            """INSERT INTO template_packs (name, category, description, config_json, is_builtin, created_at, updated_at)
               VALUES (?, ?, ?, ?, 0, ?, ?)""",
            (req.name, req.category, req.description, json.dumps(req.config), now, now),
        )
        conn.commit()
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(400, f"Template '{req.name}' already exists")
        raise
    return {"ok": True, "message": f"Template '{req.name}' created"}


@router.delete("/{tpl_id}")
def delete_template(tpl_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM template_packs WHERE id=?", (tpl_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Template not found")
    if row["is_builtin"]:
        raise HTTPException(400, "Cannot delete built-in template")
    conn.execute("DELETE FROM template_packs WHERE id=?", (tpl_id,))
    conn.commit()
    return {"ok": True, "message": "Template deleted"}


@router.post("/seed")
def seed_templates():
    """Tạo các template mặc định (idempotent)."""
    count = seed_default_templates()
    return {"ok": True, "message": f"Seeded {count} new templates"}
