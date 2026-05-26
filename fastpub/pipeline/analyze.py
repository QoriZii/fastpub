"""LLM analysis — convert parsed PDF into a structured PaperDocument."""
from __future__ import annotations

import typer

from fastpub import config
from fastpub.models import PaperDocument
from fastpub.pipeline.utils import make_client, parse_llm_json
from fastpub.prompts import build_prompt

MAX_IMAGES = 20


def analyze_paper(
    pdf_text: str,
    images: list[str],
    audience: str = "academic",
) -> PaperDocument:
    """Call xAI LLM to produce a PaperDocument from parsed PDF content."""
    from xai_sdk.chat import image, system, user

    prompt = build_prompt("paper_to_document", {
        "paperText": pdf_text,
        "audienceLevel": audience,
        "figureCount": str(len(images)),
        "hasFigures": bool(images),
        "noFigures": not images,
    })

    client = make_client()
    typer.echo(f"  Analyzing with {config.XAI_MODEL}…")

    chat = client.chat.create(
        model=config.XAI_MODEL,
        max_tokens=16384,
        response_format="json_object",
    )
    chat.append(system(prompt["system"]))

    # Build user message with text + figure images (vision)
    user_parts: list = [prompt["user"]]
    if images:
        for img in images[:MAX_IMAGES]:
            user_parts.append(image(img))
        if len(images) > MAX_IMAGES:
            typer.echo(f"  Truncated figures from {len(images)} to {MAX_IMAGES}")
    chat.append(user(*user_parts))

    response = chat.sample()

    data = parse_llm_json(response.content)
    doc = PaperDocument.from_dict(data)

    # Inject base64 image data into figures (LLM can't return base64)
    for i, fig in enumerate(doc.figures):
        if i < len(images):
            fig.src = images[i]

    return doc
