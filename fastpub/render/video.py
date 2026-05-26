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
