from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "y", "on"}


def _list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    items = [x.strip() for x in raw.split(",") if x.strip()]
    return items


def _fallback_list(primary_many: str, primary_one: str) -> list[str]:
    many = _list(primary_many)
    if many:
        return many
    one = os.getenv(primary_one, "").strip()
    return [one] if one else []


@dataclass(frozen=True)
class Settings:
    openai_api_keys: list[str]
    pexels_api_key: str
    pixabay_api_key: str
    elevenlabs_api_keys: list[str]
    elevenlabs_voice_id: str

    openai_text_model: str
    openai_tts_model: str
    openai_image_model: str
    openai_transcribe_model: str
    voice: str

    output_root: Path
    state_root: Path
    db_path: Path
    cache_root: Path
    profiles_root: Path

    video_format: str
    frame_width: int
    frame_height: int
    fps: int
    min_clips: int
    max_clips: int
    max_workers: int
    max_retries: int
    retry_base_seconds: int
    subtitle_style: str

    generate_ideas: bool
    use_ai_thumbnail: bool
    upload_to_youtube: bool
    upload_thumbnail: bool
    upload_captions: bool
    disclose_synthetic_media: bool
    use_openai_moderation: bool
    notify_subscribers: bool

    default_category_id: str
    default_privacy_status: str
    publish_interval_minutes: int
    schedule_start_at: str
    daily_upload_soft_limit: int

    voice_provider_order: list[str]
    transcribe_provider_order: list[str]
    footage_provider_order: list[str]
    image_provider_order: list[str]
    research_provider_order: list[str]

    youtube_client_secrets: Path
    youtube_token_json: Path
    blocked_words: list[str]
    duplicate_threshold: float

    kokoro_lang_code: str
    kokoro_voice: str
    piper_bin: str
    piper_model: str
    piper_config: str
    faster_whisper_model: str


def load_settings() -> Settings:
    output_root = Path(os.getenv("OUTPUT_ROOT", "./output"))
    state_root = Path(os.getenv("STATE_ROOT", "./state"))
    cache_root = Path(os.getenv("CACHE_ROOT", str(state_root / "cache")))
    profiles_root = Path(os.getenv("PROFILES_ROOT", "./profiles"))
    db_path = Path(os.getenv("DB_PATH", str(state_root / "jobs.sqlite3")))

    for p in (output_root, state_root, cache_root, profiles_root, db_path.parent):
        p.mkdir(parents=True, exist_ok=True)

    return Settings(
        openai_api_keys=_fallback_list("OPENAI_API_KEYS", "OPENAI_API_KEY"),
        pexels_api_key=os.getenv("PEXELS_API_KEY", "").strip(),
        pixabay_api_key=os.getenv("PIXABAY_API_KEY", "").strip(),
        elevenlabs_api_keys=_fallback_list("ELEVENLABS_API_KEYS", "ELEVENLABS_API_KEY"),
        elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID", "").strip(),
        openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
        openai_tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        openai_image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"),
        openai_transcribe_model=os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1"),
        voice=os.getenv("VOICE", "alloy"),
        output_root=output_root,
        state_root=state_root,
        db_path=db_path,
        cache_root=cache_root,
        profiles_root=profiles_root,
        video_format=os.getenv("VIDEO_FORMAT", "shorts"),
        frame_width=int(os.getenv("FRAME_WIDTH", "1080")),
        frame_height=int(os.getenv("FRAME_HEIGHT", "1920")),
        fps=int(os.getenv("FPS", "30")),
        min_clips=int(os.getenv("MIN_CLIPS", "4")),
        max_clips=int(os.getenv("MAX_CLIPS", "8")),
        max_workers=int(os.getenv("MAX_WORKERS", "3")),
        max_retries=int(os.getenv("MAX_RETRIES", "4")),
        retry_base_seconds=int(os.getenv("RETRY_BASE_SECONDS", "4")),
        subtitle_style=os.getenv("SUBTITLE_STYLE", "bottom-box"),
        generate_ideas=_bool("GENERATE_IDEAS", True),
        use_ai_thumbnail=_bool("USE_AI_THUMBNAIL", False),
        upload_to_youtube=_bool("UPLOAD_TO_YOUTUBE", False),
        upload_thumbnail=_bool("UPLOAD_THUMBNAIL", False),
        upload_captions=_bool("UPLOAD_CAPTIONS", False),
        disclose_synthetic_media=_bool("DISCLOSE_SYNTHETIC_MEDIA", False),
        use_openai_moderation=_bool("USE_OPENAI_MODERATION", True),
        notify_subscribers=_bool("NOTIFY_SUBSCRIBERS", False),
        default_category_id=os.getenv("DEFAULT_CATEGORY_ID", "27"),
        default_privacy_status=os.getenv("DEFAULT_PRIVACY_STATUS", "private"),
        publish_interval_minutes=int(os.getenv("PUBLISH_INTERVAL_MINUTES", "60")),
        schedule_start_at=os.getenv("SCHEDULE_START_AT", ""),
        daily_upload_soft_limit=int(os.getenv("DAILY_UPLOAD_SOFT_LIMIT", "90")),
        voice_provider_order=_list("VOICE_PROVIDER_ORDER", "openai"),
        transcribe_provider_order=_list("TRANSCRIBE_PROVIDER_ORDER", "openai"),
        footage_provider_order=_list("FOOTAGE_PROVIDER_ORDER", "pexels,pixabay"),
        image_provider_order=_list("IMAGE_PROVIDER_ORDER", "pexels,pixabay"),
        research_provider_order=_list("RESEARCH_PROVIDER_ORDER", "wikipedia,youtube_transcript,trafilatura,scrapling"),
        youtube_client_secrets=Path(os.getenv("YOUTUBE_CLIENT_SECRETS", "client_secret.json")),
        youtube_token_json=Path(os.getenv("YOUTUBE_TOKEN_JSON", "token.json")),
        blocked_words=_list("BLOCKED_WORDS"),
        duplicate_threshold=float(os.getenv("DUPLICATE_THRESHOLD", "0.82")),
        kokoro_lang_code=os.getenv("KOKORO_LANG_CODE", "a"),
        kokoro_voice=os.getenv("KOKORO_VOICE", "af_heart"),
        piper_bin=os.getenv("PIPER_BIN", "piper"),
        piper_model=os.getenv("PIPER_MODEL", "").strip(),
        piper_config=os.getenv("PIPER_CONFIG", "").strip(),
        faster_whisper_model=os.getenv("FASTER_WHISPER_MODEL", "small"),
    )


settings = load_settings()
