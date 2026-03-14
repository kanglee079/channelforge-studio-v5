from __future__ import annotations

import re
from difflib import SequenceMatcher

from .models import Idea


def normalize_title(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def token_set(text: str) -> set[str]:
    return set(normalize_title(text).split())


def title_similarity(a: str, b: str) -> float:
    a_n = normalize_title(a)
    b_n = normalize_title(b)
    seq = SequenceMatcher(None, a_n, b_n).ratio()
    ta = token_set(a_n)
    tb = token_set(b_n)
    jacc = len(ta & tb) / max(1, len(ta | tb))
    return max(seq, jacc)


def filter_duplicate_ideas(ideas: list[Idea], seen_titles: list[str], threshold: float = 0.82) -> list[Idea]:
    accepted: list[Idea] = []
    seen = list(seen_titles)
    for idea in ideas:
        if any(title_similarity(idea.title, s) >= threshold for s in seen):
            continue
        accepted.append(idea)
        seen.append(idea.title)
    return accepted
