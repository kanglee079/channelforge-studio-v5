"""Test: Generate and upload a YouTube Short — full pipeline."""

import logging
import json
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("test_shorts")

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.shorts_composer import ShortsComposer, ShortSpec

print("=" * 60)
print("Test: Full Shorts Video Production Pipeline")
print("=" * 60)

# Initialize composer
composer = ShortsComposer(
    openai_key=settings.openai_api_keys[0] if settings.openai_api_keys else "",
    pexels_key=settings.pexels_api_key,
    elevenlabs_key=settings.elevenlabs_api_keys[0] if settings.elevenlabs_api_keys else "",
)

# Create spec — let AI generate script
spec = ShortSpec(
    topic="Amazing Octopus Intelligence — 9 brains, 3 hearts, camouflage master",
    channel_niche="animals",
    voice="nova",
)

print("\n>>> Starting pipeline: topic -> script -> TTS -> footage -> compose")
print(f">>> Topic: {spec.topic}")
print(f">>> Voice: {spec.voice}")
print()

# Run pipeline
result = composer.compose(spec)

print("\n" + "=" * 60)
print(f"Status: {result.status}")
if result.status == "ready":
    print(f"Video: {result.video_path}")
    print(f"Thumbnail: {result.thumbnail_path}")
    print(f"Duration: {result.duration_sec:.1f}s")
    print(f"Title: {result.title}")
    print(f"Tags: {result.tags[:5]}...")

    # Upload to YouTube
    print("\n>>> Uploading to YouTube...")
    from app.services.youtube_auth import youtube_auth
    if youtube_auth.is_authenticated:
        from googleapiclient.http import MediaFileUpload
        youtube = youtube_auth.get_youtube_service()

        tags = result.tags
        if "#Shorts" not in tags:
            tags.insert(0, "#Shorts")

        body = {
            "snippet": {
                "title": result.title[:100],
                "description": result.description + "\n\n#Shorts",
                "tags": tags[:30],
                "categoryId": "15",
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        }

        insert_req = youtube.videos().insert(
            part="snippet,status",
            body=body,
            notifySubscribers=True,
            media_body=MediaFileUpload(
                result.video_path, chunksize=8 * 1024 * 1024, resumable=True
            ),
        )
        response = None
        while response is None:
            status, response = insert_req.next_chunk()
            if status:
                print(f"  Upload: {status.progress() * 100:.0f}%")

        video_id = response["id"]
        print(f"\n[OK] Uploaded! https://youtube.com/shorts/{video_id}")
    else:
        print("[SKIP] YouTube not authenticated")
else:
    print(f"Error: {result.error}")

print("=" * 60)
