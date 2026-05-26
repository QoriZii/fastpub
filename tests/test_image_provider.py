import pytest
from fastpub.ai.image_providers import get_provider
from fastpub.ai.image_providers.base import ImageProvider


def test_get_provider_returns_image_provider():
    provider = get_provider("xai", api_key="test-key")
    assert isinstance(provider, ImageProvider)


def test_get_provider_unknown_raises():
    with pytest.raises(ValueError, match="Unknown image provider"):
        get_provider("nonexistent", api_key="test-key")


def test_xai_provider_has_generate_method():
    provider = get_provider("xai", api_key="test-key")
    assert callable(getattr(provider, "generate", None))
