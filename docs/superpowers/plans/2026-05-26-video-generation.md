# Video Generation Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add video generation to fastpub — transform a PaperDocument into a motion-graphics MP4 with AI-generated visuals and TTS narration.

**Architecture:** Two-stage pipeline. The slides stage (Python) generates a scene script via LLM, produces AI images, and outputs an HTML deck + `scenes.json`. The video stage (Python + Node.js) generates TTS audio, assembles a `manifest.json`, and shells out to Remotion to render MP4.

**Tech Stack:** Python 3.11+ (httpx, typer, xai-sdk), Node.js 18+ (Remotion, React, TypeScript), ffmpeg

**Spec:** `docs/superpowers/specs/2026-05-26-video-generation-design.md`

---

## File Map

### New Python files
- `fastpub/ai/image_providers/__init__.py` — provider factory `get_provider(name)`
- `fastpub/ai/image_providers/base.py` — `ImageProvider` ABC
- `fastpub/ai/image_providers/xai.py` — `XAIImageProvider` (grok-2-image)
- `fastpub/pipeline/scene_script.py` — `generate_scene_script(doc)` → list of scene dicts
- `fastpub/pipeline/image_gen.py` — `generate_images(scenes, provider, output_dir)` → image paths

### Modified Python files
- `fastpub/config.py` — add `IMAGE_PROVIDER` config
- `fastpub/render/slides.py` — integrate scene script + image gen
- `fastpub/render/video.py` — implement TTS + manifest + Remotion render
- `fastpub/cli/main.py` — add `--image-provider` flag
- `fastpub/prompts/scene_script/system.txt` — update prompt to include `imagePrompt` field

### New Node.js files (packages/remotion-video/)
- `package.json`, `tsconfig.json`, `remotion.config.ts`
- `src/index.ts` — registerRoot
- `src/types.ts` — manifest TypeScript types
- `src/Video.tsx` — root composition
- `src/Scene.tsx` — unified scene component
- `src/SceneWrapper.tsx` — transition handling
- `src/AudioTrack.tsx` — per-scene audio
- `src/animations/fade-in.ts`, `slide-in.ts`, `scale-reveal.ts`, `typewriter.ts`, `stagger.ts`

### Test files
- `tests/test_image_provider.py`
- `tests/test_scene_script.py`
- `tests/test_image_gen.py`
- `tests/test_video_manifest.py`

### Other
- `Makefile` — setup + build commands

---

## Task 1: Image Provider ABC + xAI adapter

**Files:**
- Create: `fastpub/ai/image_providers/base.py`
- Create: `fastpub/ai/image_providers/xai.py`
- Create: `fastpub/ai/image_providers/__init__.py`
- Create: `tests/test_image_provider.py`

- [ ] **Step 1: Write the failing test for provider factory**

```python
# tests/test_image_provider.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/qin/Apps/fastpub-py && python -m pytest tests/test_image_provider.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fastpub.ai.image_providers'`

- [ ] **Step 3: Create the ABC**

```python
# fastpub/ai/image_providers/base.py
"""Abstract base for image generation providers."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, width: int, height: int) -> bytes:
        """Generate an image from a text prompt. Returns PNG bytes."""
        ...
```

- [ ] **Step 4: Create the xAI adapter**

```python
# fastpub/ai/image_providers/xai.py
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
```

- [ ] **Step 5: Create the factory**

```python
# fastpub/ai/image_providers/__init__.py
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/qin/Apps/fastpub-py && python -m pytest tests/test_image_provider.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add fastpub/ai/image_providers/ tests/test_image_provider.py
git commit -m "feat: add ImageProvider ABC and xAI adapter"
```

---

## Task 2: Add IMAGE_PROVIDER config

**Files:**
- Modify: `fastpub/config.py:1-18`

- [ ] **Step 1: Update config.py**

Add after line 9 (`XAI_MODEL`):

```python
# Image generation
IMAGE_PROVIDER: str = os.environ.get("FASTPUB_IMAGE_PROVIDER", "xai")
```

- [ ] **Step 2: Verify import works**

Run: `cd /Users/qin/Apps/fastpub-py && python -c "from fastpub.config import IMAGE_PROVIDER; print(IMAGE_PROVIDER)"`
Expected: `xai`

- [ ] **Step 3: Commit**

```bash
git add fastpub/config.py
git commit -m "feat: add IMAGE_PROVIDER config"
```

---

## Task 3: Scene script generator

**Files:**
- Create: `fastpub/pipeline/scene_script.py`
- Modify: `fastpub/prompts/scene_script/system.txt`
- Create: `tests/test_scene_script.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scene_script.py
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
    """Test with a mock LLM response — we patch make_client."""
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/qin/Apps/fastpub-py && python -m pytest tests/test_scene_script.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Update scene script prompt to include imagePrompt**

Replace `fastpub/prompts/scene_script/system.txt` with:

```
You are a short-form video producer who creates engaging research explainer videos (up to 5 minutes).

Given a PaperDocument, produce a scene script as a JSON array. Each scene represents a single visual frame with text overlay and an AI-generated illustration.

## Video Flow

The number and types of scenes are NOT fixed. Decide based on the paper content. Use as many scenes as needed to explain the paper well. Common scene types:

- **hook** — bold opening statement or question that grabs attention
- **problem** — what challenge exists, why current solutions fall short
- **approach** — key method/insight, may use multiple scenes for complex methods
- **results** — show findings, use as many scenes as needed for different results
- **significance** — why it matters, broader implications
- **closing** — paper title + authors + venue

## Output Format

Return a JSON array of scene objects:

```json
[
  {
    "sceneType": "hook | problem | approach | results | significance | closing",
    "headline": "Short bold text displayed prominently (max 8 words)",
    "body": "Supporting text shown on slide (1-2 sentences, or empty)",
    "narration": "What the voiceover says (natural spoken style, 2-3 sentences)",
    "imagePrompt": "Detailed description of an illustration for this scene. Describe a visual that explains the paper concept — study design diagram, result plot, conceptual framework, data flow chart. NOT decorative art.",
    "transition": "fade | cut | slide"
  }
]
```

