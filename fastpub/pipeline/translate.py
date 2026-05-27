"""LLM translation — translate PaperDocument content to Chinese."""
from __future__ import annotations

import json
from typing import Any

import typer

from fastpub import config
from fastpub.models import PaperDocument
from fastpub.pipeline.utils import make_client, parse_llm_json
from fastpub.prompts import build_prompt


def translate_to_chinese(doc: PaperDocument) -> dict[str, Any]:
    """Translate all content to Chinese (except author names).

    Returns a dict matching the web renderer's expected shape:
    {meta, hook, webSections, figures}.
    """
    from xai_sdk.chat import system, user

    # Serialize web sections for the prompt
    sections_data = []
    for s in doc.web_sections:
        sections_data.append({
            "type": s.type,
            "summary": s.summary,
            "subIssues": [
                {"title": si.title, "description": si.description}
                for si in s.sub_issues
            ],
        })

    figures_data = [
        {"id": f.id, "caption": f.caption, "aiDescription": f.ai_description}
        for f in doc.figures
    ]

    prompt = build_prompt("translate_to_chinese", {
        "title": doc.meta.title,
        "abstract": doc.meta.abstract,
        "hook": doc.hook,
        "webSections": json.dumps(sections_data, ensure_ascii=False, indent=2),
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
