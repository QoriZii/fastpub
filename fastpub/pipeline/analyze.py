"""LLM analysis — two calls: one for web sections, one for slides."""
from __future__ import annotations

import typer

from fastpub import config
from fastpub.models import PaperDocument, PaperMeta, WebSection, SubIssue, PaperFigure, SlideSpec, VisualizationData
from fastpub.pipeline.utils import make_client, parse_llm_json
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

    return PaperDocument(
        meta=PaperMeta.from_dict(web_data.get("meta", {})),
        hook=web_data.get("hook", ""),
        web_sections=[WebSection.from_dict(s) for s in web_data.get("webSections", [])],
        figures=figures,
        slides=[SlideSpec.from_dict(s) for s in slides_data.get("slides", [])],
    )


def _analyze_web(pdf_text: str, audience: str) -> dict:
    """Call 1: Extract web sections (meta, hook, 5 sections)."""
    from xai_sdk.chat import system, user

    prompt = build_prompt("paper_to_web", {
        "paperText": pdf_text,
        "audienceLevel": audience,
    })

    client = make_client()
    typer.echo(f"  [1/2] Analyzing for web with {config.XAI_MODEL}…")

    chat = client.chat.create(
        model=config.XAI_MODEL,
        max_tokens=8192,
        response_format="json_object",
    )
    chat.append(system(prompt["system"]))
    chat.append(user(prompt["user"]))

    response = chat.sample()
    return parse_llm_json(response.content)


def _analyze_slides(pdf_text: str, images: list[str]) -> dict:
    """Call 2: Extract figures + slides (every number, visual story)."""
    from xai_sdk.chat import image, system, user

    prompt = build_prompt("paper_to_slides", {
        "paperText": pdf_text,
        "figureCount": str(len(images)),
        "hasFigures": bool(images),
        "noFigures": not images,
    })

    client = make_client()
    typer.echo(f"  [2/2] Analyzing for slides with {config.XAI_MODEL}…")

    chat = client.chat.create(
        model=config.XAI_MODEL,
        max_tokens=32768,
        response_format="json_object",
    )
    chat.append(system(prompt["system"]))

    user_parts: list = [prompt["user"]]
    if images:
        for img in images[:MAX_IMAGES]:
            user_parts.append(image(img))
        if len(images) > MAX_IMAGES:
            typer.echo(f"  Truncated figures from {len(images)} to {MAX_IMAGES}")
    chat.append(user(*user_parts))

    response = chat.sample()
    return parse_llm_json(response.content)