## Guidelines

- **Total duration:** up to 5 minutes, driven by narration length
- **Headlines:** Max 8 words, punchy and clear
- **Body:** Max 20 words, or empty for visual-only scenes
- **Narration:** Natural spoken style, 2-3 sentences per scene. This becomes the voiceover audio.
- **imagePrompt:** Describe a visual that illustrates the paper's content. For results scenes, describe a chart or plot. For method scenes, describe a diagram. For hook/significance, describe a conceptual illustration. Use empty string for closing scenes.
- **Transitions:** Use "fade" between major sections, "cut" within sections, "slide" for figure reveals
- Audience level: {{audienceLevel}}

Return ONLY the JSON array — no markdown fences, no explanation.
```

- [ ] **Step 4: Implement scene_script.py**

```python
# fastpub/pipeline/scene_script.py
"""Scene script generator — LLM produces scene array from PaperDocument."""
from __future__ import annotations

import json

from fastpub.models import PaperDocument
from fastpub.pipeline.utils import make_client, parse_llm_json
from fastpub.prompts import build_prompt
from fastpub import config


def generate_scene_script(doc: PaperDocument) -> list[dict]:
    """Generate a scene script from a PaperDocument. Returns list of scene dicts."""
    scenes = _call_llm(doc)
    # Add IDs
    for i, scene in enumerate(scenes):
        scene["id"] = f"scene-{i + 1}"
    return scenes


def _call_llm(doc: PaperDocument) -> list[dict]:
    """Call the LLM to generate scene script JSON."""
    from xai_sdk.chat import system, user

    sections_text = "\n".join(
        f"- [{s.type}] {s.title}: {s.summary}" for s in doc.sections
    )
    figures_text = "\n".join(
        f"- {f.id}: {f.caption} ({f.type})" for f in doc.figures
    ) or "No figures available."
    results_text = "; ".join(doc.narrative.results) if doc.narrative.results else ""

    prompt = build_prompt("scene_script", {
        "audienceLevel": doc.narrative.audience_level,
        "title": doc.meta.title,
        "authors": ", ".join(doc.meta.authors),
        "hook": doc.narrative.hook,
        "problem": doc.narrative.problem,
        "approach": doc.narrative.approach,
        "results": results_text,
        "significance": doc.narrative.significance,
        "sections": sections_text,
        "figures": figures_text,
    })

    client = make_client()
    chat = client.chat.create(
        model=config.XAI_MODEL,
        max_tokens=8192,
    )
    chat.append(system(prompt["system"]))
    chat.append(user(prompt["user"]))

    response = chat.sample()
    return parse_llm_json(response.content)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/qin/Apps/fastpub-py && python -m pytest tests/test_scene_script.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add fastpub/pipeline/scene_script.py fastpub/prompts/scene_script/system.txt tests/test_scene_script.py
git commit -m "feat: add scene script generator with imagePrompt support"
```

---

## Task 4: Parallel image generation

**Files:**
- Create: `fastpub/pipeline/image_gen.py`
- Create: `tests/test_image_gen.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_image_gen.py
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

    # scene-1 and scene-2 have prompts, scene-3 is empty
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/qin/Apps/fastpub-py && python -m pytest tests/test_image_gen.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement image_gen.py**

```python
# fastpub/pipeline/image_gen.py
"""Parallel image generation for scene scripts."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from fastpub.ai.image_providers.base import ImageProvider

STYLE_PREFIX = (
    "Clean, modern academic illustration style. Professional, warm color palette. "
    "Suitable for a research presentation video. "
)


def generate_images(
    scenes: list[dict],
    provider: ImageProvider,
    output_dir: Path,
    width: int = 1920,
    height: int = 1080,
) -> dict[str, str]:
    """Generate images for all scenes with non-empty imagePrompt.

    Returns dict mapping scene id -> output file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = [
        (scene["id"], scene["imagePrompt"])
        for scene in scenes
        if scene.get("imagePrompt", "").strip()
    ]

    result: dict[str, str] = {}

    def _gen(scene_id: str, prompt: str) -> tuple[str, str]:
        full_prompt = STYLE_PREFIX + prompt
        img_bytes = provider.generate(full_prompt, width, height)
        out_path = output_dir / f"{scene_id}.png"
        out_path.write_bytes(img_bytes)
        return scene_id, str(out_path)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_gen, sid, prompt): sid for sid, prompt in tasks}
        for future in as_completed(futures):
            scene_id, path = future.result()
            result[scene_id] = path

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/qin/Apps/fastpub-py && python -m pytest tests/test_image_gen.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add fastpub/pipeline/image_gen.py tests/test_image_gen.py
git commit -m "feat: add parallel image generation for scene scripts"
```

---

## Task 5: Extend slides renderer

**Files:**
- Modify: `fastpub/render/slides.py`
- Modify: `fastpub/cli/main.py:77-127` (render command)
- Modify: `fastpub/cli/main.py:132-198` (go command)

- [ ] **Step 1: Update render_slides signature and logic**

Replace the `render_slides` function in `fastpub/render/slides.py` (lines 21-34). The function now accepts an optional `image_provider` string, runs scene script generation + image generation, saves `scenes.json`, and builds HTML from that.

