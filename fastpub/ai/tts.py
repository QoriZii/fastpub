"""Text-to-Speech via xAI Grok API.

Endpoint: POST https://api.x.ai/v1/tts
Docs: https://docs.x.ai/developers/model-capabilities/audio/voice
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import httpx

TTS_VOICES = ["eve", "ara", "rex", "sal", "leo"]


def generate_speech(
    text: str,
    output_path: str,
    api_key: str,
    voice: str = "sal",
    language: str = "en",
    base_url: str = "https://api.x.ai/v1",
) -> str:
    """Generate speech audio from text using the xAI TTS API. Returns output file path."""
    response = httpx.post(
        f"{base_url}/tts",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"text": text, "voice_id": voice, "language": language},
        timeout=60,
    )
    response.raise_for_status()

    Path(output_path).write_bytes(response.content)
    return output_path


def get_audio_duration(file_path: str) -> float:
    """Get the duration of an audio file in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", file_path],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())
