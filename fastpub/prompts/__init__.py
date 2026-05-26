"""Prompt loader with {{variable}} interpolation and {{#if}}...{{/if}} conditionals."""
from __future__ import annotations

import json
import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(prompt_id: str) -> dict[str, str]:
    """Load a prompt template pair (system.txt + user.txt).

    Returns dict with keys: system, user.
    """
    prompt_dir = PROMPTS_DIR / prompt_id
    system_text = (prompt_dir / "system.txt").read_text(encoding="utf-8").strip()
    try:
        user_text = (prompt_dir / "user.txt").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        user_text = ""
    return {"system": system_text, "user": user_text}


def build_prompt(prompt_id: str, variables: dict) -> dict[str, str]:
    """Load, process conditionals, and interpolate a prompt template.

    Returns {"system": str, "user": str}.
    """
    prompt = load_prompt(prompt_id)
    return {
        "system": _interpolate(_process_conditionals(prompt["system"], variables), variables),
        "user": _interpolate(_process_conditionals(prompt["user"], variables), variables),
    }


def _process_conditionals(template: str, conditions: dict) -> str:
    """Process {{#if cond}}...{{/if}} blocks."""
    def _replace(m: re.Match) -> str:
        cond_name = m.group(1)
        content = m.group(2)
        return content if conditions.get(cond_name) else ""
    return re.sub(r"\{\{#if (\w+)\}\}([\s\S]*?)\{\{/if\}\}", _replace, template)


def _interpolate(template: str, variables: dict) -> str:
    """Replace {{variable}} placeholders with values."""
    def _replace(m: re.Match) -> str:
        key = m.group(1)
        value = variables.get(key)
        if value is None:
            return m.group(0)
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)
    return re.sub(r"\{\{(\w+)\}\}", _replace, template)
