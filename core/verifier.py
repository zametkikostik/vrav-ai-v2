"""Final-answer verifier: strip unsupported claims (anti-hallucination)."""

from __future__ import annotations

from typing import Any

from core.llm import chat
from core.logging_setup import log


VERIFY_PROMPT = """You are a strict fact verifier for a tool-using agent.

Given:
1) the user's question
2) the agent's draft answer
3) the list of tool results actually obtained this session

Rules:
- Remove or rewrite any factual claim not supported by tool results or the user message.
- If a claim has no evidence, replace it with "не проверено" / "not verified".
- Keep the answer useful and in the same language as the draft.
- Do NOT invent new facts.
- Output ONLY the corrected final answer text (no preamble).

User question:
{question}

Tool evidence:
{evidence}

Draft answer:
{draft}
"""


def _format_evidence(tool_trace: list[dict[str, Any]]) -> str:
    if not tool_trace:
        return "(no tools were called this session)"
    parts = []
    for i, t in enumerate(tool_trace, 1):
        name = t.get("name", "?")
        out = str(t.get("output", ""))[:1500]
        parts.append(f"[{i}] tool={name}\n{out}")
    return "\n\n".join(parts)


def verify_answer(
    question: str,
    draft: str,
    tool_trace: list[dict[str, Any]],
) -> str:
    if not draft.strip():
        return draft

    if not tool_trace and len(draft) < 400:
        low = draft.lower()
        if any(w in low for w in ("привет", "hello", "help", "справка", "что ты")):
            return draft

    evidence = _format_evidence(tool_trace)
    prompt = VERIFY_PROMPT.format(
        question=question[:2000],
        evidence=evidence[:8000],
        draft=draft[:4000],
    )
    try:
        msg = chat(
            [{"role": "user", "content": prompt}],
            tools=None,
            temperature=0.05,
        )
        verified = (msg.get("content") or "").strip()
        if verified:
            log.info("verifier rewrote answer (%s → %s chars)", len(draft), len(verified))
            return verified
    except Exception as e:
        log.warning("verifier failed: %s", e)
    return draft
