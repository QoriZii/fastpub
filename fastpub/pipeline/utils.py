"""Shared pipeline utilities — LLM client, JSON parsing."""
from __future__ import annotations

import re
import json

from fastpub import config


def call_llm(
    *,
    system_prompt: str,
    user_content: str | list,
    max_tokens: int = 8192,
) -> str:
    """Call the configured LLM provider and return response text.

    user_content can be a plain string or a list of content parts
    (for multimodal messages with images).
    """
    provider = config.FASTPUB_PROVIDER
    model = config.FASTPUB_MODEL

    if provider == "xai":
        return _call_xai(system_prompt, user_content, model, max_tokens)
    else:
        return _call_openai(system_prompt, user_content, model, max_tokens)


def _call_xai(system_prompt: str, user_content: str | list, model: str, max_tokens: int) -> str:
    from xai_sdk import Client
    from xai_sdk.chat import system, user

    client = Client()
    chat = client.chat.create(
        model=model,
        max_tokens=max_tokens,
        response_format="json_object",
    )
    chat.append(system(system_prompt))

    if isinstance(user_content, list):
        chat.append(user(*user_content))
    else:
        chat.append(user(user_content))

    response = chat.sample()
    return response.content


def _call_openai(system_prompt: str, user_content: str | list, model: str, max_tokens: int) -> str:
    from openai import OpenAI

    provider = config.FASTPUB_PROVIDER
    if provider == "deepseek":
        client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    else:
        raise ValueError(f"Unknown OpenAI-compatible provider: {provider}")

    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content


def parse_llm_json(raw: str) -> dict | list:
    """Parse LLM response text as JSON, stripping code fences and trailing commas.

    If the JSON is truncated (unterminated strings/brackets), attempts repair
    by closing open strings, removing the incomplete trailing element, and
    balancing brackets.
    """
    cleaned = re.sub(r"^```[a-z]*\n?|\n?```$", "", raw.strip())
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        repaired = _repair_truncated_json(cleaned)
        return json.loads(repaired)


def _repair_truncated_json(s: str) -> str:
    """Best-effort repair of truncated JSON by closing open structures."""
    in_string = False
    last_quote = -1
    stack: list[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and in_string:
            i += 2
            continue
        if c == '"':
            in_string = not in_string
            last_quote = i
        elif not in_string:
            if c in '{[':
                stack.append('}' if c == '{' else ']')
            elif c in '}]' and stack:
                stack.pop()
        i += 1

    if in_string and last_quote >= 0:
        s = s[:last_quote] + '"'
        s = re.sub(r',\s*"[^"]*"\s*$', '', s)
        stack.clear()
        in_str = False
        for c in s:
            if c == '"':
                in_str = not in_str
            elif not in_str:
                if c in '{[':
                    stack.append('}' if c == '{' else ']')
                elif c in '}]' and stack:
                    stack.pop()

    s = re.sub(r',\s*$', '', s.rstrip())
    s += ''.join(reversed(stack))
    return s
