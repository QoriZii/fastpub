"""xAI Grok image generation provider."""
from __future__ import annotations

import base64

import httpx

from fastpub.ai.image_providers.base import ImageProvider


class XAIImageProvider(ImageProvider):
    def __init__(self, api_key: str, model: str = "grok-2-image", base_url: str = "https://api.x.ai/v1"):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    def generate(self, prompt: str, width: int, height: int) -> bytes:
        response = httpx.post(
            f"{self._base_url}/images/generations",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "prompt": prompt,
                "n": 1,
                "size": f"{width}x{height}",
                "response_format": "b64_json",
            },
            timeout=120,
        )
        response.raise_for_status()
        b64_data = response.json()["data"][0]["b64_json"]
        return base64.b64decode(b64_data)
