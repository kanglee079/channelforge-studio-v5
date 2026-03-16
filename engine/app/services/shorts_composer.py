"""Shorts Composer — Full video production pipeline.

Pipeline: Script → TTS → Stock Footage → Compose (video + voice + subs + music) → Final MP4

Output: Vertical YouTube Short (1080×1920, ≤60s)
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ShortSpec:
    """Specification for a YouTube Short."""
    topic: str = ""
    script: str = ""
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    voice: str = "nova"
    keywords: list[str] = field(default_factory=list)
    channel_niche: str = "animals"
    target_countries: list[str] = field(default_factory=lambda: ["US", "UK", "CA", "AU"])


@dataclass
class ShortResult:
    """Result of a Short composition."""
    job_id: str = ""
    video_path: str = ""
    thumbnail_path: str = ""
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    duration_sec: float = 0
    status: str = "pending"
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class ShortsComposer:
    """Compose YouTube Shorts from topic → final video."""

    def __init__(self, openai_key: str = "", pexels_key: str = "",
                 elevenlabs_key: str = "", work_dir: str = "data/shorts_work"):
        self.openai_key = openai_key
        self.pexels_key = pexels_key
        self.elevenlabs_key = elevenlabs_key
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path("data/shorts_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def compose(self, spec: ShortSpec) -> ShortResult:
        """Full pipeline: topic → final Short."""
        job_id = uuid.uuid4().hex[:8]
        job_dir = self.work_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        result = ShortResult(job_id=job_id, title=spec.title, status="processing")

        try:
            # Step 1: Generate script if not provided
            if not spec.script:
                logger.info("[%s] Step 1: Generating script...", job_id)
                spec = self._generate_script(spec)
            result.title = spec.title
            result.description = spec.description
            result.tags = spec.tags

            # Step 2: Generate TTS narration
            logger.info("[%s] Step 2: Generating TTS narration...", job_id)
            audio_path, audio_duration = self._generate_tts(spec, job_dir)

            # Step 3: Fetch stock footage
            logger.info("[%s] Step 3: Fetching stock footage...", job_id)
            clips = self._fetch_footage(spec, job_dir)

            # Step 4: Prepare clips (crop to portrait, trim to fit audio)
            logger.info("[%s] Step 4: Preparing clips...", job_id)
            prepared_clips = self._prepare_clips(clips, audio_duration, job_dir)

            # Step 5: Concatenate clips into one video
            logger.info("[%s] Step 5: Merging clips...", job_id)
            merged_video = self._merge_clips(prepared_clips, job_dir)

            # Step 6: Generate SRT subtitles
            logger.info("[%s] Step 6: Generating subtitles...", job_id)
            srt_path = self._generate_srt(spec.script, audio_duration, job_dir)

            # Step 7: Compose final video (video + audio + subtitles + music)
            logger.info("[%s] Step 7: Final compositing...", job_id)
            final_path = self._compose_final(merged_video, audio_path, srt_path, job_dir)

            # Step 8: Generate thumbnail
            logger.info("[%s] Step 8: Generating thumbnail...", job_id)
            thumb_path = self._generate_thumbnail(final_path, spec, job_dir)

            # Move to output
            out_video = self.output_dir / f"short_{job_id}.mp4"
            out_thumb = self.output_dir / f"thumb_{job_id}.jpg"
            shutil.copy2(final_path, out_video)
            shutil.copy2(thumb_path, out_thumb)

            result.video_path = str(out_video)
            result.thumbnail_path = str(out_thumb)
            result.duration_sec = audio_duration
            result.status = "ready"

            # Save result
            (self.output_dir / f"result_{job_id}.json").write_text(
                json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
            )

            logger.info("[%s] Short ready: %s (%.1fs)", job_id, out_video, audio_duration)

        except Exception as e:
            logger.error("[%s] Composition failed: %s", job_id, e)
            result.status = "error"
            result.error = str(e)

        finally:
            # Cleanup work dir (keep output)
            shutil.rmtree(job_dir, ignore_errors=True)

        return result

    def _generate_script(self, spec: ShortSpec) -> ShortSpec:
        """Use OpenAI to generate a Short script."""
        import openai
        client = openai.OpenAI(api_key=self.openai_key)

        prompt = f"""Create a YouTube Short script about: {spec.topic}
Channel niche: {spec.channel_niche}
Target audience: English speakers in {', '.join(spec.target_countries)}

Requirements:
- Maximum 150 words (for ~45 second video)
- Start with a strong hook (first sentence must grab attention)
- Include 3-4 fascinating facts
- End with a call to action (subscribe, like)
- Educational and engaging tone
- Use numbers and superlatives for impact

