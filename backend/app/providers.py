from __future__ import annotations

import io
import wave
from dataclasses import dataclass
from pathlib import Path

import requests

from .config import settings
from .openai_api import OpenAIHTTP
from .retry import retry_call
from .utils import require_bin, run_cmd


@dataclass
class KeyRing:
    keys: list[str]
    _idx: int = 0

    def next(self) -> str:
        if not self.keys:
            raise RuntimeError("No keys configured")
        key = self.keys[self._idx % len(self.keys)]
        self._idx += 1
        return key


class VoiceRouter:
    def __init__(self, provider_order: list[str]) -> None:
        self.provider_order = provider_order
        self.openai_keys = KeyRing(settings.openai_api_keys)
        self.eleven_keys = KeyRing(settings.elevenlabs_api_keys)

    def synthesize(self, text: str, output_path: Path) -> Path:
        errors: list[str] = []
        for provider in self.provider_order:
            try:
                if provider == "openai":
                    key = self.openai_keys.next()
                    return retry_call(lambda: OpenAIHTTP(api_key=key).text_to_speech(text=text, output_path=output_path), tries=2)
                if provider == "elevenlabs":
                    return retry_call(lambda: self._elevenlabs_tts(text, output_path), tries=2)
                if provider == "kokoro":
                    return self._kokoro_tts(text, output_path)
                if provider == "piper":
                    return self._piper_tts(text, output_path)
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
        raise RuntimeError("All voice providers failed: " + " | ".join(errors))

    def _elevenlabs_tts(self, text: str, output_path: Path) -> Path:
        api_key = self.eleven_keys.next()
        voice_id = settings.elevenlabs_voice_id
        if not api_key or not voice_id:
            raise RuntimeError("ELEVENLABS_API_KEY(S) or ELEVENLABS_VOICE_ID missing")
        res = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            params={"output_format": "mp3_44100_128"},
            json={"text": text, "model_id": "eleven_multilingual_v2"},
            timeout=300,
        )
        res.raise_for_status()
        output_path.write_bytes(res.content)
        return output_path

    def _kokoro_tts(self, text: str, output_path: Path) -> Path:
        try:
            import soundfile as sf  # type: ignore
            from kokoro import KPipeline  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"kokoro not installed: {exc}")
        pipe = KPipeline(lang_code=settings.kokoro_lang_code)
        wav_tmp = output_path.with_suffix(".wav")
        pieces = []
        for _, _, audio in pipe(text, voice=settings.kokoro_voice):
            pieces.append(audio)
        if not pieces:
            raise RuntimeError("kokoro returned no audio")
        import numpy as np  # type: ignore
        audio = np.concatenate(pieces)
        sf.write(str(wav_tmp), audio, 24000)
        require_bin("ffmpeg")
        run_cmd(["ffmpeg", "-y", "-i", str(wav_tmp), str(output_path)])
        return output_path

    def _piper_tts(self, text: str, output_path: Path) -> Path:
        if not settings.piper_model:
            raise RuntimeError("PIPER_MODEL missing")
        require_bin(settings.piper_bin)
        wav_tmp = output_path.with_suffix(".wav")
        cmd = [settings.piper_bin, "-m", settings.piper_model, "-f", str(wav_tmp)]
        if settings.piper_config:
            cmd.extend(["-c", settings.piper_config])
        proc = requests  # satisfy linters for no unused imports in environments without piper
        import subprocess
        res = subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True)
        if res.returncode != 0:
            raise RuntimeError(res.stderr.decode("utf-8", errors="ignore"))
        require_bin("ffmpeg")
        run_cmd(["ffmpeg", "-y", "-i", str(wav_tmp), str(output_path)])
        return output_path


class TranscriptionRouter:
    def __init__(self, provider_order: list[str]) -> None:
        self.provider_order = provider_order
        self.openai_keys = KeyRing(settings.openai_api_keys)

    def transcribe_verbose(self, audio_path: Path) -> dict:
        errors: list[str] = []
        for provider in self.provider_order:
            try:
                if provider == "openai":
                    key = self.openai_keys.next()
                    return OpenAIHTTP(api_key=key).transcribe_verbose(audio_path)
                if provider == "faster_whisper":
                    return self._faster_whisper(audio_path)
            except Exception as exc:
                errors.append(f"{provider}: {exc}")
        raise RuntimeError("All transcription providers failed: " + " | ".join(errors))

    def _faster_whisper(self, audio_path: Path) -> dict:
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception as exc:
            raise RuntimeError(f"faster-whisper not installed: {exc}")
        model = WhisperModel(settings.faster_whisper_model, device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(audio_path), word_timestamps=True)
        words = []
        text_parts = []
        for seg in segments:
            text_parts.append(seg.text)
            for w in getattr(seg, 'words', []) or []:
                words.append({"word": w.word, "start": w.start, "end": w.end})
        return {"text": " ".join(x.strip() for x in text_parts if x.strip()), "words": words, "language": getattr(info, 'language', None)}
