"""Structured agent response (JSON-friendly)."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field


class AgentAnswer(BaseModel):
    """Canonical structured output from the agent."""

    answer: str = Field(description="Final user-facing answer")
    sources: list[str] = Field(default_factory=list, description="Evidence sources")
    tools_used: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    verified: bool = Field(default=False, description="Passed verifier pass")

    def to_text(self) -> str:
        lines = [self.answer.strip()]
        if self.sources:
            lines.append("")
            lines.append("Sources:")
            for s in self.sources[:12]:
                lines.append(f"- {s}")
        if self.tools_used:
            lines.append("")
            lines.append(f"Tools: {', '.join(self.tools_used)}")
        lines.append(f"Confidence: {self.confidence:.2f}" + (" (verified)" if self.verified else ""))
        return "\n".join(lines)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)


def extract_sources_from_trace(tool_trace: list[dict[str, Any]]) -> list[str]:
    sources: list[str] = []
    seen: set[str] = set()
    url_re = re.compile(r"https?://[^\s\]\)\"']+")
    for t in tool_trace:
        name = t.get("name", "")
        out = str(t.get("output", ""))
        if name in {"read_file", "write_file", "list_dir"}:
            args = t.get("args") or {}
            path = args.get("path")
            if path and path not in seen:
                seen.add(path)
                sources.append(f"file:{path}")
        if name == "web_search":
            for m in url_re.findall(out):
                if m not in seen:
                    seen.add(m)
                    sources.append(m)
        if name == "bash" and t.get("success"):
            sources.append("tool:bash")
        if name == "search_memory":
            sources.append("memory")
    return sources


def estimate_confidence(tool_trace: list[dict[str, Any]], verified: bool) -> float:
    if not tool_trace:
        return 0.35 if not verified else 0.45
    successes = sum(1 for t in tool_trace if t.get("success"))
    ratio = successes / max(len(tool_trace), 1)
    base = 0.55 + 0.35 * ratio
    if verified:
        base = min(1.0, base + 0.1)
    return round(base, 2)


def build_structured_answer(
    text: str,
    tools_used: list[str],
    tool_trace: list[dict[str, Any]],
    *,
    verified: bool = False,
) -> AgentAnswer:
    return AgentAnswer(
        answer=text.strip(),
        sources=extract_sources_from_trace(tool_trace),
        tools_used=list(dict.fromkeys(tools_used)),
        confidence=estimate_confidence(tool_trace, verified),
        verified=verified,
    )
