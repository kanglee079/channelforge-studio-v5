"""YouTube API Router — OAuth, channel management, video upload.

Endpoints:
- GET  /youtube/auth/status     — Check auth status
- POST /youtube/auth/connect    — Start OAuth flow (opens browser)
- POST /youtube/auth/revoke     — Revoke OAuth token
- GET  /youtube/channel         — Get channel info
- GET  /youtube/videos          — List recent videos
- POST /youtube/upload          — Upload a video
"""

from __future__ import annotations

import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v5/youtube", tags=["youtube"])


# ═══════════════════════════════════════════════════════════
# Auth Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/auth/status")
def auth_status():
    """Get current YouTube OAuth status."""
    from ..services.youtube_auth import youtube_auth
    return youtube_auth.get_auth_status()


@router.post("/auth/connect")
def auth_connect(port: int = 8085):
    """Start OAuth consent flow — opens browser for user to authorize.

    The browser will open automatically. After the user authorizes,
    the token will be saved and the channel info will be returned.
    """
    from ..services.youtube_auth import youtube_auth
    result = youtube_auth.start_auth_flow(port=port)
    return result


@router.post("/auth/revoke")
def auth_revoke():
    """Revoke OAuth token and clear stored credentials."""
    from ..services.youtube_auth import youtube_auth
    return youtube_auth.revoke_auth()


# ═══════════════════════════════════════════════════════════
# Channel Info
# ═══════════════════════════════════════════════════════════

@router.get("/channel")
def get_channel():
    """Get info about the authenticated YouTube channel."""
    from ..services.youtube_auth import youtube_auth
    if not youtube_auth.is_authenticated:
        raise HTTPException(status_code=401, detail="Chưa kết nối YouTube. Gọi /auth/connect trước.")
    return youtube_auth.get_channel_info()


@router.get("/videos")
def list_videos(max_results: int = 10):
    """List recent videos from the authenticated channel."""
    from ..services.youtube_auth import youtube_auth
    if not youtube_auth.is_authenticated:
        raise HTTPException(status_code=401, detail="Chưa kết nối YouTube. Gọi /auth/connect trước.")
    videos = youtube_auth.list_videos(max_results=max_results)
    return {"videos": videos, "count": len(videos)}


# ═══════════════════════════════════════════════════════════
# Video Upload
# ═══════════════════════════════════════════════════════════

class UploadRequest(BaseModel):
    video_path: str
    title: str
    description: str = ""
    tags: list[str] = []
    privacy_status: str = "private"  # private | public | unlisted
    category_id: str = "22"  # 22 = People & Blogs
    thumbnail_path: Optional[str] = None
    notify_subscribers: bool = False


@router.post("/upload")
def upload_video(req: UploadRequest):
    """Upload a video to YouTube.

    Requires: authenticated via /auth/connect first.
    Video file must exist on disk at video_path.
    """
    from ..services.youtube_auth import youtube_auth

    if not youtube_auth.is_authenticated:
        raise HTTPException(status_code=401, detail="Chưa kết nối YouTube. Gọi /auth/connect trước.")

    video_file = Path(req.video_path)
    if not video_file.exists():
        raise HTTPException(status_code=400, detail=f"Video file not found: {req.video_path}")

    try:
        from googleapiclient.http import MediaFileUpload

        youtube = youtube_auth.get_youtube_service()

        body = {
            "snippet": {
                "title": req.title[:100],
                "description": req.description[:5000],
                "tags": req.tags[:30],
                "categoryId": req.category_id,
            },
            "status": {
                "privacyStatus": req.privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            notifySubscribers=req.notify_subscribers,
            media_body=MediaFileUpload(
                str(video_file),
                chunksize=1024 * 1024 * 8,  # 8MB chunks
                resumable=True,
            ),
        )

        # Execute upload with progress
        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                logger.info("Upload progress: %.1f%%", status.progress() * 100)

        video_id = response["id"]
        logger.info("Video uploaded: %s (id: %s)", req.title, video_id)

        # Upload thumbnail if provided
        if req.thumbnail_path:
            thumb_file = Path(req.thumbnail_path)
            if thumb_file.exists():
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumb_file)),
                ).execute()
                logger.info("Thumbnail uploaded for video: %s", video_id)

        return {
            "ok": True,
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": req.title,
            "privacy_status": req.privacy_status,
        }

    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
