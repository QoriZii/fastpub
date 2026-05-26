"""Scene script generator — LLM produces scene array from PaperDocument."""
from __future__ import annotations

from fastpub.models import PaperDocument
from fastpub.pipeline.utils import make_client, parse_llm_json
from fastpub.prompts import build_prompt
from fastpub import config


def generate_scene_script(doc: PaperDocument) -> list[dict]:
    """Generate a scene script from a PaperDocument. Returns list of scene dicts."""
    scenes = _call_llm(doc)
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
