"""Content Studio API — Idea inbox → Brief → Script pipeline."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..db import get_conn
from ..utils import utc_now_iso

router = APIRouter(prefix="/api/v2/content", tags=["content"])


# ── Schemas ───────────────────────────────────────────────
class CreateIdeaRequest(BaseModel):
    channel_name: str
    title: str
    angle: str = ""
    source: str = ""
    notes: str = ""
    priority: int = 100


class UpdateIdeaStatusRequest(BaseModel):
    status: str  # inbox, approved, rejected, briefed, scripted, produced


class CreateBriefRequest(BaseModel):
    idea_id: int
    channel_name: str
    title: str
    target_format: str = "shorts"
    target_duration_sec: int = 60
    voice_style: str = ""
    footage_style: str = ""
    thumbnail_notes: str = ""
    cta_text: str = ""


class CreateScriptRequest(BaseModel):
    brief_id: int
    channel_name: str
    title: str
    script_text: str = ""
    source_refs: list[str] = []


class GenerateScriptRequest(BaseModel):
    brief_id: int
    channel_name: str


# ══════════════════════════════════════════════════════════
#  IDEAS
# ══════════════════════════════════════════════════════════

@router.get("/ideas")
def list_ideas(channel: str | None = None, status: str | None = None, limit: int = 100):
    conn = get_conn()
    q = "SELECT * FROM content_ideas WHERE 1=1"
    params: list = []
    if channel:
        q += " AND channel_name=?"
        params.append(channel)
    if status:
        q += " AND status=?"
        params.append(status)
    q += " ORDER BY priority ASC, created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.post("/ideas")
def create_idea(req: CreateIdeaRequest):
    conn = get_conn()
    now = utc_now_iso()
    cur = conn.execute(
        """INSERT INTO content_ideas (channel_name, title, angle, source, status, priority, notes, research_ids, created_at, updated_at)
           VALUES (?, ?, ?, ?, 'inbox', ?, ?, '[]', ?, ?)""",
        (req.channel_name, req.title, req.angle, req.source, req.priority, req.notes, now, now),
    )
    conn.commit()
    return {"ok": True, "id": cur.lastrowid, "message": "Idea added to inbox"}


@router.put("/ideas/{idea_id}/status")
def update_idea_status(idea_id: int, req: UpdateIdeaStatusRequest):
    conn = get_conn()
    now = utc_now_iso()
    conn.execute("UPDATE content_ideas SET status=?, updated_at=? WHERE id=?", (req.status, now, idea_id))
    conn.commit()
    return {"ok": True, "message": f"Idea #{idea_id} → {req.status}"}


@router.delete("/ideas/{idea_id}")
def delete_idea(idea_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM content_ideas WHERE id=?", (idea_id,))
    conn.commit()
    return {"ok": True, "message": "Idea deleted"}


# ══════════════════════════════════════════════════════════
#  BRIEFS
# ══════════════════════════════════════════════════════════

@router.get("/briefs")
def list_briefs(channel: str | None = None, limit: int = 50):
    conn = get_conn()
    if channel:
        rows = conn.execute(
            "SELECT * FROM content_briefs WHERE channel_name=? ORDER BY created_at DESC LIMIT ?",
            (channel, limit),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM content_briefs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.post("/briefs")
def create_brief(req: CreateBriefRequest):
    conn = get_conn()
    now = utc_now_iso()
    cur = conn.execute(
        """INSERT INTO content_briefs
           (idea_id, channel_name, title, target_format, outline_json, target_duration_sec,
            voice_style, footage_style, thumbnail_notes, cta_text, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, '{}', ?, ?, ?, ?, ?, 'draft', ?, ?)""",
        (req.idea_id, req.channel_name, req.title, req.target_format,
         req.target_duration_sec, req.voice_style, req.footage_style,
         req.thumbnail_notes, req.cta_text, now, now),
    )
    conn.commit()
    conn.execute("UPDATE content_ideas SET status='briefed', updated_at=? WHERE id=?", (now, req.idea_id))
    conn.commit()
    return {"ok": True, "id": cur.lastrowid, "message": "Brief created"}


@router.get("/briefs/{brief_id}")
def get_brief(brief_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM content_briefs WHERE id=?", (brief_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Brief not found")
    return dict(row)


# ══════════════════════════════════════════════════════════
#  SCRIPTS
# ══════════════════════════════════════════════════════════

@router.get("/scripts")
def list_scripts(channel: str | None = None, limit: int = 50):
    conn = get_conn()
    if channel:
        rows = conn.execute(
            "SELECT * FROM script_drafts WHERE channel_name=? ORDER BY created_at DESC LIMIT ?",
            (channel, limit),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM script_drafts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.post("/scripts")
def create_script(req: CreateScriptRequest):
    conn = get_conn()
    now = utc_now_iso()
    word_count = len(req.script_text.split())
    est_dur = int(word_count / 2.5)  # ~150 wpm
    cur = conn.execute(
        """INSERT INTO script_drafts
           (brief_id, channel_name, title, script_text, script_json, word_count, estimated_duration_sec,
            fact_check_status, source_refs, provider_used, model_used, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, '{}', ?, ?, 'pending', ?, 'manual', '', 'draft', ?, ?)""",
        (req.brief_id, req.channel_name, req.title, req.script_text,
         word_count, est_dur, json.dumps(req.source_refs), now, now),
    )
    conn.commit()
    return {"ok": True, "id": cur.lastrowid, "message": f"Script created ({word_count} words, ~{est_dur}s)"}


@router.post("/scripts/generate")
async def generate_script(req: GenerateScriptRequest):
    """Tạo script bằng AI từ brief + channel memory."""
    conn = get_conn()
    brief = conn.execute("SELECT * FROM content_briefs WHERE id=?", (req.brief_id,)).fetchone()
    if not brief:
        raise HTTPException(404, "Brief not found")

    # Lấy channel profile để lấy brand voice
    profile = conn.execute("SELECT json FROM profiles WHERE name=?", (req.channel_name,)).fetchone()
    profile_json = json.loads(profile["json"]) if profile else {}
    niche = profile_json.get("niche", "")
    language = profile_json.get("language", "en")

    prompt = f"""Write a YouTube {brief['target_format']} script about: {brief['title']}

