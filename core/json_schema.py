"""JSON schema for final agent answers + parse helpers."""

from __future__ import annotations

import json
import re
from typing import Any

from core.response import AgentAnswer


AGENT_ANSWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "answer": {"type": "string", "description": "Final answer for the user"},
        "sources": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Evidence: file:path, tool:name, or https:// URL",
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "0=guess, 1=fully grounded in tools",
        },
    },
    "required": ["answer"],
    "additionalProperties": False,
}


FINAL_JSON_INSTRUCTION = """
When you give the FINAL answer (no more tools), output ONLY valid JSON:
{
  "answer": "<text for the user>",
  "sources": ["file:...", "https://...", "tool:bash"],
  "confidence": 0.0
}
No markdown fences. No text before or after the JSON.
confidence: 1.0 only if every fact came from tools this turn; else lower.
"""


def parse_agent_json(text: str) -> AgentAnswer | None:
    if not text or not text.strip():
        return None
    raw = text.strip()
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw, re.I)
    if fence:
        raw = fence.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    blob = raw[start : end + 1]
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "answer" not in data:
        return None
    answer = str(data.get("answer", "")).strip()
    if not answer:
        return None
    sources = data.get("sources") or []
    if not isinstance(sources, list):
        sources = [str(sources)]
    conf = data.get("confidence", 0.5)
    try:
        conf = float(conf)
    except (TypeError, ValueError):
        conf = 0.5
    conf = max(0.0, min(1.0, conf))
    return AgentAnswer(
        answer=answer,
        sources=[str(s) for s in sources],
        tools_used=[],
        confidence=conf,
        verified=False,
    )


def merge_structured(
    parsed: AgentAnswer | None,
    fallback_text: str,
    tools_used: list[str],
    sources_from_trace: list[str],
    *,
    verified: bool,
    confidence: float,
) -> AgentAnswer:
    if parsed is None:
        return AgentAnswer(
            answer=fallback_text.strip(),
            sources=sources_from_trace,
            tools_used=list(dict.fromkeys(tools_used)),
            confidence=confidence,
            verified=verified,
        )
    sources = list(parsed.sources) if parsed.sources else list(sources_from_trace)
    seen = set(sources)
    for s in sources_from_trace:
        if s not in seen:
            sources.append(s)
            seen.add(s)
    return AgentAnswer(
        answer=parsed.answer or fallback_text.strip(),
        sources=sources,
        tools_used=list(dict.fromkeys(tools_used)),
        confidence=parsed.confidence if parsed.sources else confidence,
        verified=verified,
    )
