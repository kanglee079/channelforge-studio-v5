"""Create and Upload Animal Facts Video — High CPM Strategy

Channel: Animals World Facts KVH
Target: Tier-1 countries (US, UK, Canada, Australia)
Strategy: Educational animal facts in English, optimized SEO
"""

import subprocess
import sys
import os
import json
import shutil
import tempfile
from pathlib import Path

# ── VIDEO CONFIGURATION ─────────────────────────────────────────
WIDTH, HEIGHT = 1920, 1080  # Full HD
FPS = 30
SECONDS_PER_FACT = 6
TRANSITION_FRAMES = 15

# ── CONTENT: 8 Mind-Blowing Animal Facts (Educational, Tier-1 optimized) ──
FACTS = [
    {
        "title": "🐙 Octopus Intelligence",
        "fact": "Octopuses have 9 brains — one central brain\nand one in each of their 8 arms.\nEach arm can taste, touch and move independently.",
        "bg_color": (15, 25, 65),     # Deep navy
        "accent": (0, 180, 255),       # Bright blue
    },
    {
        "title": "🦑 Immortal Jellyfish",
        "fact": "Turritopsis dohrnii can reverse its aging process,\nturning back into a juvenile polyp.\nIt's the only known biologically immortal species.",
        "bg_color": (10, 40, 50),
        "accent": (0, 230, 180),
    },
    {
        "title": "🐋 Blue Whale Heart",
        "fact": "A Blue Whale's heart is so massive\nthat a small child could crawl through its arteries.\nIt weighs around 400 pounds (180 kg).",
        "bg_color": (10, 30, 70),
        "accent": (100, 180, 255),
    },
    {
        "title": "🦈 Sharks Older Than Trees",
        "fact": "Sharks have existed for over 450 million years.\nThat's 90 million years BEFORE the first trees appeared.\nThey survived 5 mass extinctions.",
        "bg_color": (20, 20, 40),
        "accent": (255, 120, 50),
    },
    {
        "title": "🐧 Emperor Penguin Diving",
        "fact": "Emperor Penguins can dive to depths of 1,800 feet\nand hold their breath for over 20 minutes.\nThat's deeper than most submarines operate.",
        "bg_color": (15, 25, 55),
        "accent": (180, 220, 255),
    },
    {
        "title": "🐝 Honeybee Mathematics",
        "fact": "Honeybees can understand the concept of zero,\nperform basic addition and subtraction,\nand navigate using the sun as a compass.",
        "bg_color": (45, 30, 5),
        "accent": (255, 200, 0),
    },
    {
        "title": "🦅 Peregrine Falcon Speed",
        "fact": "The Peregrine Falcon reaches 240 mph (386 km/h)\nduring hunting dives — making it the fastest\nanimal on Earth, faster than most race cars.",
        "bg_color": (30, 20, 10),
        "accent": (255, 160, 50),
    },
    {
        "title": "🐬 Dolphin Sleep Pattern",
        "fact": "Dolphins sleep with one eye open.\nOnly half their brain rests at a time,\nso they can keep breathing and watch for predators.",
        "bg_color": (5, 30, 55),
        "accent": (80, 200, 255),
    },
]

# ── SEO-OPTIMIZED METADATA (Targeting US/UK/CA/AU) ─────────────
VIDEO_TITLE = "8 Mind-Blowing Animal Facts That Will Change How You See Nature"
VIDEO_DESCRIPTION = """🧠 Did you know octopuses have 9 brains? Or that sharks are OLDER than trees?

Discover 8 incredible animal facts backed by science that will completely change how you see the natural world.

📋 Facts in this video:
00:00 - Octopus Intelligence (9 Brains!)
00:06 - The Immortal Jellyfish
00:12 - Blue Whale Heart Size
00:18 - Sharks Are Older Than Trees
00:24 - Emperor Penguin Deep Diving
00:30 - Honeybee Mathematics
00:36 - Peregrine Falcon Speed Record
00:42 - Dolphin Sleep Pattern

🔔 Subscribe for more mind-blowing animal facts every week!
👍 Like this video if you learned something new!

#AnimalFacts #NatureFacts #WildlifeEducation #ScienceFacts #MarineBiology #OceanLife #AmazingAnimals #NatureDocumentary #AnimalIntelligence #WildlifeConservation

© Animals World Facts KVH — Educational content about the natural world."""

VIDEO_TAGS = [
    "animal facts", "amazing animal facts", "nature facts",
    "wildlife education", "science facts", "marine biology",
    "octopus brain", "immortal jellyfish", "blue whale heart",
    "shark facts", "peregrine falcon speed", "dolphin sleep",
    "emperor penguin", "honeybee intelligence",
    "mind blowing facts", "nature documentary", "animal intelligence",
    "educational video", "wildlife conservation", "ocean facts",
    "did you know animals", "animal trivia", "biology facts",
    "top animal facts", "animals world facts",
]


