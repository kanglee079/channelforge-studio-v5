from __future__ import annotations

from .models import Idea, ResearchPack, ScriptPackage
from .openai_api import OpenAIHTTP

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "hook": {"type": "string"},
        "intro": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["heading", "text"],
                "additionalProperties": False,
            },
        },
        "outro": {"type": "string"},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "search_terms": {"type": "array", "items": {"type": "string"}},
        "thumbnail_text": {"type": "string"},
        "seo_keywords": {"type": "array", "items": {"type": "string"}},
        "disclosure_recommended": {"type": "boolean"},
    },
    "required": [
        "title", "hook", "intro", "sections", "outro", "description", "tags", "search_terms", "thumbnail_text", "seo_keywords", "disclosure_recommended"
    ],
    "additionalProperties": False,
}


def build_script(idea: Idea, research: ResearchPack | None = None, video_format: str = "shorts") -> ScriptPackage:
    client = OpenAIHTTP()
    target_duration = "45-60 seconds" if video_format == "shorts" else "about 2 minutes"
    system = (
        "You are an expert YouTube script writer for faceless educational channels. "
        "Write with short paragraphs, high retention, clean wording, and no filler. "
        "Do not include unverified sensational claims."
    )
    user = (
        f"Create a YouTube script package for this idea:\n"
        f"Title seed: {idea.title}\n"
        f"Angle: {idea.angle}\n"
        f"Target duration: {target_duration}\n"
        "Stock footage search terms should stay relevant to the topic.\n"
        "The description should be 2-4 short paragraphs.\n"
        "Tags should be useful, not keyword stuffing.\n"
        "thumbnail_text should be 2 to 5 words maximum.\n"
        "Set disclosure_recommended=true only if the concept strongly suggests realistic synthetic scenes or cloned voices of other real people."
    )
    if research and research.summary:
        user += f"\n\nReference context (summarized sources):\n{research.summary[:5000]}"
    data = client.chat_json_schema(system=system, user=user, schema_name="script_package", schema=SCRIPT_SCHEMA)
    return ScriptPackage(**data)


def full_narration(script: ScriptPackage) -> str:
    body = [script.hook, script.intro]
    for section in script.sections:
        body.append(section["heading"])
        body.append(section["text"])
    body.append(script.outro)
    return "\n\n".join(x.strip() for x in body if x and x.strip())