Target duration: {brief['target_duration_sec']} seconds (~{brief['target_duration_sec'] * 2.5:.0f} words)
Niche: {niche}
Language: {language}
Voice style: {brief['voice_style'] or 'engaging, informative'}
Footage style: {brief['footage_style'] or 'stock footage with text overlays'}
CTA: {brief['cta_text'] or 'Subscribe for more'}

Requirements:
- Hook in first 3 seconds
- Clear structure with transition markers
- End with CTA
- Keep claims verifiable
- Write ONLY the narration script text"""

    try:
        from ..openai_api import chat
        result = chat(prompt, model=None)
        script_text = result if isinstance(result, str) else str(result)
    except Exception as e:
        raise HTTPException(500, f"AI generation failed: {e}")

    word_count = len(script_text.split())
    est_dur = int(word_count / 2.5)
    now = utc_now_iso()

    cur = conn.execute(
        """INSERT INTO script_drafts
           (brief_id, channel_name, title, script_text, script_json, word_count, estimated_duration_sec,
            fact_check_status, source_refs, provider_used, model_used, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, '{}', ?, ?, 'pending', '[]', 'openai', '', 'draft', ?, ?)""",
        (req.brief_id, req.channel_name, brief["title"], script_text, word_count, est_dur, now, now),
    )
    conn.commit()

    conn.execute("UPDATE content_briefs SET status='scripted', updated_at=? WHERE id=?", (now, req.brief_id))
    conn.commit()

    return {"ok": True, "id": cur.lastrowid, "word_count": word_count, "est_duration_sec": est_dur,
            "message": f"Script generated ({word_count} words)"}


@router.get("/scripts/{script_id}")
def get_script(script_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM script_drafts WHERE id=?", (script_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Script not found")
    return dict(row)
