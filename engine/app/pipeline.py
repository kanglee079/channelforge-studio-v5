from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .config import settings
from .db import add_title_index, claim_jobs, enqueue_job, get_indexed_titles, get_upload_count_today, increment_upload_count, init_db, mark_done, mark_failed, mark_retry
from .dedupe import filter_duplicate_ideas, normalize_title
from .footage import fetch_media_assets
from .models import ChannelProfile, Idea, JobPaths, JobResult
from .moderation import moderate_script
from .planner import generate_ideas
from .profiles import load_profile
from .providers import VoiceRouter
from .quota import estimate_quota
from .render import render_video
from .research import build_research_pack
from .scheduler import schedule_publish_at
from .scriptgen import build_script, full_narration
from .subtitles import build_srt_from_transcription
from .thumbnail import create_thumbnail
from .utils import save_json, slugify, utc_now_iso
from .youtube_upload import upload_video


def make_paths(channel: str, job_id: int, title: str) -> JobPaths:
    slug = f"{job_id:06d}-{slugify(title)}"
    root = settings.output_root / channel / slug
    root.mkdir(parents=True, exist_ok=True)
    clips_dir = root / "clips"
    temp_dir = root / "temp"
    clips_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)
    return JobPaths(
        root=root,
        research_json=root / "research.json",
        idea_json=root / "idea.json",
        script_json=root / "script.json",
        moderation_json=root / "moderation.json",
        voice_audio=root / "voice.mp3",
        subtitles_srt=root / "subtitles.srt",
        thumbnail_jpg=root / "thumbnail.jpg",
        final_mp4=root / "final.mp4",
        credits_json=root / "credits.json",
        upload_json=root / "upload.json",
        clips_dir=clips_dir,
        temp_dir=temp_dir,
    )


