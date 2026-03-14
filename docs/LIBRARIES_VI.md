
# Thư viện / source open nên áp dụng cho dự án

## Nhóm scraping / research
- Scrapling: adaptive scraping, spiders, proxy rotation
- Trafilatura: bóc text, metadata, main content
- youtube-transcript-api: transcript từ YouTube public
- feedparser: RSS ingest cực nhẹ
- BeautifulSoup: fallback HTML parsing

## Nhóm trend / discovery
- Google Trends Trending Now web/RSS
- GDELT doc API
- NewsAPI
- SerpApi
- Hacker News RSS, Reddit RSS, niche RSS feeds

## Nhóm ASR / subtitle
- OpenAI transcription
- faster-whisper
- WhisperX

## Nhóm TTS
- OpenAI TTS
- ElevenLabs
- Kokoro
- Piper

## Nhóm render / video
- FFmpeg
- MoviePy
- Remotion nếu bạn muốn dựng scene dynamic đẹp hơn

## Nhóm orchestration
- APScheduler
- SQLite
- sau này có thể nâng sang Redis + Celery / RQ