```python
def render_slides(
    doc: PaperDocument,
    output_path: Path,
    no_audio: bool = False,
    aspect: str = "4:3",
    image_provider: str | None = None,
) -> Path:
    """Render PaperDocument to an HTML slide deck.

    If image_provider is set, generates scene script via LLM and AI images.
    Otherwise falls back to deterministic slide building.
    Returns the output HTML path.
    Also saves scenes.json and images/ alongside the HTML for video stage reuse.
    """
    if aspect not in _ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect ratio: {aspect!r}. Use '4:3' or '16:9'.")

    if image_provider:
        from fastpub.pipeline.scene_script import generate_scene_script
        from fastpub.pipeline.image_gen import generate_images
        from fastpub.ai.image_providers import get_provider
        from fastpub import config

        import json
        import typer

        typer.echo("  Generating scene script...")
        scenes = generate_scene_script(doc)

        # Save scenes.json for video stage reuse
        base_name = output_path.stem.replace(".slides", "")
        assets_dir = output_path.parent / base_name
        scenes_path = output_path.parent / f"{base_name}.scenes.json"
        scenes_path.write_text(json.dumps(scenes, ensure_ascii=False, indent=2))

        typer.echo(f"  Generating images ({image_provider})...")
        provider = get_provider(image_provider, api_key=config.XAI_API_KEY)
        images_dir = assets_dir / "images"
        image_map = generate_images(scenes, provider, images_dir)

        # Convert scenes to _Slide objects for HTML generation
        slides = _slides_from_scenes(scenes, image_map)
    else:
        slides = _build_slides(doc)

    result = _build_html(doc, slides, aspect=aspect)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")
    return output_path
```

- [ ] **Step 2: Add _slides_from_scenes helper**

Add this function after `_build_slides` in slides.py:

```python
def _slides_from_scenes(scenes: list[dict], image_map: dict[str, str]) -> list[_Slide]:
    """Convert scene script dicts to _Slide objects for HTML rendering."""
    slides: list[_Slide] = []
    for scene in scenes:
        scene_type = scene.get("sceneType", "other")
        headline = scene.get("headline", "")
        body = scene.get("body", "")
        scene_id = scene.get("id", "")

        bullets = [body] if body else []
        figure_src = image_map.get(scene_id)

        slides.append(_Slide(
            slide_type=scene_type,
            title=headline,
            bullets=bullets,
            figure_src=figure_src,
        ))
    return slides
```

- [ ] **Step 3: Add scene type colors for new types**

Update `_TYPE_COLORS` dict in slides.py to include all scene types:

```python
_TYPE_COLORS = {
    "title": "#1E3A5F",
    "hook": "#7C3AED",
    "problem": "#DC2626",
    "method": "#2563EB",
    "approach": "#2563EB",
    "results": "#059669",
    "significance": "#D97706",
    "closing": "#1E3A5F",
    "takeaway": "#1E3A5F",
}
```

- [ ] **Step 4: Add --image-provider to render command in CLI**

In `fastpub/cli/main.py`, add the parameter to the `render` function signature (after `no_audio`):

```python
@app.command()
def render(
    analysis: Path = typer.Argument(..., help="Path to analysis.json"),
    format: str = typer.Option("web", "-f", "--format", help="Comma-separated: web, slides, video"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output path"),
    aspect: str = typer.Option("4:3", "--aspect", help="Slide aspect ratio: 4:3 | 16:9"),
    voice: Optional[str] = typer.Option(None, "--voice", help="TTS voice: eve, ara, rex, sal, leo"),
    no_audio: bool = typer.Option(False, "--no-audio", help="Skip audio generation"),
    image_provider: Optional[str] = typer.Option(None, "--image-provider", help="Image generation provider: xai"),
):
```

And update the slides case to pass it through:

```python
            case "slides":
                from fastpub.render.slides import render_slides

                out_path = output or out_dir / f"{base_name}.slides.html"
                result = render_slides(doc, out_path, no_audio=no_audio, aspect=aspect, image_provider=image_provider)
                typer.echo(f"  Slides: {result}")
```

- [ ] **Step 5: Add --image-provider to go command in CLI**

Add the same parameter to the `go` function and pass it to the slides render case. Same pattern as Step 4.

- [ ] **Step 6: Verify the module imports work**

Run: `cd /Users/qin/Apps/fastpub-py && python -c "from fastpub.render.slides import render_slides; print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add fastpub/render/slides.py fastpub/cli/main.py
git commit -m "feat: integrate scene script + image gen into slides renderer"
```

---

## Task 6: Video renderer (Python side)

**Files:**
- Modify: `fastpub/render/video.py`
- Create: `tests/test_video_manifest.py`

- [ ] **Step 1: Write the failing test for manifest building**

```python
# tests/test_video_manifest.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/qin/Apps/fastpub-py && python -m pytest tests/test_video_manifest.py -v`
Expected: FAIL — `ImportError: cannot import name 'build_manifest'`

- [ ] **Step 3: Implement video.py**

