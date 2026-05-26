"""Image provider factory."""
from __future__ import annotations

from fastpub.ai.image_providers.base import ImageProvider


def get_provider(name: str, *, api_key: str, **kwargs) -> ImageProvider:
    """Get an image provider by name."""
    match name:
        case "xai":
            from fastpub.ai.image_providers.xai import XAIImageProvider
            return XAIImageProvider(api_key=api_key, **kwargs)
        case _:
            raise ValueError(f"Unknown image provider: {name!r}. Available: xai")
