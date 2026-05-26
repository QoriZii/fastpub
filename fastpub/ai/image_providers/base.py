"""Abstract base for image generation providers."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, width: int, height: int) -> bytes:
        """Generate an image from a text prompt. Returns PNG bytes."""
        ...
