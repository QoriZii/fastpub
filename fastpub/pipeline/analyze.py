"""LLM analysis — two calls: one for web sections, one for slides."""
from __future__ import annotations

import typer

from fastpub import config
from fastpub.models import PaperDocument, PaperMeta, WebSection, PaperFigure, SlideSpec
from fastpub.pipeline.utils import call_llm, parse_llm_json
from fastpub.prompts import build_prompt

MAX_IMAGES = 20


def analyze_paper(
    pdf_text: str,
    images: list[str],
    audience: str = "academic",
) -> PaperDocument:
    """Run two LLM calls: web sections + slides. Merge into PaperDocument."""
    web_data = _analyze_web(pdf_text, audience)
    slides_data = _analyze_slides(pdf_text, images)

    # Build figures with injected image sources
    figures = [PaperFigure.from_dict(f) for f in slides_data.get("figures", [])]
    for i, fig in enumerate(figures):
        if i < len(images):
            fig.src = images[i]

    # Extract zh translations from both responses
    zh = _extract_zh(web_data, slides_data)

    return PaperDocument(
        meta=PaperMeta.from_dict(web_data.get("meta", {})),
        hook=web_data.get("hook", ""),
        web_sections=[WebSection.from_dict(s) for s in web_data.get("webSections", [])],
        figures=figures,
        slides=[SlideSpec.from_dict(s) for s in slides_data.get("slides", [])],
        zh=zh,
    )


def _extract_zh(web_data: dict, slides_data: dict) -> dict:
    """Extract Chinese translations from both analysis responses."""
    meta = web_data.get("meta", {})
    zh = {
        "meta": {
            "title": meta.get("title_zh", ""),
            "abstract": meta.get("abstract_zh", ""),
        },
        "hook": web_data.get("hook_zh", ""),
        "webSections": [],
        "figures": [
            {
                "id": f.get("id", ""),
                "caption": f.get("caption_zh", ""),
                "aiDescription": f.get("aiDescription_zh", ""),
            }
            for f in slides_data.get("figures", [])
        ],
    }
    for s in web_data.get("webSections", []):
        zh_section = {
            "type": s.get("type", ""),
            "summary": s.get("summary_zh", ""),
            "subIssues": [
                {
                    "title": si.get("title_zh", ""),
                    "description": si.get("description_zh", ""),
                }
                for si in s.get("subIssues", [])
            ],
        }
        zh["webSections"].append(zh_section)
    return zh


def _analyze_web(pdf_text: str, audience: str) -> dict:
    """Call 1: Extract web sections (meta, hook, 5 sections)."""
    prompt = build_prompt("paper_to_web", {
        "paperText": pdf_text,
        "audienceLevel": audience,
    })

    typer.echo(f"  [1/2] Analyzing for web with {config.FASTPUB_MODEL}…")
    raw = call_llm(
        system_prompt=prompt["system"],
        user_content=prompt["user"],
        max_tokens=8192,
    )
    return parse_llm_json(raw)


def _analyze_slides(pdf_text: str, images: list[str]) -> dict:
    """Call 2: Extract figures + slides (every number, visual story)."""
    prompt = build_prompt("paper_to_slides", {
        "paperText": pdf_text,
        "figureCount": str(len(images)),
        "hasFigures": bool(images),
        "noFigures": not images,
    })

    typer.echo(f"  [2/2] Analyzing for slides with {config.FASTPUB_MODEL}…")

    # Build user content with images if the provider supports vision
    if images and config.FASTPUB_PROVIDER == "xai":
        from xai_sdk.chat import image
        user_parts: list = [prompt["user"]]
        for img in images[:MAX_IMAGES]:
            user_parts.append(image(img))
        if len(images) > MAX_IMAGES:
            typer.echo(f"  Truncated figures from {len(images)} to {MAX_IMAGES}")
        user_content = user_parts
    else:
        if images:
            typer.echo(f"  (Skipping {len(images)} images — {config.FASTPUB_PROVIDER} provider is text-only)")
        user_content = prompt["user"]

    raw = call_llm(
        system_prompt=prompt["system"],
        user_content=user_content,
        max_tokens=32768,
    )
    return parse_llm_json(raw)