def ideas_from_topic_file(topic_file: Path, count: int) -> list[Idea]:
    lines = [x.strip() for x in topic_file.read_text(encoding="utf-8").splitlines() if x.strip()]
    if not lines:
        raise RuntimeError("Topic file is empty")
    ideas: list[Idea] = []
    if settings.generate_ideas:
        per_seed = max(1, count // len(lines))
        for niche in lines:
            ideas.extend(generate_ideas(niche=niche, count=per_seed))
        return ideas[:count]
    return [Idea(title=line, angle=line, search_terms=[line]) for line in lines[:count]]


def enqueue_batch(*, profile: ChannelProfile, count: int, niche: str | None, topic_file: Path | None, video_format: str, seed_url_file: Path | None = None, youtube_url_file: Path | None = None) -> list[int]:
    init_db()
    quota_needed = estimate_quota(count, settings.upload_thumbnail, settings.upload_captions) if profile.upload_enabled else 0
    print(f"[info] upload_enabled={profile.upload_enabled} estimated_quota={quota_needed}")

    research = build_research_pack(niche or profile.niche) if niche or profile.niche else None
    if niche:
        ideas = generate_ideas(niche=niche, count=count, research=research) if settings.generate_ideas else [Idea(title=niche, angle=niche, search_terms=[niche])]
    elif topic_file:
        ideas = ideas_from_topic_file(topic_file, count)
    else:
        raise RuntimeError("Provide either niche or topic_file")

    seed_urls = [x.strip() for x in seed_url_file.read_text(encoding='utf-8').splitlines() if x.strip()] if seed_url_file and seed_url_file.exists() else []
    yt_urls = [x.strip() for x in youtube_url_file.read_text(encoding='utf-8').splitlines() if x.strip()] if youtube_url_file and youtube_url_file.exists() else []
    for idea in ideas:
        if seed_urls:
            idea.seed_urls = seed_urls
        if yt_urls:
            idea.youtube_urls = yt_urls

    ideas = filter_duplicate_ideas(ideas[:count], get_indexed_titles(profile.name), threshold=settings.duplicate_threshold)
    job_ids = []
    for idea in ideas:
        payload = {"idea": idea.__dict__, "video_format": video_format or profile.default_video_format, "profile": profile.to_dict()}
        job_ids.append(enqueue_job(profile.name, idea.title, payload))
    return job_ids


def _process_claimed_job(row) -> JobResult:
    payload = json.loads(row["payload_json"])
    profile = ChannelProfile(**payload["profile"])
    idea = Idea(**payload["idea"])
    job_id = int(row["id"])
    paths = make_paths(profile.name, job_id, idea.title)
    save_json(paths.idea_json, idea.__dict__)

    research = build_research_pack(idea.title, seed_urls=idea.seed_urls, youtube_urls=idea.youtube_urls)
    save_json(paths.research_json, {"topic": research.topic, "summary": research.summary, "notes": [n.__dict__ for n in research.notes]})

    script = build_script(idea, research=research, video_format=payload.get("video_format", profile.default_video_format))
    if profile.title_prefix:
        script.title = (profile.title_prefix + script.title)[:100]
    merged_tags = []
    for tag in (profile.tags + script.tags + script.seo_keywords):
        if tag not in merged_tags:
            merged_tags.append(tag)
    script.tags = merged_tags[:30]
    save_json(paths.script_json, script.__dict__)

    moderation = moderate_script(script, profile)
    save_json(paths.moderation_json, moderation)
    if moderation.get("blocked"):
        raise RuntimeError("blocked by moderation: " + ", ".join(moderation.get("reasons") or []))

    narration = full_narration(script)
    VoiceRouter(profile.voice_provider_order or settings.voice_provider_order).synthesize(narration, paths.voice_audio)
    build_srt_from_transcription(paths.voice_audio, paths.subtitles_srt, profile.transcribe_provider_order or settings.transcribe_provider_order)

    assets = fetch_media_assets(script.search_terms or idea.search_terms, paths.clips_dir, paths.credits_json, profile.footage_provider_order or settings.footage_provider_order)
    render_video(assets, paths.voice_audio, paths.subtitles_srt, paths.final_mp4, paths.temp_dir)
    create_thumbnail(paths.final_mp4, script.thumbnail_text, paths.thumbnail_jpg)

    upload_info = {"upload_enabled": False, "publish_at": None, "daily_soft_limit_hit": False}
    final_state = "done"
    if profile.upload_enabled and settings.upload_to_youtube:
        count_today = get_upload_count_today(profile.name)
        if count_today >= profile.daily_upload_soft_limit:
            upload_info["daily_soft_limit_hit"] = True
            final_state = "rendered"
        else:
            publish_at = schedule_publish_at(count_today, interval_minutes=profile.publish_interval_minutes, schedule_start_at=settings.schedule_start_at or None)
            upload_info = upload_video(
                profile=profile,
                video_path=paths.final_mp4,
                thumbnail_path=paths.thumbnail_jpg,
                title=script.title,
                description=script.description,
                tags=script.tags,
                publish_at=publish_at,
                srt_path=paths.subtitles_srt,
            )
            increment_upload_count(profile.name)
            final_state = "uploaded"
    save_json(paths.upload_json, upload_info)
    add_title_index(profile.name, normalize_title(script.title), script.title, job_id=job_id)
    return JobResult(
        title=script.title,
        root=paths.root,
        video_path=paths.final_mp4,
        thumbnail_path=paths.thumbnail_jpg,
        state=final_state,
        scheduled_publish_at=upload_info.get("publish_at"),
        youtube_video_id=upload_info.get("video_id"),
        extra=upload_info,
    )


def run_workers(*, channel: str | None, limit: int = 10) -> list[JobResult]:
    init_db()
    rows = claim_jobs(limit=limit, channel=channel)
    results: list[JobResult] = []
    if not rows:
        return results
    with ThreadPoolExecutor(max_workers=settings.max_workers) as ex:
        futures = {ex.submit(_process_claimed_job, row): row for row in rows}
        for future in as_completed(futures):
            row = futures[future]
            job_id = int(row['id'])
            retries = int(row['retries'])
            try:
                result = future.result()
                mark_done(job_id, {"title": result.title, "root": str(result.root), "state": result.state, "youtube_video_id": result.youtube_video_id, "publish_at": result.scheduled_publish_at, "extra": result.extra}, final_state=result.state)
                print(f"[done] #{job_id}: {result.title} ({result.state})")
                results.append(result)
            except Exception as exc:
                if retries + 1 < settings.max_retries:
                    next_attempt = (datetime.now(timezone.utc) + timedelta(seconds=settings.retry_base_seconds * (2 ** retries))).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                    mark_retry(job_id, str(exc), retries + 1, next_attempt)
                    print(f"[retry] #{job_id}: {exc}")
                else:
                    final_state = 'blocked' if 'moderation' in str(exc) else 'failed'
                    mark_failed(job_id, str(exc), final_state=final_state)
                    print(f"[error] #{job_id}: {exc}")
    return results
