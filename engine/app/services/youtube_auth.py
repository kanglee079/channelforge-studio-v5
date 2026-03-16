"""YouTube Auth Service — OAuth 2.0 flow for YouTube Data API v3.

Manages: OAuth consent, token persistence, credential refresh, channel info.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Scopes needed for full YouTube management
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

# Default paths — file is at engine/app/services/youtube_auth.py
ENGINE_DIR = Path(__file__).resolve().parent.parent.parent  # → engine/
DEFAULT_CLIENT_SECRET = ENGINE_DIR / "client_secret.json"
DEFAULT_TOKEN_PATH = ENGINE_DIR / "data" / "youtube_token.json"


class YouTubeAuth:
    """Manage YouTube OAuth 2.0 authentication."""

    def __init__(self, client_secret_path: str | Path | None = None,
                 token_path: str | Path | None = None):
        self.client_secret_path = Path(client_secret_path) if client_secret_path else self._find_client_secret()
        self.token_path = Path(token_path) if token_path else DEFAULT_TOKEN_PATH
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self._credentials: Credentials | None = None
        self._youtube = None

    def _find_client_secret(self) -> Path:
        """Find client_secret file — check multiple locations."""
        candidates = [
            DEFAULT_CLIENT_SECRET,
            *list(ENGINE_DIR.glob("client_secret_*.json")),
            ENGINE_DIR / "data" / "client_secret.json",
        ]
        for p in candidates:
            if p.exists():
                logger.info("Found client_secret at: %s", p)
                return p
        return DEFAULT_CLIENT_SECRET

    @property
    def is_configured(self) -> bool:
        """Check if client_secret file exists."""
        return self.client_secret_path.exists()

    @property
    def is_authenticated(self) -> bool:
        """Check if we have a valid token."""
        if self._credentials and self._credentials.valid:
            return True
        return self._load_token()

    def _load_token(self) -> bool:
        """Try to load existing token from disk."""
        if not self.token_path.exists():
            return False
        try:
            self._credentials = Credentials.from_authorized_user_file(
                str(self.token_path), SCOPES
            )
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                self._credentials.refresh(Request())
                self._save_token()
            return self._credentials is not None and self._credentials.valid
        except Exception as e:
            logger.warning("Failed to load token: %s", e)
            return False

    def _save_token(self):
        """Save credentials to disk."""
        if self._credentials:
            self.token_path.write_text(self._credentials.to_json(), encoding="utf-8")

    def start_auth_flow(self, port: int = 8085) -> dict:
        """Start OAuth consent flow — opens browser for user to authorize.

        Returns dict with auth status and channel info.
        """
        if not self.is_configured:
            return {
                "ok": False,
                "error": f"Client secret not found at {self.client_secret_path}",
                "hint": "Download client_secret.json from Google Cloud Console",
            }

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.client_secret_path), SCOPES
            )
            # This opens browser automatically
            self._credentials = flow.run_local_server(
                port=port,
                prompt="consent",
                success_message="✅ ChannelForge Studio đã kết nối YouTube thành công! Bạn có thể đóng tab này.",
            )
            self._save_token()
            self._youtube = None  # Reset cached service

            # Get channel info immediately after auth
            channel_info = self.get_channel_info()
            return {
                "ok": True,
                "message": "YouTube authorization successful!",
                "channel": channel_info,
                "token_path": str(self.token_path),
            }
        except Exception as e:
            logger.error("OAuth flow failed: %s", e)
            return {"ok": False, "error": str(e)}

    def get_youtube_service(self):
        """Get authenticated YouTube API service."""
        if self._youtube:
            return self._youtube

        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Run start_auth_flow() first.")

        self._youtube = build("youtube", "v3", credentials=self._credentials)
        return self._youtube

    def get_channel_info(self) -> dict:
        """Get info about the authenticated user's YouTube channel."""
        try:
            youtube = self.get_youtube_service()
            response = youtube.channels().list(
                part="snippet,statistics,contentDetails",
                mine=True,
            ).execute()

            if not response.get("items"):
                return {"ok": False, "error": "No channel found for this account"}

            channel = response["items"][0]
            snippet = channel.get("snippet", {})
            stats = channel.get("statistics", {})

            return {
                "ok": True,
                "channel_id": channel["id"],
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:200],
                "custom_url": snippet.get("customUrl", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                "subscriber_count": stats.get("subscriberCount", "0"),
                "video_count": stats.get("videoCount", "0"),
                "view_count": stats.get("viewCount", "0"),
                "country": snippet.get("country", ""),
                "published_at": snippet.get("publishedAt", ""),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def list_videos(self, max_results: int = 10) -> list[dict]:
        """List recent videos from the authenticated channel."""
        try:
            youtube = self.get_youtube_service()

            # Get uploads playlist
            channels = youtube.channels().list(part="contentDetails", mine=True).execute()
            if not channels.get("items"):
                return []

            uploads_id = channels["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # Get videos from uploads playlist
            response = youtube.playlistItems().list(
                part="snippet,status",
                playlistId=uploads_id,
                maxResults=min(max_results, 50),
            ).execute()

            videos = []
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                videos.append({
                    "video_id": snippet.get("resourceId", {}).get("videoId", ""),
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", "")[:100],
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                    "status": item.get("status", {}).get("privacyStatus", ""),
                })
            return videos
        except Exception as e:
            logger.error("Failed to list videos: %s", e)
            return []

    def revoke_auth(self) -> dict:
        """Revoke OAuth token and clear stored credentials."""
        try:
            if self.token_path.exists():
                self.token_path.unlink()
            self._credentials = None
            self._youtube = None
            return {"ok": True, "message": "OAuth token revoked"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_auth_status(self) -> dict:
        """Get current authentication status."""
        return {
            "configured": self.is_configured,
            "authenticated": self.is_authenticated,
            "client_secret_path": str(self.client_secret_path),
            "token_path": str(self.token_path),
            "token_exists": self.token_path.exists(),
        }


# Module-level singleton
youtube_auth = YouTubeAuth()
