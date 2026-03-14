from __future__ import annotations

from .config import settings
from .models import ChannelProfile, ScriptPackage
from .openai_api import OpenAIHTTP


HEURISTIC_BLOCKLIST = {
    "how to make a bomb",
    "child porn",
    "suicide tutorial",
}


def moderate_script(script: ScriptPackage, profile: ChannelProfile) -> dict:
    full_text = "\n".join([
        script.title,
        script.description,
        script.hook,
        script.intro,
        *[f"{s['heading']} {s['text']}" for s in script.sections],
        script.outro,
    ])
    lower = full_text.lower()
    blocked = []
    for word in settings.blocked_words + profile.blocked_words:
        if word.lower() in lower:
            blocked.append(f"blocked_word:{word}")
    for word in HEURISTIC_BLOCKLIST:
        if word in lower:
            blocked.append(f"heuristic:{word}")
    result = {"blocked": bool(blocked), "reasons": blocked, "provider": None, "provider_result": None}
    if blocked:
        return result
    if settings.use_openai_moderation and settings.openai_api_keys:
        provider_result = OpenAIHTTP(api_key=settings.openai_api_keys[0]).moderate_text(full_text)
        flagged = False
        categories = {}
        try:
            out = provider_result["results"][0]
            flagged = bool(out.get("flagged"))
            categories = out.get("categories", {})
        except Exception:
            pass
        result.update({
            "provider": "openai",
            "provider_result": provider_result,
            "blocked": flagged,
            "reasons": [k for k, v in categories.items() if v],
        })
    return result
