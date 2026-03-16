"""TTS Service — Text-to-Speech using OpenAI or ElevenLabs.

Generates voice narration for video scripts.
Returns audio file path + duration.
"""

from __future__ import annotations

import logging
import subprocess
import json
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


class TTSService:
    """Generate speech audio from text."""

    def __init__(self, openai_api_key: str = "", elevenlabs_api_key: str = "",
                 elevenlabs_voice_id: str = "", cache_dir: str = "data/tts_cache"):
        self.openai_key = openai_api_key
        self.elevenlabs_key = elevenlabs_api_key
        self.elevenlabs_voice_id = elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"  # Rachel
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, text: str, output_path: Path | str | None = None,
                 voice: str = "nova",
                 provider: str = "openai") -> dict:
        """Generate TTS audio. Returns {path, duration_sec, provider}."""
        output_path = Path(output_path) if output_path else self.cache_dir / "narration.mp3"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if provider == "openai" and self.openai_key:
            return self._generate_openai(text, output_path, voice)
        elif provider == "elevenlabs" and self.elevenlabs_key:
            return self._generate_elevenlabs(text, output_path)
        elif self.openai_key:
            return self._generate_openai(text, output_path, voice)
        elif self.elevenlabs_key:
            return self._generate_elevenlabs(text, output_path)
        else:
            raise RuntimeError("No TTS API key configured (OpenAI or ElevenLabs)")

    def _generate_openai(self, text: str, output_path: Path, voice: str = "nova") -> dict:
        """Generate using OpenAI TTS API."""
        import openai

        client = openai.OpenAI(api_key=self.openai_key)

        logger.info("Generating TTS (OpenAI, voice=%s, %d chars)...", voice, len(text))
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text,
            instructions="Speak in a clear, engaging, educational tone. "
                         "Emphasize key facts and numbers. Natural pacing with slight pauses between facts.",
            response_format="mp3",
        )

        response.stream_to_file(str(output_path))

        duration = self._get_audio_duration(output_path)
        logger.info("TTS generated: %s (%.1f sec)", output_path.name, duration)

        return {
            "path": str(output_path),
            "duration_sec": duration,
            "provider": "openai",
            "voice": voice,
            "chars": len(text),
        }

    def _generate_elevenlabs(self, text: str, output_path: Path) -> dict:
        """Generate using ElevenLabs TTS API."""
        import httpx

        logger.info("Generating TTS (ElevenLabs, %d chars)...", len(text))

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_key,
        }
        body = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        resp = httpx.post(url, headers=headers, json=body, timeout=60)
        resp.raise_for_status()

        output_path.write_bytes(resp.content)
        duration = self._get_audio_duration(output_path)

        logger.info("TTS generated: %s (%.1f sec)", output_path.name, duration)
        return {
            "path": str(output_path),
            "duration_sec": duration,
            "provider": "elevenlabs",
            "voice": self.elevenlabs_voice_id,
            "chars": len(text),
        }

    def _get_audio_duration(self, path: Path) -> float:
        """Get audio duration using FFprobe."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                capture_output=True, text=True, timeout=10,
            )
            return float(result.stdout.strip())
        except Exception:
            return 30.0  # Default estimate
