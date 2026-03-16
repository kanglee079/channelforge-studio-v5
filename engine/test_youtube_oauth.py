"""Quick OAuth test — Run this to connect YouTube account."""
import sys
from pathlib import Path

print("=" * 50)
print("ChannelForge Studio — YouTube OAuth Connect")
print("=" * 50)

# Check client_secret
cs = Path("client_secret.json")
if not cs.exists():
    print("ERROR: client_secret.json not found in engine/ folder")
    sys.exit(1)
print("[OK] client_secret.json found")

# Run OAuth flow — this WILL open your browser
print("\n>>> Opening browser for Google authorization...")
print(">>> Please log in and click 'Allow'\n")

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=8085, open_browser=True)

print("\n[OK] Authorization successful! Token received.")

# Save token
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
token_path = data_dir / "youtube_token.json"
token_path.write_text(creds.to_json(), encoding="utf-8")
print(f"[OK] Token saved to: {token_path}")

# Get channel info
print("\nFetching channel info...")
from googleapiclient.discovery import build

youtube = build("youtube", "v3", credentials=creds)
resp = youtube.channels().list(part="snippet,statistics", mine=True).execute()

if resp.get("items"):
    ch = resp["items"][0]
    snippet = ch["snippet"]
    stats = ch["statistics"]
    print(f"\n{'=' * 50}")
    print(f"Channel: {snippet['title']}")
    print(f"URL: https://youtube.com/channel/{ch['id']}")
    print(f"Subscribers: {stats.get('subscriberCount', '?')}")
    print(f"Videos: {stats.get('videoCount', '?')}")
    print(f"Views: {stats.get('viewCount', '?')}")
    print(f"Channel ID: {ch['id']}")
    print(f"{'=' * 50}")
    print("\nYouTube account connected successfully!")
else:
    print("No YouTube channel found for this account.")
    print("You may need to create a channel first at youtube.com")
