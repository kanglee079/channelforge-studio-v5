from __future__ import annotations

from .models import Idea, ResearchPack
from .openai_api import OpenAIHTTP

IDEA_SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "angle": {"type": "string"},
                    "search_terms": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "angle", "search_terms"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["ideas"],
    "additionalProperties": False,
}


def generate_ideas(niche: str, count: int, research: ResearchPack | None = None) -> list[Idea]:
    client = OpenAIHTTP()
    system = (
        "You generate original faceless YouTube video ideas. "
        "Avoid duplicate titles, clickbait spam, and sensitive harmful claims. "
        "Ideas must be easy to visualize with stock footage and easy to verify."
    )
    user = (
        f"Generate {count} short-video ideas for this niche: {niche}. "
        "Each idea must be concise, differentiated from the others, and suitable for 30-90 second or 2 minute educational videos. "
        "Provide 3 to 6 search terms for stock footage."
    )
    if research and research.summary:
        user += f"\n\nContext you may use for idea inspiration:\n{research.summary[:3000]}"
    data = client.chat_json_schema(system=system, user=user, schema_name="ideas_batch", schema=IDEA_SCHEMA)
    return [Idea(**x) for x in data["ideas"]]
