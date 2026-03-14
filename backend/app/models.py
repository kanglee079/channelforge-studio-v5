from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class Idea:
    title: str
    angle: str
    search_terms: list[str]
    seed_urls: list[str] = field(default_factory=list)
    youtube_urls: list[str] = field(default_factory=list)


@dataclass
class SourceNote:
    kind: str
    title: str
    url: str
    excerpt: str
    attribution: str = ""


@dataclass
class ResearchPack:
    topic: str
    summary: str = ""
    notes: list[SourceNote] = field(default_factory=list)


@dataclass
class ScriptPackage:
    title: str
    hook: str
    intro: str
    sections: list[dict[str, Any]]
    outro: str
    description: str
    tags: list[str]
    search_terms: list[str]
    thumbnail_text: str
    seo_keywords: list[str] = field(default_factory=list)
    disclosure_recommended: bool = False


@dataclass
class MediaAsset:
    kind: str  # video | image
    path: Path
    source: str
    source_url: str
    attribution: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelProfile:
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
    tags: list[str] = field(default_factory=list)
    voice_provider_order: list[str] = field(default_factory=lambda: ["openai"])
    transcribe_provider_order: list[str] = field(default_factory=lambda: ["openai"])
    footage_provider_order: list[str] = field(default_factory=lambda: ["pexels", "pixabay"])
    research_provider_order: list[str] = field(default_factory=lambda: ["wikipedia"])
    youtube_client_secrets: str = "client_secret.json"
    youtube_token_json: str = "token.json"
    disclose_synthetic_media: bool = False
    allowed_seed_domains: list[str] = field(default_factory=list)
    blocked_words: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class JobPaths:
    root: Path
    research_json: Path
    idea_json: Path
    script_json: Path
    moderation_json: Path
    voice_audio: Path
    subtitles_srt: Path
    thumbnail_jpg: Path
    final_mp4: Path
    credits_json: Path
    upload_json: Path
    clips_dir: Path
    temp_dir: Path


@dataclass
class JobResult:
    title: str
    root: Path
    video_path: Path
    thumbnail_path: Path
    state: str
    scheduled_publish_at: str | None = None
    youtube_video_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
