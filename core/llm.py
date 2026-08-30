"""Thin wrapper around Ollama."""

from __future__ import annotations

from typing import Any

import ollama

from config import cfg


def chat(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    temperature: float | None = None,
) -> dict[str, Any]:
    """Call Ollama chat API and return the message dict."""
    kwargs: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "options": {
            "temperature": temperature if temperature is not None else cfg.temperature,
            "num_ctx": cfg.num_ctx,
        },
    }
    if tools:
        kwargs["tools"] = tools

    response = ollama.chat(**kwargs)
    return response["message"]
