
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


class EnqueueRequest(BaseModel):
    profile: str
    count: int = Field(default=10, ge=1, le=200)
    niche: str | None = None
    topic_file: str | None = None
    format: str = "shorts"
    seed_url_file: str | None = None
    youtube_url_file: str | None = None


class RunWorkerRequest(BaseModel):
    profile: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class TrendScanRequest(BaseModel):
    niche: str | None = None
    geo: str = "VN"
    hours: int = Field(default=24, ge=4, le=168)
    max_items: int = Field(default=50, ge=5, le=200)


class ChannelUpsertRequest(BaseModel):
    name: str
    title_prefix: str = ""
    niche: str = ""
    language: str = "en"
    default_video_format: str = "shorts"
    upload_enabled: bool = False
    privacy_status: str = "private"
    category_id: str = "27"
    publish_interval_minutes: int = 60
    daily_upload_soft_limit: int = 90
    notify_subscribers: bool = False
    tags: list[str] = []
    voice_provider_order: list[str] = ["openai"]
    transcribe_provider_order: list[str] = ["openai"]
    footage_provider_order: list[str] = ["pexels", "pixabay"]
    research_provider_order: list[str] = ["wikipedia", "trafilatura", "scrapling"]
    youtube_client_secrets: str = "client_secret.json"
    youtube_token_json: str = "token.json"
    disclose_synthetic_media: bool = False
    allowed_seed_domains: list[str] = []
    blocked_words: list[str] = []


class GenericMessage(BaseModel):
    ok: bool = True
    message: str
    data: dict[str, Any] | None = None
