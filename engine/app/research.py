from __future__ import annotations

import re
from typing import Iterable

import requests

from .models import ResearchPack, SourceNote
from .utils import domain_of


WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"


def _wiki_title(topic: str) -> str:
    return topic.strip().replace(" ", "_")


def wikipedia_summary(topic: str) -> SourceNote | None:
    url = WIKI_SUMMARY.format(title=_wiki_title(topic))
    res = requests.get(url, timeout=60, headers={"User-Agent": "youtube-auto-v3/1.0"})
    if res.status_code != 200:
        return None
    data = res.json()
    extract = (data.get("extract") or "").strip()
    title = data.get("title") or topic
    page_url = data.get("content_urls", {}).get("desktop", {}).get("page") or f"https://en.wikipedia.org/wiki/{_wiki_title(topic)}"
    if not extract:
        return None
    return SourceNote(kind="wikipedia", title=title, url=page_url, excerpt=extract[:1200], attribution="Wikipedia")


def youtube_transcripts(urls: Iterable[str]) -> list[SourceNote]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except Exception:
        return []
    notes: list[SourceNote] = []
    api = YouTubeTranscriptApi()
    for url in urls:
        m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
        if not m:
            continue
        video_id = m.group(1)
        try:
            transcript = api.fetch(video_id)
            joined = " ".join(item.text for item in transcript)
            notes.append(SourceNote(kind="youtube_transcript", title=video_id, url=url, excerpt=joined[:1600], attribution="YouTube transcript"))
        except Exception:
            continue
    return notes


def extract_article_text(url: str) -> SourceNote | None:
    try:
        import trafilatura  # type: ignore

        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False, favor_precision=True)
            if text:
                title = domain_of(url)
                return SourceNote(kind="trafilatura", title=title, url=url, excerpt=text[:2000], attribution="trafilatura")
    except Exception:
        pass

    try:
        from scrapling.fetchers import Fetcher  # type: ignore

        page = Fetcher.get(url)
        text = " ".join(page.css("body ::text").getall())
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            return SourceNote(kind="scrapling", title=domain_of(url), url=url, excerpt=text[:2000], attribution="Scrapling")
    except Exception:
        pass
    return None


def build_research_pack(topic: str, seed_urls: list[str] | None = None, youtube_urls: list[str] | None = None) -> ResearchPack:
    notes: list[SourceNote] = []
    wiki = wikipedia_summary(topic)
    if wiki:
        notes.append(wiki)
    for url in youtube_urls or []:
        notes.extend(youtube_transcripts([url]))
    for url in seed_urls or []:
        note = extract_article_text(url)
        if note:
            notes.append(note)
    summary = "\n\n".join(f"[{n.kind}] {n.title}: {n.excerpt}" for n in notes[:5])
    return ResearchPack(topic=topic, summary=summary[:6000], notes=notes)
