from __future__ import annotations

import random
from pathlib import Path

from .config import settings
from .models import MediaAsset
from .utils import ffprobe_duration, require_bin, run_cmd


def _scale_filter() -> str:
    return (
        f"scale={settings.frame_width}:{settings.frame_height}:force_original_aspect_ratio=increase,"
        f"crop={settings.frame_width}:{settings.frame_height},fps={settings.fps}"
    )


def _subtitle_style_filter(subtitles_path: Path) -> str:
    escaped = subtitles_path.as_posix().replace(":", "\\:")
    if settings.subtitle_style == "bottom-box":
        return f"subtitles='{escaped}':force_style='FontName=Arial,FontSize=18,OutlineColour=&H40000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=80,Alignment=2'"
    return f"subtitles='{escaped}'"


def _video_segment(src: Path, out: Path, start: float, duration: float) -> None:
    run_cmd([
        "ffmpeg", "-y", "-ss", str(start), "-t", str(duration), "-i", str(src),
        "-vf", _scale_filter(), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
    ])


def _image_segment(src: Path, out: Path, duration: float) -> None:
    frames = max(1, int(duration * settings.fps))
    vf = (
        f"scale={settings.frame_width}:{settings.frame_height}:force_original_aspect_ratio=increase,"
        f"crop={settings.frame_width}:{settings.frame_height},"
        f"zoompan=z='min(zoom+0.0007,1.08)':d={frames}:s={settings.frame_width}x{settings.frame_height}:fps={settings.fps}"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-t", str(duration), "-i", str(src),
        "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
    ])


def render_video(assets: list[MediaAsset], voice_path: Path, subtitles_path: Path, output_path: Path, temp_dir: Path) -> Path:
    require_bin("ffmpeg")
    require_bin("ffprobe")
    temp_dir.mkdir(parents=True, exist_ok=True)
    audio_duration = ffprobe_duration(voice_path)
    if not assets:
        raise RuntimeError("No media assets downloaded")

    segment_count = min(max(len(assets), settings.min_clips), settings.max_clips)
    target_each = max(3.0, audio_duration / segment_count)
    rendered_segments: list[Path] = []

    for i in range(segment_count):
        asset = assets[i % len(assets)]
        out = temp_dir / f"seg_{i+1}.mp4"
        if asset.kind == "video":
            clip_dur = ffprobe_duration(asset.path)
            max_start = max(0.0, clip_dur - target_each - 0.2)
            start = 0.0 if max_start == 0 else round(random.uniform(0, max_start), 2)
            _video_segment(asset.path, out, start, target_each)
        else:
            _image_segment(asset.path, out, target_each)
        rendered_segments.append(out)

    concat_txt = temp_dir / "concat.txt"
    concat_txt.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in rendered_segments), encoding="utf-8")

    stitched = temp_dir / "stitched.mp4"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(stitched),
    ])

    run_cmd([
        "ffmpeg", "-y", "-i", str(stitched), "-i", str(voice_path),
        "-vf", _subtitle_style_filter(subtitles_path),
        "-c:v", "libx264", "-c:a", "aac", "-shortest", str(output_path),
    ])
    return output_path
