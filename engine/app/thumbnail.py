from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import settings
from .openai_api import OpenAIHTTP
from .utils import run_cmd


def _best_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def create_thumbnail(video_path: Path, title_text: str, output_path: Path) -> Path:
    if settings.use_ai_thumbnail and settings.openai_api_keys:
        prompt = (
            f"Create a bold YouTube thumbnail background for this topic: {title_text}. "
            "No text in the image. High contrast, dramatic, clean composition, suitable for a faceless educational video."
        )
        OpenAIHTTP(api_key=settings.openai_api_keys[0]).generate_image(prompt=prompt, output_path=output_path, size="1536x1024")
        return output_path

    frame = output_path.with_name("thumb_frame.jpg")
    run_cmd(["ffmpeg", "-y", "-ss", "00:00:01", "-i", str(video_path), "-vframes", "1", str(frame)])

    img = Image.open(frame).convert("RGB").resize((1280, 720))
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 420, 1280, 720), fill=(0, 0, 0, 150))

    font = _best_font(92)
    wrapped = "\n".join(textwrap.wrap(title_text.upper(), width=14))[:80]
    draw.multiline_text(
        (60, 460),
        wrapped,
        font=font,
        fill=(255, 255, 255, 255),
        spacing=8,
        stroke_width=4,
        stroke_fill=(0, 0, 0, 255),
    )

    out = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    out.save(output_path, quality=92)
    return output_path
