from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .config import settings
from .models import ChannelProfile

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]


def _get_credentials(client_secrets: Path, token_json: Path) -> Credentials:
    creds = None
    if token_json.exists():
        creds = Credentials.from_authorized_user_file(str(token_json), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
        creds = flow.run_local_server(port=0)
        token_json.write_text(creds.to_json(), encoding="utf-8")
    return creds


def upload_video(*, profile: ChannelProfile, video_path: Path, thumbnail_path: Path | None, title: str, description: str, tags: list[str], publish_at: str | None, srt_path: Path | None = None) -> dict:
    client_secrets = Path(profile.youtube_client_secrets)
    token_json = Path(profile.youtube_token_json)
    youtube = build("youtube", "v3", credentials=_get_credentials(client_secrets, token_json))

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": profile.category_id or settings.default_category_id,
        },
        "status": {
            "privacyStatus": profile.privacy_status or settings.default_privacy_status,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": bool(profile.disclose_synthetic_media or settings.disclose_synthetic_media),
        },
    }
    if publish_at and body["status"]["privacyStatus"] == "private":
        body["status"]["publishAt"] = publish_at

    insert = youtube.videos().insert(
        part="snippet,status",
        body=body,
        notifySubscribers=bool(profile.notify_subscribers or settings.notify_subscribers),
        media_body=MediaFileUpload(str(video_path), chunksize=-1, resumable=True),
    )

    response = None
    while response is None:
        _, response = insert.next_chunk()
    video_id = response["id"]

    if settings.upload_thumbnail and thumbnail_path and thumbnail_path.exists():
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumbnail_path))).execute()

    if settings.upload_captions and srt_path and srt_path.exists():
        youtube.captions().insert(
            part="snippet",
            body={"snippet": {"videoId": video_id, "language": "en", "name": "English", "isDraft": False}},
            media_body=MediaFileUpload(str(srt_path), mimetype="application/octet-stream", resumable=True),
        ).execute()

    return {"video_id": video_id, "publish_at": publish_at, "thumbnail_uploaded": settings.upload_thumbnail}