def create_frames(output_dir: Path):
    """Create video frames using Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    # Try to load a nice font, fallback to default
    font_title = None
    font_fact = None
    font_watermark = None
    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                font_title = ImageFont.truetype(fp, 72)
                font_fact = ImageFont.truetype(fp, 44)
                font_watermark = ImageFont.truetype(fp, 28)
                break
            except Exception:
                pass
    if font_title is None:
        font_title = ImageFont.load_default()
        font_fact = ImageFont.load_default()
        font_watermark = ImageFont.load_default()

    frame_num = 0
    total_facts = len(FACTS)

    # Intro frame (2 seconds)
    for f in range(FPS * 2):
        img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 30))
        draw = ImageDraw.Draw(img)

        # Animated title
        alpha = min(1.0, f / (FPS * 0.8))
        draw.text(
            (WIDTH // 2, HEIGHT // 2 - 80),
            "🌍 ANIMALS WORLD FACTS",
            font=font_title, fill=(255, 255, 255), anchor="mm",
        )
        draw.text(
            (WIDTH // 2, HEIGHT // 2 + 20),
            "8 Mind-Blowing Facts About Animals",
            font=font_fact, fill=(180, 220, 255), anchor="mm",
        )
        draw.text(
            (WIDTH // 2, HEIGHT - 50),
            "Animals World Facts KVH",
            font=font_watermark, fill=(100, 100, 120), anchor="mm",
        )

        img.save(output_dir / f"frame_{frame_num:05d}.png")
        frame_num += 1

    # Each fact
    for idx, fact_data in enumerate(FACTS):
        bg = fact_data["bg_color"]
        accent = fact_data["accent"]
        num_frames = FPS * SECONDS_PER_FACT

        for f in range(num_frames):
            img = Image.new("RGB", (WIDTH, HEIGHT), bg)
            draw = ImageDraw.Draw(img)

            # Progress bar at top
            progress = (idx * SECONDS_PER_FACT + f / FPS) / (total_facts * SECONDS_PER_FACT)
            bar_width = int(WIDTH * progress)
            draw.rectangle([(0, 0), (bar_width, 6)], fill=accent)

            # Fact number
            draw.text(
                (WIDTH // 2, 80),
                f"FACT {idx + 1} OF {total_facts}",
                font=font_watermark, fill=accent, anchor="mm",
            )

            # Title with emoji
            draw.text(
                (WIDTH // 2, HEIGHT // 2 - 120),
                fact_data["title"],
                font=font_title, fill=(255, 255, 255), anchor="mm",
            )

            # Horizontal line
            line_y = HEIGHT // 2 - 50
            draw.rectangle(
                [(WIDTH // 2 - 200, line_y), (WIDTH // 2 + 200, line_y + 3)],
                fill=accent,
            )

            # Fact text
            y = HEIGHT // 2 + 10
            for line in fact_data["fact"].split("\n"):
                draw.text(
                    (WIDTH // 2, y),
                    line.strip(),
                    font=font_fact, fill=(220, 230, 255), anchor="mm",
                )
                y += 55

            # Watermark
            draw.text(
                (WIDTH // 2, HEIGHT - 50),
                "Animals World Facts KVH  |  Subscribe for more!",
                font=font_watermark, fill=(80, 90, 110), anchor="mm",
            )

            img.save(output_dir / f"frame_{frame_num:05d}.png")
            frame_num += 1

    # Outro (3 seconds)
    for f in range(FPS * 3):
        img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 30))
        draw = ImageDraw.Draw(img)

        draw.text(
            (WIDTH // 2, HEIGHT // 2 - 60),
            "🔔 SUBSCRIBE FOR MORE",
            font=font_title, fill=(255, 255, 255), anchor="mm",
        )
        draw.text(
            (WIDTH // 2, HEIGHT // 2 + 40),
            "New animal facts every week!",
            font=font_fact, fill=(100, 200, 255), anchor="mm",
        )
        draw.text(
            (WIDTH // 2, HEIGHT // 2 + 110),
            "👍 Like  |  💬 Comment  |  🔗 Share",
            font=font_fact, fill=(180, 180, 200), anchor="mm",
        )
        draw.text(
            (WIDTH // 2, HEIGHT - 50),
            "© Animals World Facts KVH",
            font=font_watermark, fill=(100, 100, 120), anchor="mm",
        )

        img.save(output_dir / f"frame_{frame_num:05d}.png")
        frame_num += 1

    print(f"[OK] Created {frame_num} frames")
    return frame_num


def create_thumbnail(output_path: Path):
    """Create an eye-catching thumbnail."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1280, 720), (10, 15, 45))
    draw = ImageDraw.Draw(img)

    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    font_big = None
    font_med = None
    for fp in font_paths:
        if Path(fp).exists():
            try:
                font_big = ImageFont.truetype(fp, 90)
                font_med = ImageFont.truetype(fp, 50)
                font_small = ImageFont.truetype(fp, 36)
                break
            except Exception:
                pass
    if font_big is None:
        font_big = ImageFont.load_default()
        font_med = font_big
        font_small = font_big

    # Gradient-like colored rectangles
    draw.rectangle([(0, 0), (1280, 8)], fill=(0, 200, 255))
    draw.rectangle([(0, 712), (1280, 720)], fill=(255, 120, 50))

    # Big text
    draw.text(
        (640, 200), "8 MIND-BLOWING",
        font=font_big, fill=(255, 255, 255), anchor="mm",
    )
    draw.text(
        (640, 320), "ANIMAL FACTS",
        font=font_big, fill=(0, 200, 255), anchor="mm",
    )

    # Subtitle
    draw.text(
        (640, 440), "🧠 9 Brains · 🦈 450M Years · 🐋 400lb Heart",
        font=font_med, fill=(255, 200, 100), anchor="mm",
    )

    # CTA
    draw.text(
        (640, 560), "You Won't Believe #4!",
        font=font_med, fill=(255, 100, 100), anchor="mm",
    )

    draw.text(
        (640, 660), "Animals World Facts KVH",
        font=font_small, fill=(150, 150, 170), anchor="mm",
    )

    img.save(output_path, quality=95)
    print(f"[OK] Thumbnail created: {output_path}")


