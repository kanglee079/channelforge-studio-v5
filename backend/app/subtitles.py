from __future__ import annotations

from pathlib import Path

from .providers import TranscriptionRouter


def _fmt(ts: float) -> str:
    ms = int(round(ts * 1000))
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    seconds = ms // 1000
    ms %= 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"


def build_srt_from_transcription(audio_path: Path, output_srt: Path, provider_order: list[str], max_words_per_caption: int = 8) -> Path:
    data = TranscriptionRouter(provider_order).transcribe_verbose(audio_path)
    words = data.get("words") or []
    if not words:
        text = data.get("text", "").split()
        lines = []
        t = 0.0
        step = 2.0
        for i in range(0, len(text), max_words_per_caption):
            group = text[i : i + max_words_per_caption]
            start = t
            end = t + step
            lines.append(f"{len(lines)+1}\n{_fmt(start)} --> {_fmt(end)}\n{' '.join(group)}\n")
            t = end
        output_srt.write_text("\n".join(lines), encoding="utf-8")
        return output_srt

    entries = []
    i = 0
    while i < len(words):
        block = words[i : i + max_words_per_caption]
        text = " ".join(w.get("word", "").strip() for w in block).strip()
        start = float(block[0]["start"])
        end = float(block[-1]["end"])
        if text:
            entries.append((start, end, text))
        i += max_words_per_caption

    lines = []
    for idx, (start, end, text) in enumerate(entries, start=1):
        lines.append(f"{idx}\n{_fmt(start)} --> {_fmt(end)}\n{text}\n")
    output_srt.write_text("\n".join(lines), encoding="utf-8")
    return output_srt