Return JSON:
{{"script": "the narration text", "title": "catchy YouTube title (max 70 chars)", "description": "SEO description with hashtags", "tags": ["tag1", "tag2", ...], "keywords": ["visual search keyword 1", "keyword 2", ...]}}"""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
        )

        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```")

        data = json.loads(raw)
        spec.script = data.get("script", spec.topic)
        spec.title = data.get("title", spec.topic)[:70]
        spec.description = data.get("description", "")
        spec.tags = data.get("tags", [])[:20]
        # Always add #Shorts
        if "#Shorts" not in spec.tags:
            spec.tags.insert(0, "#Shorts")
        spec.keywords = data.get("keywords", [spec.topic])

        logger.info("Script generated: %d words, title: %s", len(spec.script.split()), spec.title)
        return spec

    def _generate_tts(self, spec: ShortSpec, job_dir: Path) -> tuple[Path, float]:
        """Generate TTS narration."""
        from .tts_service import TTSService
        tts = TTSService(
            openai_api_key=self.openai_key,
            elevenlabs_api_key=self.elevenlabs_key,
        )
        audio_path = job_dir / "narration.mp3"
        result = tts.generate(spec.script, output_path=audio_path, voice=spec.voice)
        return Path(result["path"]), result["duration_sec"]

    def _fetch_footage(self, spec: ShortSpec, job_dir: Path) -> list[Path]:
        """Fetch stock footage from Pexels."""
        from .pexels_fetcher import PexelsFetcher
        fetcher = PexelsFetcher(api_key=self.pexels_key)

        keywords = spec.keywords if spec.keywords else [spec.topic]
        clips = fetcher.fetch_clips_for_topic(
            spec.topic, num_clips=5, keywords=keywords
        )

        if not clips:
            logger.warning("No stock clips found, creating fallback solid frames")
            clips = [self._create_fallback_clip(job_dir)]

        return clips

    def _create_fallback_clip(self, job_dir: Path) -> Path:
        """Create a fallback clip if no stock footage found."""
        fallback = job_dir / "fallback.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=0x0A1430:s=1080x1920:d=30:r=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(fallback),
        ], capture_output=True, timeout=30)
        return fallback

    def _prepare_clips(self, clips: list[Path], target_duration: float,
                       job_dir: Path) -> list[Path]:
        """Crop clips to portrait (1080x1920) and trim to fill audio duration."""
        prepared = []
        clip_duration = target_duration / len(clips) if clips else target_duration

        for i, clip in enumerate(clips):
            out = job_dir / f"clip_{i:02d}.mp4"
            # Scale and crop to 1080x1920 portrait, trim to clip_duration
            cmd = [
                "ffmpeg", "-y",
                "-i", str(clip),
                "-t", str(clip_duration),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-an",  # Remove audio from clips
                "-pix_fmt", "yuv420p",
                str(out),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and out.exists():
                prepared.append(out)
            else:
                logger.warning("Failed to prepare clip %s: %s", clip.name, result.stderr[-200:])

        return prepared if prepared else [self._create_fallback_clip(job_dir)]

    def _merge_clips(self, clips: list[Path], job_dir: Path) -> Path:
        """Concatenate prepared clips into one video."""
        if len(clips) == 1:
            return clips[0]

        # Create concat file
        concat_file = job_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for clip in clips:
                f.write(f"file '{clip.resolve()}'\n")

        merged = job_dir / "merged.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(merged),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.error("Merge failed: %s", result.stderr[-300:])
            return clips[0]  # Fallback: just use first clip

        return merged

    def _generate_srt(self, script: str, duration: float, job_dir: Path) -> Path:
        """Generate SRT subtitle file from script text."""
        srt_path = job_dir / "subtitles.srt"

        # Split script into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', script.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            sentences = [script]

        # Distribute time evenly across sentences
        time_per_sentence = duration / len(sentences)

        lines = []
        for i, sentence in enumerate(sentences):
            start = i * time_per_sentence
            end = min((i + 1) * time_per_sentence, duration)

            # Format as SRT timecode
            start_tc = self._format_timecode(start)
            end_tc = self._format_timecode(end)

            # Split long sentences into 2 lines (max ~40 chars per line)
            words = sentence.split()
            mid = len(words) // 2
            if len(words) > 6:
                line1 = " ".join(words[:mid])
                line2 = " ".join(words[mid:])
                text = f"{line1}\n{line2}"
            else:
                text = sentence

            lines.append(f"{i + 1}\n{start_tc} --> {end_tc}\n{text}\n")

        srt_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("SRT generated: %d subtitles", len(sentences))
        return srt_path

    def _format_timecode(self, seconds: float) -> str:
        """Format seconds as SRT timecode: HH:MM:SS,mmm"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _compose_final(self, video_path: Path, audio_path: Path,
                       srt_path: Path, job_dir: Path) -> Path:
        """Compose final video: footage + narration + subtitles.

        Subtitle style: bold white text with dark outline, positioned at bottom third.
        """
        final_path = job_dir / "final.mp4"

        # Subtitle filter with styling
        sub_filter = (
            f"subtitles='{srt_path.resolve().as_posix()}':"
            f"force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00000000,BackColour=&H80000000,Outline=2,"
            f"Shadow=1,MarginV=120,Alignment=2,Bold=1'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),       # Video (no audio)
            "-i", str(audio_path),        # Narration audio
            "-filter_complex",
            f"[0:v]{sub_filter}[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(final_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.warning("Subtitles failed, compositing without subs: %s", result.stderr[-200:])
            # Fallback: just merge video + audio without subs
            cmd_fallback = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(final_path),
            ]
            subprocess.run(cmd_fallback, capture_output=True, timeout=300)

        if final_path.exists():
            size_mb = final_path.stat().st_size / (1024 * 1024)
            logger.info("Final video: %.1f MB", size_mb)
        return final_path

    def _generate_thumbnail(self, video_path: Path, spec: ShortSpec,
                            job_dir: Path) -> Path:
        """Extract a frame from video as thumbnail."""
        thumb_path = job_dir / "thumbnail.jpg"

        # Extract frame at 2 seconds
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-ss", "2",
            "-vframes", "1",
            "-q:v", "2",
            str(thumb_path),
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)

        if not thumb_path.exists():
            # Fallback: create solid thumbnail
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (1080, 1920), (10, 15, 45))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 60)
            except Exception:
                font = ImageFont.load_default()
            draw.text((540, 960), spec.title[:30], font=font, fill=(255, 255, 255), anchor="mm")
            img.save(thumb_path, quality=90)

        return thumb_path