```python
# fastpub/render/video.py
"""Video renderer — produces an MP4 video from a PaperDocument."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer

from fastpub import config
from fastpub.models import PaperDocument, PaperMeta


_SCENE_TYPE_COLORS = {
    "hook": "#c8aa78",
    "problem": "#a0635a",
    "approach": "#5b8fa8",
    "results": "#c8aa78",
    "significance": "#c8aa78",
    "closing": "#c8aa78",
}


def render_video(
    doc: PaperDocument,
    output_path: Path,
    no_audio: bool = False,
    image_provider: str | None = None,
    voice: str = "sal",
) -> Path:
    """Render PaperDocument to MP4 video via Remotion."""
    base_name = output_path.stem
    out_dir = output_path.parent
    assets_dir = out_dir / base_name

    # Step 1: Run slides stage to get scenes + images (if not already done)
    scenes_path = out_dir / f"{base_name}.scenes.json"
    if not scenes_path.exists():
        from fastpub.render.slides import render_slides
        slides_path = out_dir / f"{base_name}.slides.html"
        render_slides(doc, slides_path, image_provider=image_provider or config.IMAGE_PROVIDER)

    scenes = json.loads(scenes_path.read_text(encoding="utf-8"))

    # Step 2: Collect existing images
    images_dir = assets_dir / "images"
    image_map: dict[str, str] = {}
    if images_dir.exists():
        for scene in scenes:
            img_path = images_dir / f"{scene['id']}.png"
            if img_path.exists():
                image_map[scene["id"]] = str(img_path)

    # Step 3: Generate TTS audio
    audio_map: dict[str, dict] = {}
    if not no_audio:
        typer.echo("  Generating TTS audio...")
        audio_map = _generate_all_tts(scenes, assets_dir / "audio", voice=voice)

    # Step 4: Build manifest
    manifest = build_manifest(doc.meta, scenes, audio_map, image_map)
    manifest_path = assets_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    typer.echo(f"  Manifest: {manifest_path}")

    # Step 5: Render with Remotion
    typer.echo("  Rendering video with Remotion...")
    remotion_dir = Path(__file__).parent.parent.parent / "packages" / "remotion-video"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "npx", "remotion", "render",
            "src/index.ts",
            "Video",
            str(output_path.resolve()),
            "--props", str(manifest_path.resolve()),
        ],
        cwd=str(remotion_dir),
        check=True,
    )
    typer.echo(f"  Video: {output_path}")
    return output_path


def build_manifest(
    meta: PaperMeta,
    scenes: list[dict],
    audio_map: dict[str, dict],
    image_map: dict[str, str],
) -> dict:
    """Assemble the Remotion manifest from scenes, audio, and images."""
    manifest_scenes = []
    for scene in scenes:
        sid = scene["id"]
        audio_info = audio_map.get(sid, {})
        manifest_scenes.append({
            "id": sid,
            "type": scene.get("sceneType", "other"),
            "durationSec": audio_info.get("duration", 5.0),
            "headline": scene.get("headline", ""),
            "body": scene.get("body", ""),
            "narration": scene.get("narration", ""),
            "audioFile": audio_info.get("path"),
            "imageFile": image_map.get(sid),
            "imagePrompt": scene.get("imagePrompt", ""),
            "transition": scene.get("transition", "fade"),
            "colorAccent": _SCENE_TYPE_COLORS.get(scene.get("sceneType", ""), "#c8aa78"),
        })

    return {
        "meta": {
            "title": meta.title,
            "authors": meta.authors,
            "venue": meta.venue,
            "year": meta.year,
        },
        "settings": {
            "fps": 30,
            "width": 1920,
            "height": 1080,
        },
        "scenes": manifest_scenes,
    }


def _generate_all_tts(
    scenes: list[dict],
    audio_dir: Path,
    voice: str = "sal",
) -> dict[str, dict]:
    """Generate TTS audio for all scenes. Returns {scene_id: {path, duration}}."""
    from fastpub.ai.tts import generate_speech, get_audio_duration

    audio_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, dict] = {}

    for scene in scenes:
        narration = scene.get("narration", "").strip()
        if not narration:
            continue
        sid = scene["id"]
        out_path = str(audio_dir / f"{sid}.mp3")
        generate_speech(
            text=narration,
            output_path=out_path,
            api_key=config.XAI_API_KEY,
            voice=voice,
        )
        duration = get_audio_duration(out_path)
        result[sid] = {"path": out_path, "duration": duration}

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/qin/Apps/fastpub-py && python -m pytest tests/test_video_manifest.py -v`
Expected: 2 passed

- [ ] **Step 5: Update CLI to pass image_provider to render_video**

In `fastpub/cli/main.py`, update the video case in `render` command:

```python
            case "video":
                from fastpub.render.video import render_video

                out_path = output or out_dir / f"{base_name}.mp4"
                result = render_video(doc, out_path, no_audio=no_audio, image_provider=image_provider, voice=voice or "sal")
                typer.echo(f"  Video: {result}")
```

And in the `go` command similarly.

- [ ] **Step 6: Commit**

```bash
git add fastpub/render/video.py fastpub/cli/main.py tests/test_video_manifest.py
git commit -m "feat: implement video renderer with TTS + manifest + Remotion shell-out"
```

---

## Task 7: Remotion project scaffold

