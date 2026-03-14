"""Research Library API — Manage research snapshots and source extraction."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import get_conn
from ..utils import utc_now_iso

router = APIRouter(prefix="/api/v2/research", tags=["research"])


class CreateResearchRequest(BaseModel):
    channel_name: str | None = None
    title: str
    source_url: str = ""
    source_title: str = ""
    cleaned_text: str = ""
    tags: list[str] = []


class ExtractRequest(BaseModel):
    url: str
    channel_name: str | None = None
    extractor: str = "auto"


# ── List ──────────────────────────────────────────────────
@router.get("")
def list_research(channel: str | None = None, limit: int = 50):
    conn = get_conn()
    if channel:
        rows = conn.execute(
            "SELECT * FROM research_snapshots WHERE channel_name=? ORDER BY created_at DESC LIMIT ?",
            (channel, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM research_snapshots ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return {"items": [dict(r) for r in rows]}


# ── Create ────────────────────────────────────────────────
@router.post("")
def create_research(req: CreateResearchRequest):
    conn = get_conn()
    now = utc_now_iso()
    import json
    cur = conn.execute(
        """INSERT INTO research_snapshots
           (channel_name, title, source_url, source_title, extractor, cleaned_text, metadata_json, tags, created_at)
           VALUES (?, ?, ?, ?, 'manual', ?, '{}', ?, ?)""",
        (req.channel_name, req.title, req.source_url, req.source_title,
         req.cleaned_text, json.dumps(req.tags), now),
    )
    conn.commit()
    return {"ok": True, "id": cur.lastrowid, "message": "Research snapshot created"}


# ── Get one ───────────────────────────────────────────────
@router.get("/{res_id}")
def get_research(res_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM research_snapshots WHERE id=?", (res_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Research snapshot not found")
    return dict(row)


# ── Extract from URL ─────────────────────────────────────
@router.post("/extract")
def extract_from_url(req: ExtractRequest):
    """Nhận URL → trích xuất nội dung sạch bằng Trafilatura/Scrapling."""
    import json

    title = ""
    text = ""
    extractor_used = "trafilatura"

    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(req.url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False) or ""
            meta = trafilatura.extract_metadata(downloaded)
            title = meta.title if meta and meta.title else req.url
            extractor_used = "trafilatura"
    except ImportError:
        try:
            import requests
            resp = requests.get(req.url, timeout=15, headers={"User-Agent": "ChannelForge/5.0"})
            text = resp.text[:10000]
            title = req.url
            extractor_used = "requests_fallback"
        except Exception as e:
            raise HTTPException(500, f"Extraction failed: {e}")

    conn = get_conn()
    now = utc_now_iso()
    cur = conn.execute(
        """INSERT INTO research_snapshots
           (channel_name, title, source_url, source_title, extractor, cleaned_text, metadata_json, tags, created_at)
           VALUES (?, ?, ?, ?, ?, ?, '{}', '[]', ?)""",
        (req.channel_name, title, req.url, title, extractor_used, text[:50000], now),
    )
    conn.commit()
    return {"ok": True, "id": cur.lastrowid, "title": title, "extractor": extractor_used, "text_length": len(text)}


# ── Delete ────────────────────────────────────────────────
@router.delete("/{res_id}")
def delete_research(res_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM research_snapshots WHERE id=?", (res_id,))
    conn.commit()
    return {"ok": True, "message": "Research snapshot deleted"}
