import pytest
from pathlib import Path
from unittest.mock import MagicMock

from fastpub.pipeline.image_gen import generate_images
from fastpub.ai.image_providers.base import ImageProvider


def _make_scenes():
    return [
        {"id": "scene-1", "sceneType": "hook", "imagePrompt": "A diagram of X"},
        {"id": "scene-2", "sceneType": "results", "imagePrompt": "A bar chart showing Y"},
        {"id": "scene-3", "sceneType": "closing", "imagePrompt": ""},
    ]


def test_generate_images_creates_files(tmp_path):
    provider = MagicMock(spec=ImageProvider)
    provider.generate.return_value = b"\x89PNG fake image data"

    scenes = _make_scenes()
    result = generate_images(scenes, provider, tmp_path)

    assert (tmp_path / "scene-1.png").exists()
    assert (tmp_path / "scene-2.png").exists()
    assert not (tmp_path / "scene-3.png").exists()
    assert provider.generate.call_count == 2


def test_generate_images_returns_path_map(tmp_path):
    provider = MagicMock(spec=ImageProvider)
    provider.generate.return_value = b"\x89PNG fake"

    result = generate_images(_make_scenes(), provider, tmp_path)
    assert result["scene-1"] == str(tmp_path / "scene-1.png")
    assert result["scene-2"] == str(tmp_path / "scene-2.png")
    assert "scene-3" not in result


def test_generate_images_skips_empty_prompts(tmp_path):
    provider = MagicMock(spec=ImageProvider)
    scenes = [{"id": "scene-1", "sceneType": "closing", "imagePrompt": ""}]
    result = generate_images(scenes, provider, tmp_path)
    assert result == {}
    provider.generate.assert_not_called()
