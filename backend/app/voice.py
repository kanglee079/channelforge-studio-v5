from __future__ import annotations

from pathlib import Path

from .openai_api import OpenAIHTTP


def generate_voice(narration: str, output_path: Path) -> Path:
    return OpenAIHTTP().text_to_speech(text=narration, output_path=output_path)