def encode_video(frames_dir: Path, output_path: Path, total_frames: int):
    """Encode frames to MP4 using FFmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]
    print(f"[...] Encoding video ({total_frames} frames)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] FFmpeg failed: {result.stderr[-500:]}")
        sys.exit(1)
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[OK] Video encoded: {output_path} ({size_mb:.1f} MB)")


def upload_to_youtube(video_path: Path, thumbnail_path: Path):
    """Upload video to YouTube using saved OAuth token."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    SCOPES = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.upload",
    ]

    token_path = Path("data/youtube_token.json")
    if not token_path.exists():
        print("[ERROR] YouTube token not found. Run test_youtube_oauth.py first.")
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": VIDEO_TITLE,
            "description": VIDEO_DESCRIPTION,
            "tags": VIDEO_TAGS,
            "categoryId": "15",  # Pets & Animals
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
        },
    }

    print("[...] Uploading video to YouTube...")
    insert_req = youtube.videos().insert(
        part="snippet,status",
        body=body,
        notifySubscribers=True,
        media_body=MediaFileUpload(
            str(video_path), chunksize=1024 * 1024 * 8, resumable=True,
        ),
    )

    response = None
    while response is None:
        status, response = insert_req.next_chunk()
        if status:
            pct = status.progress() * 100
            print(f"  Upload progress: {pct:.0f}%")

    video_id = response["id"]
    print(f"[OK] Video uploaded! ID: {video_id}")
    print(f"     URL: https://www.youtube.com/watch?v={video_id}")

    # Upload thumbnail
    print("[...] Setting custom thumbnail...")
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumbnail_path)),
        ).execute()
        print("[OK] Thumbnail set!")
    except Exception as e:
        print(f"[WARN] Thumbnail upload failed (may need channel verification): {e}")

    return video_id


def main():
    print("=" * 60)
    print("Animals World Facts KVH — Video Creator & Uploader")
    print("Target: High CPM (US/UK/CA/AU) | Category: Education")
    print("=" * 60)

    output_dir = Path("data/video_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    video_path = output_dir / "animal_facts_001.mp4"
    thumb_path = output_dir / "thumbnail_001.jpg"

    # Step 1: Create thumbnail
    print("\n--- Step 1: Creating thumbnail ---")
    create_thumbnail(thumb_path)

    # Step 2: Create video frames
    print("\n--- Step 2: Creating video frames ---")
    frames_dir = output_dir / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir()
    total_frames = create_frames(frames_dir)

    # Step 3: Encode video
    print("\n--- Step 3: Encoding video with FFmpeg ---")
    encode_video(frames_dir, video_path, total_frames)

    # Step 4: Upload to YouTube
    print("\n--- Step 4: Uploading to YouTube ---")
    video_id = upload_to_youtube(video_path, thumb_path)

    # Cleanup frames
    print("\n--- Cleanup ---")
    shutil.rmtree(frames_dir, ignore_errors=True)
    print("[OK] Temporary frames cleaned up")

    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE!")
    print(f"Video: https://www.youtube.com/watch?v={video_id}")
    print(f"Channel: https://youtube.com/channel/UCQ-4mdLAb3EmnRRMbXhawrQ")
    print("=" * 60)

    # Save upload record
    record = {
        "video_id": video_id,
        "title": VIDEO_TITLE,
        "tags": VIDEO_TAGS,
        "channel": "Animals World Facts KVH",
        "target_countries": ["US", "UK", "CA", "AU"],
        "category": "15 (Pets & Animals)",
        "strategy": "Educational animal facts, Tier-1 CPM optimization",
    }
    record_path = output_dir / f"upload_record_{video_id}.json"
    record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Upload record saved: {record_path}")


if __name__ == "__main__":
    main()
