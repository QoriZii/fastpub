"""LLM translation — translate PaperDocument content to Chinese."""
from __future__ import annotations

from typing import Any

import typer

from fastpub import config
from fastpub.models import PaperDocument
from fastpub.pipeline.utils import make_client, parse_llm_json
from fastpub.prompts import build_prompt


def translate_to_chinese(doc: PaperDocument) -> dict[str, Any]:
    """Translate narrative, sections, and meta to Chinese.

    Returns a dict with translated content matching the web renderer's
    expected TranslatedContent shape.
    """
    from xai_sdk.chat import system, user

    sections_text = "\n\n".join(
        f"### {s.title} (id: {s.id})\n{s.summary}\nKey points:\n"
        + "\n".join(f"- {p}" for p in s.key_points)
        for s in doc.sections
    )

    figures_text = "\n\n".join(
        f"### {f.id}\nCaption: {f.caption}\nAI Description: {f.ai_description}"
        for f in doc.figures
        if f.usability != "skip"
    )

    prompt = build_prompt("translate_to_chinese", {
        "title": doc.meta.title,
        "abstract": doc.meta.abstract,
        "hook": doc.narrative.hook,
        "problem": doc.narrative.problem,
        "approach": doc.narrative.approach,
        "results": "\n- ".join(doc.narrative.results),
        "significance": doc.narrative.significance,
        "sections": sections_text,
        "figures": figures_text,
    })

    client = make_client()
    typer.echo(f"  Translating with {config.XAI_MODEL}…")

    chat = client.chat.create(
        model=config.XAI_MODEL,
        max_tokens=8192,
        response_format="json_object",
    )
    chat.append(system(prompt["system"]))
    chat.append(user(prompt["user"]))
    response = chat.sample()

    return parse_llm_json(response.content)
