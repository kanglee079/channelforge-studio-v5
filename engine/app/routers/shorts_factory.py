"""Shorts Factory Router — Create, preview, and upload YouTube Shorts.

Endpoints:
- POST /shorts/generate   — Generate a Short from topic
- GET  /shorts/list        — List generated Shorts
- POST /shorts/upload      — Upload a Short to YouTube
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v5/shorts", tags=["shorts-factory"])


class GenerateRequest(BaseModel):
    topic: str
    voice: str = "nova"
    channel_niche: str = "animals"
    script: Optional[str] = None
    title: Optional[str] = None


class UploadRequest(BaseModel):
    job_id: str
    privacy_status: str = "public"


@router.post("/generate")
def generate_short(req: GenerateRequest):
    """Generate a YouTube Short from a topic.

    Pipeline: topic → AI script → TTS voice → stock footage → compose → ready to upload.
    """
    from ..config import settings
    from ..services.shorts_composer import ShortsComposer, ShortSpec

    composer = ShortsComposer(
        openai_key=settings.openai_api_keys[0] if settings.openai_api_keys else "",
        pexels_key=settings.pexels_api_key,
        elevenlabs_key=settings.elevenlabs_api_keys[0] if settings.elevenlabs_api_keys else "",
    )

    spec = ShortSpec(
        topic=req.topic,
        script=req.script or "",
        title=req.title or "",
        voice=req.voice,
        channel_niche=req.channel_niche,
    )

    result = composer.compose(spec)

    if result.status == "error":
        raise HTTPException(status_code=500, detail=f"Composition failed: {result.error}")

    return result.to_dict()


@router.get("/list")
def list_shorts():
    """List all generated Shorts."""
    output_dir = Path("data/shorts_output")
    if not output_dir.exists():
        return {"shorts": [], "count": 0}

    shorts = []
    for f in sorted(output_dir.glob("result_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            shorts.append(data)
        except Exception:
            pass

    return {"shorts": shorts, "count": len(shorts)}


@router.post("/upload")
def upload_short(req: UploadRequest):
    """Upload a generated Short to YouTube."""
    from ..services.youtube_auth import youtube_auth

    if not youtube_auth.is_authenticated:
        raise HTTPException(status_code=401, detail="YouTube not connected")

    # Find the short
    result_file = Path(f"data/shorts_output/result_{req.job_id}.json")
    if not result_file.exists():
        raise HTTPException(status_code=404, detail=f"Short {req.job_id} not found")

    data = json.loads(result_file.read_text(encoding="utf-8"))
    video_path = Path(data["video_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    # Upload
    try:
        from googleapiclient.http import MediaFileUpload

        youtube = youtube_auth.get_youtube_service()

        tags = data.get("tags", [])
        if "#Shorts" not in tags:
            tags.insert(0, "#Shorts")

        body = {
            "snippet": {
                "title": data.get("title", "")[:100],
                "description": data.get("description", "") + "\n\n#Shorts",
                "tags": tags[:30],
                "categoryId": "15",
                "defaultLanguage": "en",
            },
            "status": {
                "privacyStatus": req.privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        insert_req = youtube.videos().insert(
            part="snippet,status",
            body=body,
            notifySubscribers=True,
            media_body=MediaFileUpload(str(video_path), chunksize=8 * 1024 * 1024, resumable=True),
        )

        response = None
        while response is None:
            _, response = insert_req.next_chunk()

        video_id = response["id"]

        # Update record
        data["youtube_id"] = video_id
        data["youtube_url"] = f"https://youtube.com/shorts/{video_id}"
        data["status"] = "uploaded"
        result_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Upload thumbnail
        thumb_path = Path(data.get("thumbnail_path", ""))
        if thumb_path.exists():
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumb_path)),
                ).execute()
            except Exception:
                pass

        return {
            "ok": True,
            "video_id": video_id,
            "url": f"https://youtube.com/shorts/{video_id}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
