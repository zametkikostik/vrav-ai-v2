"""Simple sub-agent spawning: isolated context, returns summary only."""

from __future__ import annotations

from typing import Any

from config import cfg
from core.llm import chat
from core.logging_setup import log
from core.prompts import SYSTEM_PROMPT
from core.tools import TOOLS_SPEC, execute_tool
from memory.store import load_static_context
import json


def run_subagent(
    task: str,
    *,
    max_turns: int | None = None,
    include_memory: bool = False,
) -> str:
    """
    Run a focused sub-agent with its own message history.
    Only the final text is returned to the parent (isolation).
    """
    turns = max_turns or min(8, cfg.max_turns)
    context = load_static_context() if include_memory else ""

    system = (
        SYSTEM_PROMPT
        + "\n\nYou are a sub-agent. Solve ONLY the given task. "
        "Be concise. Return a clear final summary."
    )
    if context:
        system += "\n\n## Context\n" + context[:2000]

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": task},
    ]

    log.info("subagent start task=%s", task[:120])

    for _ in range(turns):
        msg = chat(messages, tools=TOOLS_SPEC, temperature=0.1)
        messages.append(msg)
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            final = (msg.get("content") or "").strip()
            log.info("subagent done (%s chars)", len(final))
            return final or "(empty sub-agent result)"

        for call in tool_calls:
            name = call["function"]["name"]
            raw = call["function"]["arguments"]
            args = json.loads(raw) if isinstance(raw, str) else (raw or {})
            result = execute_tool(name, args)
            messages.append(
                {
                    "role": "tool",
                    "name": name,
                    "content": result.model_dump_json(),
                }
            )

    return "Sub-agent reached turn limit."
