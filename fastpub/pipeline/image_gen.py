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