**Files:**
- Create: `packages/remotion-video/package.json`
- Create: `packages/remotion-video/tsconfig.json`
- Create: `packages/remotion-video/remotion.config.ts`
- Create: `packages/remotion-video/src/types.ts`
- Create: `packages/remotion-video/src/index.ts`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "@fastpub/remotion-video",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "preview": "remotion preview src/index.ts",
    "render": "remotion render src/index.ts Video"
  },
  "dependencies": {
    "@remotion/cli": "^4",
    "@remotion/player": "^4",
    "react": "^18",
    "react-dom": "^18",
    "remotion": "^4"
  },
  "devDependencies": {
    "@types/react": "^18",
    "typescript": "^5"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist"
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create remotion.config.ts**

```typescript
// packages/remotion-video/remotion.config.ts
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
```

- [ ] **Step 4: Create types.ts**

```typescript
// packages/remotion-video/src/types.ts
export interface ManifestMeta {
  title: string;
  authors: string[];
  venue: string;
  year: number | null;
}

export interface ManifestSettings {
  fps: number;
  width: number;
  height: number;
}

export interface ManifestScene {
  id: string;
  type: "hook" | "problem" | "approach" | "results" | "significance" | "closing";
  durationSec: number;

  // Visual text (displayed on slide)
  headline: string;
  body: string;

  // Audio (TTS narration, not displayed)
  narration: string;
  audioFile: string | null;

  // Image (AI-generated, displayed on slide)
  imageFile: string | null;
  imagePrompt: string;

  transition: "fade" | "cut" | "slide";
  colorAccent: string;
}

export interface VideoManifest {
  meta: ManifestMeta;
  settings: ManifestSettings;
  scenes: ManifestScene[];
}
```

- [ ] **Step 5: Create index.ts**

```typescript
// packages/remotion-video/src/index.ts
import { registerRoot } from "remotion";
import { Video } from "./Video";

registerRoot(Video);
```

- [ ] **Step 6: Create minimal Video.tsx placeholder**

```tsx
// packages/remotion-video/src/Video.tsx
import { Composition, staticFile } from "remotion";
import type { VideoManifest } from "./types";

export const Video: React.FC = () => {
  return (
    <Composition
      id="Video"
      component={VideoComposition}
      durationInFrames={150}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};

const VideoComposition: React.FC = () => {
  return (
    <div style={{ flex: 1, background: "#1a2332", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <h1 style={{ color: "#f0ebe3", fontFamily: "Georgia, serif" }}>FastPub Video</h1>
    </div>
  );
};
```

- [ ] **Step 7: Install dependencies**

Run: `cd /Users/qin/Apps/fastpub-py/packages/remotion-video && npm install`
Expected: `node_modules/` created, no errors.

- [ ] **Step 8: Verify Remotion preview works**

Run: `cd /Users/qin/Apps/fastpub-py/packages/remotion-video && npx remotion preview src/index.ts`
Expected: Browser opens with preview showing "FastPub Video" text.

- [ ] **Step 9: Commit**

```bash
git add packages/remotion-video/
echo "packages/remotion-video/node_modules/" >> .gitignore
git add .gitignore
git commit -m "feat: scaffold Remotion project with types and minimal composition"
```

---

## Task 8: Remotion Scene component + layouts

**Files:**
- Create: `packages/remotion-video/src/Scene.tsx`
- Modify: `packages/remotion-video/src/Video.tsx`

- [ ] **Step 1: Create Scene.tsx**

```tsx
// packages/remotion-video/src/Scene.tsx
import React from "react";
import type { ManifestScene } from "./types";

interface SceneProps {
  scene: ManifestScene;
}

export const Scene: React.FC<SceneProps> = ({ scene }) => {
  const isDark = scene.type === "hook" || scene.type === "closing";
  const hasImage = !!scene.imageFile;

  if (isDark) return <DarkScene scene={scene} />;
  if (hasImage) return <SplitScene scene={scene} />;
  return <CenteredScene scene={scene} />;
};

const DarkScene: React.FC<SceneProps> = ({ scene }) => (
  <div
    style={{
      width: "100%",
      height: "100%",
      background: "linear-gradient(135deg, #1a2332 0%, #2a3f5f 100%)",
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      padding: "80px 120px",
      position: "relative",
      overflow: "hidden",
    }}
  >
    {/* Decorative circles */}
    <div style={{ position: "absolute", top: -40, right: -40, width: 300, height: 300, border: "2px solid rgba(200,170,120,0.1)", borderRadius: "50%" }} />
    <div style={{ position: "absolute", top: 20, right: 20, width: 200, height: 200, border: "2px solid rgba(200,170,120,0.06)", borderRadius: "50%" }} />

    {/* Brand */}
    <div style={{ position: "absolute", top: 40, left: 60, fontFamily: "-apple-system, sans-serif", fontSize: 14, fontWeight: 700, color: "#c8aa78", letterSpacing: "0.2em", textTransform: "uppercase" as const }}>
      fastpub
    </div>

    {/* Headline */}
    <h1 style={{
      fontFamily: "Georgia, serif",
      fontSize: scene.type === "hook" ? 72 : 52,
      fontWeight: 700,
      fontStyle: scene.type === "hook" ? "italic" : "normal",
      color: "#f0ebe3",
      lineHeight: 1.3,
      maxWidth: "75%",
    }}>
      {scene.headline}
    </h1>

    {/* Divider */}
    <div style={{ width: 60, height: 3, background: "linear-gradient(90deg, #c8aa78, transparent)", marginTop: 40, borderRadius: 2 }} />

    {/* Body */}
    {scene.body && (
      <p style={{ fontFamily: "-apple-system, sans-serif", fontSize: 28, color: "#8a9ab0", marginTop: 24, lineHeight: 1.6, maxWidth: "65%" }}>
        {scene.body}
      </p>
    )}

    {/* Closing extras */}
    {scene.type === "closing" && (
      <div style={{ position: "absolute", bottom: 60, left: 0, right: 0, textAlign: "center" }}>
        <div style={{ fontFamily: "Georgia, serif", fontSize: 12, color: "#556a78", letterSpacing: "0.1em", textTransform: "uppercase" as const }}>fastpub</div>
      </div>
    )}
  </div>
);

const SplitScene: React.FC<SceneProps> = ({ scene }) => (
  <div style={{ width: "100%", height: "100%", background: "#faf8f5", display: "flex", padding: "60px 80px", gap: 60, position: "relative" }}>
    {/* Top accent bar */}
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 4, background: `linear-gradient(90deg, ${scene.colorAccent} 0%, transparent 100%)` }} />

    {/* Text side */}
    <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
      <div style={{ fontFamily: "-apple-system, sans-serif", fontSize: 14, color: scene.colorAccent, fontWeight: 700, letterSpacing: "0.15em", textTransform: "uppercase" as const, marginBottom: 16 }}>
        {scene.type}
      </div>
      <h2 style={{ fontFamily: "Georgia, serif", fontSize: 48, fontWeight: 700, color: "#1a2332", lineHeight: 1.3, marginBottom: 32 }}>
        {scene.headline}
      </h2>
      {scene.body && (
        <div style={{ fontSize: 22, color: "#4a5568", lineHeight: 1.7, fontFamily: "-apple-system, sans-serif", paddingLeft: 16, borderLeft: `3px solid ${scene.colorAccent}` }}>
          {scene.body}
        </div>
      )}
    </div>

    {/* Image side */}
    <div style={{ flex: 0.85, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <img
        src={scene.imageFile!}
        style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain", background: "#fff", border: "1px solid #e0ddd8", borderRadius: 6, boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}
      />
    </div>

    {/* Brand */}
    <div style={{ position: "absolute", bottom: 24, left: 80, fontFamily: "Georgia, serif", fontSize: 12, color: "#bbb", letterSpacing: "0.1em", textTransform: "uppercase" as const }}>fastpub</div>
  </div>
);

const CenteredScene: React.FC<SceneProps> = ({ scene }) => (
  <div style={{ width: "100%", height: "100%", background: "#faf8f5", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", padding: "80px 120px", position: "relative" }}>
    {/* Top accent bar */}
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 4, background: `linear-gradient(90deg, ${scene.colorAccent} 0%, transparent 100%)` }} />

    <div style={{ fontFamily: "-apple-system, sans-serif", fontSize: 14, color: scene.colorAccent, fontWeight: 700, letterSpacing: "0.15em", textTransform: "uppercase" as const, marginBottom: 16 }}>
      {scene.type}
    </div>
    <h2 style={{ fontFamily: "Georgia, serif", fontSize: 56, fontWeight: 700, color: "#1a2332", lineHeight: 1.3, maxWidth: "80%", marginBottom: 32 }}>
      {scene.headline}
    </h2>
    {scene.body && (
      <p style={{ fontSize: 26, color: "#4a5568", lineHeight: 1.7, fontFamily: "-apple-system, sans-serif", maxWidth: "65%" }}>
        {scene.body}
      </p>
    )}

    <div style={{ position: "absolute", bottom: 24, fontFamily: "Georgia, serif", fontSize: 12, color: "#bbb", letterSpacing: "0.1em", textTransform: "uppercase" as const }}>fastpub</div>
  </div>
);
```

- [ ] **Step 2: Update Video.tsx to read manifest and render scenes**

```tsx
// packages/remotion-video/src/Video.tsx
import React from "react";
import { Composition, AbsoluteFill, Series, Audio, useCurrentFrame, staticFile } from "remotion";
import type { VideoManifest, ManifestScene } from "./types";
import { Scene } from "./Scene";

const VideoComposition: React.FC<{ manifest: VideoManifest }> = ({ manifest }) => {
  const { settings, scenes } = manifest;

  return (
    <AbsoluteFill>
      <Series>
        {scenes.map((scene) => {
          const durationInFrames = Math.round(scene.durationSec * settings.fps);
          return (
            <Series.Sequence key={scene.id} durationInFrames={durationInFrames}>
              <Scene scene={scene} />
              {scene.audioFile && <Audio src={scene.audioFile} />}
            </Series.Sequence>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};

export const Video: React.FC = () => {
  // Default manifest for preview
  const defaultManifest: VideoManifest = {
    meta: { title: "Preview", authors: [], venue: "", year: null },
    settings: { fps: 30, width: 1920, height: 1080 },
    scenes: [
      {
        id: "preview-1",
        type: "hook",
        durationSec: 5,
        headline: "Preview Scene",
        body: "This is a preview of the FastPub video renderer.",
        narration: "",
        audioFile: null,
        imageFile: null,
        imagePrompt: "",
        transition: "fade",
        colorAccent: "#c8aa78",
      },
    ],
  };

  const totalFrames = defaultManifest.scenes.reduce(
    (sum, s) => sum + Math.round(s.durationSec * defaultManifest.settings.fps),
    0
  );

  return (
    <Composition
      id="Video"
      component={VideoComposition}
      durationInFrames={totalFrames}
      fps={defaultManifest.settings.fps}
      width={defaultManifest.settings.width}
      height={defaultManifest.settings.height}
      defaultProps={{ manifest: defaultManifest }}
    />
  );
};
```

- [ ] **Step 3: Verify preview renders with scene layouts**

Run: `cd /Users/qin/Apps/fastpub-py/packages/remotion-video && npx remotion preview src/index.ts`
Expected: Preview shows hook scene with dark gradient, italic headline, gold accents.

- [ ] **Step 4: Commit**

```bash
git add packages/remotion-video/src/Scene.tsx packages/remotion-video/src/Video.tsx
git commit -m "feat: add Scene component with dark, split, and centered layouts"
```

---

## Task 9: Animation primitives

**Files:**
- Create: `packages/remotion-video/src/animations/fade-in.ts`
- Create: `packages/remotion-video/src/animations/slide-in.ts`
- Create: `packages/remotion-video/src/animations/scale-reveal.ts`
- Create: `packages/remotion-video/src/animations/stagger.ts`
- Create: `packages/remotion-video/src/animations/typewriter.ts`
- Create: `packages/remotion-video/src/animations/index.ts`

- [ ] **Step 1: Create fade-in animation**

```typescript
// packages/remotion-video/src/animations/fade-in.ts
import { interpolate, useCurrentFrame } from "remotion";

export function useFadeIn(delay: number = 0, duration: number = 15, offsetY: number = 40) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [delay, delay + duration], [0, 1], { extrapolateRight: "clamp" });
  const translateY = interpolate(frame, [delay, delay + duration], [offsetY, 0], { extrapolateRight: "clamp" });
  return { opacity, transform: `translateY(${translateY}px)` };
}
```

- [ ] **Step 2: Create slide-in animation**

```typescript
// packages/remotion-video/src/animations/slide-in.ts
import { interpolate, useCurrentFrame } from "remotion";

export function useSlideIn(delay: number = 0, duration: number = 12, fromX: number = 100) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [delay, delay + duration], [0, 1], { extrapolateRight: "clamp" });
  const translateX = interpolate(frame, [delay, delay + duration], [fromX, 0], { extrapolateRight: "clamp" });
  return { opacity, transform: `translateX(${translateX}px)` };
}
```

- [ ] **Step 3: Create scale-reveal animation**

```typescript
// packages/remotion-video/src/animations/scale-reveal.ts
import { interpolate, useCurrentFrame } from "remotion";

export function useScaleReveal(delay: number = 0, duration: number = 15) {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [delay, delay + duration], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(frame, [delay, delay + duration], [0.95, 1], { extrapolateRight: "clamp" });
  return { opacity, transform: `scale(${scale})` };
}
```

- [ ] **Step 4: Create stagger animation**

```typescript
// packages/remotion-video/src/animations/stagger.ts
import { interpolate, useCurrentFrame } from "remotion";

export function useStagger(index: number, delayPerItem: number = 5, duration: number = 12, offsetX: number = 20) {
  const frame = useCurrentFrame();
  const delay = index * delayPerItem;
  const opacity = interpolate(frame, [delay, delay + duration], [0, 1], { extrapolateRight: "clamp" });
  const translateX = interpolate(frame, [delay, delay + duration], [-offsetX, 0], { extrapolateRight: "clamp" });
  return { opacity, transform: `translateX(${translateX}px)` };
}
```

- [ ] **Step 5: Create typewriter animation**

```typescript
// packages/remotion-video/src/animations/typewriter.ts
import { useCurrentFrame } from "remotion";

export function useTypewriter(text: string, charsPerFrame: number = 0.8, delay: number = 0) {
  const frame = useCurrentFrame();
  const elapsed = Math.max(0, frame - delay);
  const visibleChars = Math.min(Math.floor(elapsed * charsPerFrame), text.length);
  return text.slice(0, visibleChars);
}
```

- [ ] **Step 6: Create barrel export**

```typescript
// packages/remotion-video/src/animations/index.ts
export { useFadeIn } from "./fade-in";
export { useSlideIn } from "./slide-in";
export { useScaleReveal } from "./scale-reveal";
export { useStagger } from "./stagger";
export { useTypewriter } from "./typewriter";
```

- [ ] **Step 7: Commit**

```bash
git add packages/remotion-video/src/animations/
git commit -m "feat: add animation primitives (fadeIn, slideIn, scaleReveal, stagger, typewriter)"
```

---

## Task 10: Wire animations into Scene component

**Files:**
- Modify: `packages/remotion-video/src/Scene.tsx`

- [ ] **Step 1: Update Scene.tsx to use animations**

Update the three sub-components in Scene.tsx to use the animation hooks. For `DarkScene`, use `useTypewriter` for the headline and `useFadeIn` for body. For `SplitScene`, use `useFadeIn` for text and `useSlideIn` for image. For `CenteredScene`, use `useFadeIn` for headline and body.

Key changes to `DarkScene`:

```tsx
import { useFadeIn, useSlideIn, useScaleReveal, useStagger, useTypewriter } from "./animations";

const DarkScene: React.FC<SceneProps> = ({ scene }) => {
  const typedHeadline = useTypewriter(scene.headline, 0.8, 10);
  const bodyStyle = useFadeIn(30, 15);
  const dividerStyle = useFadeIn(5, 10);

  return (
    <div style={{ /* ... same container styles ... */ }}>
      {/* ... decorative circles, brand ... */}
      <h1 style={{ /* ... same text styles ... */ }}>
        {typedHeadline}
        <span style={{ opacity: 0.3 }}>|</span>
      </h1>
      <div style={{ ...dividerStyle, width: 60, height: 3, background: "linear-gradient(90deg, #c8aa78, transparent)", borderRadius: 2 }} />
      {scene.body && (
        <p style={{ ...bodyStyle, /* ... same text styles ... */ }}>
          {scene.body}
        </p>
      )}
    </div>
  );
};
```

Key changes to `SplitScene` — use `useFadeIn` for label/headline (delay 5), `useStagger` for body items, `useScaleReveal` for image (delay 15):

```tsx
const SplitScene: React.FC<SceneProps> = ({ scene }) => {
  const labelStyle = useFadeIn(5, 10);
  const headlineStyle = useFadeIn(8, 15);
  const bodyStyle = useFadeIn(15, 15);
  const imageStyle = useScaleReveal(12, 18);

  return (
    <div style={{ /* ... container ... */ }}>
      <div style={{ /* ... text side ... */ }}>
        <div style={{ ...labelStyle, /* ... label styles ... */ }}>{scene.type}</div>
        <h2 style={{ ...headlineStyle, /* ... headline styles ... */ }}>{scene.headline}</h2>
        {scene.body && <div style={{ ...bodyStyle, /* ... body styles ... */ }}>{scene.body}</div>}
      </div>
      <div style={{ /* ... image side ... */ }}>
        <img src={scene.imageFile!} style={{ ...imageStyle, /* ... img styles ... */ }} />
      </div>
    </div>
  );
};
```

Key changes to `CenteredScene` — use `useFadeIn` for label (delay 5), headline (delay 8), body (delay 15):

```tsx
const CenteredScene: React.FC<SceneProps> = ({ scene }) => {
  const labelStyle = useFadeIn(5, 10);
  const headlineStyle = useFadeIn(8, 15);
  const bodyStyle = useFadeIn(15, 15);

  return (
    <div style={{ /* ... container ... */ }}>
      <div style={{ ...labelStyle, /* ... label ... */ }}>{scene.type}</div>
      <h2 style={{ ...headlineStyle, /* ... headline ... */ }}>{scene.headline}</h2>
      {scene.body && <p style={{ ...bodyStyle, /* ... body ... */ }}>{scene.body}</p>}
    </div>
  );
};
```

- [ ] **Step 2: Verify animations in preview**

Run: `cd /Users/qin/Apps/fastpub-py/packages/remotion-video && npx remotion preview src/index.ts`
Expected: Preview shows typewriter effect on hook headline, fade-in on body text.

- [ ] **Step 3: Commit**

```bash
git add packages/remotion-video/src/Scene.tsx
git commit -m "feat: wire animations into scene components"
```

---

## Task 11: SceneWrapper transitions + AudioTrack

**Files:**
- Create: `packages/remotion-video/src/SceneWrapper.tsx`
- Create: `packages/remotion-video/src/AudioTrack.tsx`
- Modify: `packages/remotion-video/src/Video.tsx`

- [ ] **Step 1: Create SceneWrapper with crossfade**

```tsx
// packages/remotion-video/src/SceneWrapper.tsx
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

interface SceneWrapperProps {
  children: React.ReactNode;
  durationInFrames: number;
  transition: "fade" | "cut" | "slide";
}

const FADE_FRAMES = 15; // 500ms at 30fps

export const SceneWrapper: React.FC<SceneWrapperProps> = ({ children, durationInFrames, transition }) => {
  const frame = useCurrentFrame();

  let opacity = 1;
  if (transition === "fade") {
    const fadeIn = interpolate(frame, [0, FADE_FRAMES], [0, 1], { extrapolateRight: "clamp" });
    const fadeOut = interpolate(frame, [durationInFrames - FADE_FRAMES, durationInFrames], [1, 0], { extrapolateRight: "clamp" });
    opacity = Math.min(fadeIn, fadeOut);
  }

  return (
    <AbsoluteFill style={{ opacity }}>
      {children}
    </AbsoluteFill>
  );
};
```

- [ ] **Step 2: Create AudioTrack**

```tsx
// packages/remotion-video/src/AudioTrack.tsx
import React from "react";
import { Audio, Sequence } from "remotion";
import type { ManifestScene } from "./types";

interface AudioTrackProps {
  scenes: ManifestScene[];
  fps: number;
}

export const AudioTrack: React.FC<AudioTrackProps> = ({ scenes, fps }) => {
  let frameOffset = 0;

  return (
    <>
      {scenes.map((scene) => {
        const durationInFrames = Math.round(scene.durationSec * fps);
        const from = frameOffset;
        frameOffset += durationInFrames;

        if (!scene.audioFile) return null;

        return (
          <Sequence key={scene.id} from={from} durationInFrames={durationInFrames}>
            <Audio src={scene.audioFile} />
          </Sequence>
        );
      })}
    </>
  );
};
```

- [ ] **Step 3: Update Video.tsx to use SceneWrapper and AudioTrack**

```tsx
// packages/remotion-video/src/Video.tsx
import React from "react";
import { Composition, AbsoluteFill, Series } from "remotion";
import type { VideoManifest } from "./types";
import { Scene } from "./Scene";
import { SceneWrapper } from "./SceneWrapper";
import { AudioTrack } from "./AudioTrack";

const VideoComposition: React.FC<{ manifest: VideoManifest }> = ({ manifest }) => {
  const { settings, scenes } = manifest;

  return (
    <AbsoluteFill>
      <Series>
        {scenes.map((scene) => {
          const durationInFrames = Math.round(scene.durationSec * settings.fps);
          return (
            <Series.Sequence key={scene.id} durationInFrames={durationInFrames}>
              <SceneWrapper durationInFrames={durationInFrames} transition={scene.transition}>
                <Scene scene={scene} />
              </SceneWrapper>
            </Series.Sequence>
          );
        })}
      </Series>
      <AudioTrack scenes={scenes} fps={settings.fps} />
    </AbsoluteFill>
  );
};

export const Video: React.FC = () => {
  const defaultManifest: VideoManifest = {
    meta: { title: "Preview", authors: [], venue: "", year: null },
    settings: { fps: 30, width: 1920, height: 1080 },
    scenes: [
      { id: "p1", type: "hook", durationSec: 5, headline: "Preview Hook Scene", body: "This is a preview.", narration: "", audioFile: null, imageFile: null, imagePrompt: "", transition: "fade", colorAccent: "#c8aa78" },
      { id: "p2", type: "approach", durationSec: 5, headline: "Preview Method", body: "Method details here.", narration: "", audioFile: null, imageFile: null, imagePrompt: "", transition: "fade", colorAccent: "#5b8fa8" },
    ],
  };

  const totalFrames = defaultManifest.scenes.reduce(
    (sum, s) => sum + Math.round(s.durationSec * defaultManifest.settings.fps), 0
  );

  return (
    <Composition
      id="Video"
      component={VideoComposition}
      durationInFrames={totalFrames}
      fps={defaultManifest.settings.fps}
      width={defaultManifest.settings.width}
      height={defaultManifest.settings.height}
      defaultProps={{ manifest: defaultManifest }}
    />
  );
};
```

- [ ] **Step 4: Verify transitions in preview**

Run: `cd /Users/qin/Apps/fastpub-py/packages/remotion-video && npx remotion preview src/index.ts`
Expected: Two scenes with fade transitions between them.

- [ ] **Step 5: Commit**

```bash
git add packages/remotion-video/src/SceneWrapper.tsx packages/remotion-video/src/AudioTrack.tsx packages/remotion-video/src/Video.tsx
git commit -m "feat: add SceneWrapper transitions and AudioTrack"
```

---

## Task 12: Makefile + end-to-end wiring

**Files:**
- Create: `Makefile`
- Modify: `.gitignore`

- [ ] **Step 1: Create Makefile**

```makefile
# Makefile

.PHONY: setup setup-python setup-node render-video clean

setup: setup-python setup-node

setup-python:
	pip install -e .

setup-node:
	cd packages/remotion-video && npm install

render-video:
	@echo "Usage: fastpub render <analysis.json> -f video --image-provider xai"

clean:
	rm -rf packages/remotion-video/node_modules
```

- [ ] **Step 2: Update .gitignore**

Append these lines to `.gitignore`:

```
packages/remotion-video/node_modules/
packages/remotion-video/dist/
.superpowers/
```

- [ ] **Step 3: Run all Python tests**

Run: `cd /Users/qin/Apps/fastpub-py && python -m pytest tests/ -v`
Expected: All tests pass (test_image_provider, test_scene_script, test_image_gen, test_video_manifest).

- [ ] **Step 4: Commit**

```bash
git add Makefile .gitignore
git commit -m "feat: add Makefile and gitignore for video pipeline"
```

---

## Summary

| Task | What it builds | Key files |
|------|---------------|-----------|
| 1 | Image provider ABC + xAI adapter | `fastpub/ai/image_providers/` |
| 2 | IMAGE_PROVIDER config | `fastpub/config.py` |
| 3 | Scene script generator | `fastpub/pipeline/scene_script.py` |
| 4 | Parallel image generation | `fastpub/pipeline/image_gen.py` |
| 5 | Extended slides renderer + CLI | `fastpub/render/slides.py`, `cli/main.py` |
| 6 | Video renderer (Python) | `fastpub/render/video.py` |
| 7 | Remotion project scaffold | `packages/remotion-video/` |
| 8 | Scene component + layouts | `Scene.tsx` |
| 9 | Animation primitives | `animations/*.ts` |
| 10 | Wire animations into scenes | `Scene.tsx` |
| 11 | Transitions + audio | `SceneWrapper.tsx`, `AudioTrack.tsx` |
| 12 | Makefile + integration | `Makefile` |
