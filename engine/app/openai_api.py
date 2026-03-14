from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import requests

from .config import settings


class OpenAIHTTP:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or (settings.openai_api_keys[0] if settings.openai_api_keys else "")
        if not self.api_key:
            raise RuntimeError("No OpenAI API key configured")
        self.base_headers = {"Authorization": f"Bearer {self.api_key}"}

    def chat_json_schema(self, *, system: str, user: str, schema_name: str, schema: dict[str, Any], model: str | None = None) -> dict[str, Any]:
        payload = {
            "model": model or settings.openai_text_model,
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": schema},
            },
        }
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={**self.base_headers, "Content-Type": "application/json"},
            json=payload,
            timeout=180,
        )
        res.raise_for_status()
        data = res.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)

    def text_to_speech(self, *, text: str, output_path: Path, voice: str | None = None, model: str | None = None) -> Path:
        payload = {"model": model or settings.openai_tts_model, "input": text, "voice": voice or settings.voice, "format": "mp3"}
        res = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers={**self.base_headers, "Content-Type": "application/json"},
            json=payload,
            timeout=300,
        )
        res.raise_for_status()
        output_path.write_bytes(res.content)
        return output_path

    def transcribe_verbose(self, audio_path: Path) -> dict[str, Any]:
        with audio_path.open("rb") as f:
            files = {"file": (audio_path.name, f, "audio/mpeg")}
            data = {"model": settings.openai_transcribe_model, "response_format": "verbose_json", "timestamp_granularities[]": "word"}
            res = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=self.base_headers,
                files=files,
                data=data,
                timeout=300,
            )
        res.raise_for_status()
        return res.json()

    def generate_image(self, *, prompt: str, output_path: Path, size: str = "1024x1536") -> Path:
        payload = {"model": settings.openai_image_model, "prompt": prompt, "size": size, "quality": "medium", "output_format": "jpeg"}
        res = requests.post(
            "https://api.openai.com/v1/images",
            headers={**self.base_headers, "Content-Type": "application/json"},
            json=payload,
            timeout=300,
        )
        res.raise_for_status()
        data = res.json()
        b64 = data["data"][0]["b64_json"]
        output_path.write_bytes(base64.b64decode(b64))
        return output_path

    def moderate_text(self, text: str) -> dict[str, Any]:
        payload = {"model": "omni-moderation-latest", "input": text}
        res = requests.post(
            "https://api.openai.com/v1/moderations",
            headers={**self.base_headers, "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        res.raise_for_status()
        return res.json()
