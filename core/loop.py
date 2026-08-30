"""Main agentic loop with strong anti-hallucination controls."""

from __future__ import annotations

import json
from typing import Any

from config import cfg
from core.llm import chat
from core.logging_setup import log
from core.prompts import SYSTEM_PROMPT, REFLECTION_HINT, FINAL_FORMAT_HINT
from core.tools import TOOLS_SPEC, execute_tool
from memory.store import init_memory, add_memory, load_static_context
from memory.dream import note_session, maybe_auto_dream
from core.verifier import verify_answer


def run_agent(user_message: str, verbose: bool = True) -> str:
    """Agentic loop: tool-first, low temperature, reflection, verifier."""
    init_memory()
    context = load_static_context()

    system = SYSTEM_PROMPT
    if context:
        system += "\n\n## Loaded context\n" + context

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]

    tools_used: list[str] = []
    tool_trace: list[dict] = []
    reflection_done = False

    for turn in range(cfg.max_turns):
        log.info("turn=%s tools_so_far=%s", turn + 1, tools_used)
        msg = chat(messages, tools=TOOLS_SPEC)
        messages.append(msg)

        tool_calls = msg.get("tool_calls") or []

        if not tool_calls:
            final = (msg.get("content") or "").strip()

            if (
                cfg.force_reflection
                and not reflection_done
                and not tools_used
                and turn < cfg.max_turns - 1
            ):
                reflection_done = True
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            REFLECTION_HINT
                            + "\n\nIf you need tools, call them now. "
                            "Otherwise produce the final answer following the format."
                            + FINAL_FORMAT_HINT
                        ),
                    }
                )
                log.info("reflection pass triggered (no tools used yet)")
                continue

            if getattr(cfg, "use_verifier", True):
                final = verify_answer(user_message, final, tool_trace)
            add_memory(
                f"User: {user_message}\nAgent: {final[:1500]}\nTools: {tools_used}"
            )
            note_session()
            auto = maybe_auto_dream(min_sessions=5)
            if auto and verbose:
                print(f"  [auto-dream] {auto}")
            log.info("final answer (%s chars), tools=%s", len(final), tools_used)
            return final

        for call in tool_calls:
            name = call["function"]["name"]
            raw_args = call["function"]["arguments"]
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}
            else:
                args = raw_args or {}

            tools_used.append(name)
            if verbose:
                print(f"  → {name}({args})")
            log.info("tool_call name=%s args=%s", name, args)

            result = execute_tool(name, args)
            tool_trace.append(
                {"name": name, "args": args, "output": result.output, "success": result.success}
            )

            if verbose:
                preview = result.output[:280].replace("\n", " ")
                status = "OK" if result.success else "FAIL"
                print(f"    [{status}|{result.risk}] {preview}...")
            log.info(
                "tool_result name=%s success=%s risk=%s len=%s",
                name,
                result.success,
                result.risk,
                len(result.output),
            )

            messages.append(
                {
                    "role": "tool",
                    "name": name,
                    "content": result.model_dump_json(),
                }
            )

    log.warning("turn limit reached")
    return "Reached turn limit. Please refine the request or split the task."
