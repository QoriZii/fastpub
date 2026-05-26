import json
from pathlib import Path
from fastpub.render.video import build_manifest
from fastpub.models import PaperMeta


def test_build_manifest_structure(tmp_path):
    meta = PaperMeta(title="Test", authors=["A"], venue="CHI", year=2026)
    scenes = [
        {"id": "scene-1", "sceneType": "hook", "headline": "H", "body": "B", "narration": "N", "imagePrompt": "P", "transition": "fade"},
    ]
    audio_map = {"scene-1": {"path": str(tmp_path / "s1.mp3"), "duration": 5.2}}
    image_map = {"scene-1": str(tmp_path / "s1.png")}

    manifest = build_manifest(meta, scenes, audio_map, image_map)

    assert manifest["meta"]["title"] == "Test"
    assert manifest["settings"]["width"] == 1920
    assert manifest["settings"]["fps"] == 30
    assert len(manifest["scenes"]) == 1

    s = manifest["scenes"][0]
    assert s["id"] == "scene-1"
    assert s["type"] == "hook"
    assert s["durationSec"] == 5.2
    assert s["headline"] == "H"
    assert s["narration"] == "N"


def test_build_manifest_scene_without_image():
    meta = PaperMeta(title="Test", authors=["A"])
    scenes = [
        {"id": "scene-1", "sceneType": "closing", "headline": "H", "body": "", "narration": "N", "imagePrompt": "", "transition": "fade"},
    ]
    audio_map = {"scene-1": {"path": "audio/s1.mp3", "duration": 3.0}}
    image_map = {}

    manifest = build_manifest(meta, scenes, audio_map, image_map)
    assert manifest["scenes"][0]["imageFile"] is None
