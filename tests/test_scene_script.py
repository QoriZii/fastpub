import json
from fastpub.pipeline.scene_script import generate_scene_script
from fastpub.models import PaperDocument, PaperMeta, PaperSection, Narrative


def _make_doc() -> PaperDocument:
    return PaperDocument(
        meta=PaperMeta(
            title="Test Paper",
            authors=["Alice", "Bob"],
            venue="CHI",
            year=2026,
            abstract="Test abstract.",
        ),
        sections=[
            PaperSection(id="s1", type="method", title="Method", summary="We did X.", key_points=["Point A"]),
            PaperSection(id="s2", type="result", title="Results", summary="We found Y.", key_points=["Point B"]),
        ],
        narrative=Narrative(
            hook="Why does X matter?",
            problem="X is hard.",
            approach="We use Y.",
            results=["Result 1"],
            significance="This changes Z.",
        ),
    )


def test_generate_scene_script_returns_list():
    """Test with a mock LLM response — we patch _call_llm."""
    mock_scenes = [
        {
            "sceneType": "hook",
            "headline": "Why X matters",
            "body": "Supporting text",
            "narration": "Voiceover text here.",
            "imagePrompt": "A conceptual illustration of X",
            "transition": "fade",
        },
        {
            "sceneType": "closing",
            "headline": "Test Paper",
            "body": "Alice, Bob — CHI 2026",
            "narration": "Thank you for watching.",
            "imagePrompt": "",
            "transition": "fade",
        },
    ]

    import fastpub.pipeline.scene_script as mod
    _original = mod._call_llm

    def _fake_llm(doc):
        return mock_scenes

    mod._call_llm = _fake_llm
    try:
        scenes = generate_scene_script(_make_doc())
        assert isinstance(scenes, list)
        assert len(scenes) == 2
        assert scenes[0]["sceneType"] == "hook"
        assert "headline" in scenes[0]
        assert "narration" in scenes[0]
        assert "imagePrompt" in scenes[0]
    finally:
        mod._call_llm = _original


def test_scene_script_adds_ids():
    mock_scenes = [
        {"sceneType": "hook", "headline": "H", "body": "", "narration": "N", "imagePrompt": "P", "transition": "fade"},
    ]

    import fastpub.pipeline.scene_script as mod
    _original = mod._call_llm
    mod._call_llm = lambda doc: mock_scenes
    try:
        scenes = generate_scene_script(_make_doc())
        assert scenes[0]["id"] == "scene-1"
    finally:
        mod._call_llm = _original
