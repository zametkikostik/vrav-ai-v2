"""Tool definitions and implementations. Clean-room + production safety."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel

from config import cfg
from core.permissions import assess_bash, assess_write, request_confirmation, RiskLevel


class ToolResult(BaseModel):
    success: bool
    output: str
    risk: str = "safe"


def _truncate(text: str, limit: int | None = None) -> str:
    limit = limit or cfg.max_tool_output_chars
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, {len(text)} total chars]"


def tool_bash(command: str, timeout: int | None = None) -> ToolResult:
    decision = assess_bash(command)
    if not decision.allowed:
        if decision.level == RiskLevel.CAUTION:
            ok = request_confirmation(
                f"Run caution command?\n  {command}\nReason: {decision.reason}"
            )
            if not ok:
                return ToolResult(
                    success=False,
                    output=f"Denied by user/policy: {decision.reason}",
                    risk=decision.level.value,
                )
        else:
            return ToolResult(
                success=False,
                output=f"Blocked: {decision.reason}",
                risk=decision.level.value,
            )

    timeout = timeout or cfg.bash_timeout
    try:
        r = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}\nexit:{r.returncode}"
        return ToolResult(
            success=r.returncode == 0,
            output=_truncate(out),
            risk=decision.level.value,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output=f"Timeout after {timeout}s", risk="caution")
    except Exception as e:
        return ToolResult(success=False, output=str(e), risk="caution")


def tool_read_file(path: str) -> ToolResult:
    try:
        p = Path(path)
        if not p.exists():
            return ToolResult(success=False, output=f"File not found: {path}")
        if not p.is_file():
            return ToolResult(success=False, output=f"Not a file: {path}")
        content = p.read_text(encoding="utf-8", errors="replace")
        return ToolResult(success=True, output=_truncate(content))
    except Exception as e:
        return ToolResult(success=False, output=str(e))


def tool_write_file(path: str, content: str) -> ToolResult:
    decision = assess_write(path)
    if not decision.allowed:
        return ToolResult(
            success=False,
            output=f"Blocked: {decision.reason}",
            risk=decision.level.value,
        )
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return ToolResult(
            success=True,
            output=f"Written: {path} ({len(content)} chars)",
            risk=decision.level.value,
        )
    except Exception as e:
        return ToolResult(success=False, output=str(e))


def tool_list_dir(path: str = ".") -> ToolResult:
    try:
        p = Path(path)
        if not p.exists():
            return ToolResult(success=False, output=f"Path not found: {path}")
        if not p.is_dir():
            return ToolResult(success=False, output=f"Not a directory: {path}")
        entries = []
        for item in sorted(p.iterdir()):
            kind = "dir " if item.is_dir() else "file"
            try:
                size = item.stat().st_size if item.is_file() else 0
            except OSError:
                size = 0
            entries.append(f"{kind} {size:>10}  {item.name}")
        return ToolResult(success=True, output="\n".join(entries) or "(empty)")
    except Exception as e:
        return ToolResult(success=False, output=str(e))


def tool_search_memory(query: str) -> ToolResult:
    from memory.store import search_memory
    return ToolResult(success=True, output=search_memory(query))


def tool_save_skill(name: str, description: str, body: str) -> ToolResult:
    try:
        safe_name = "".join(c for c in name if c.isalnum() or c in "-_").strip()
        if not safe_name:
            return ToolResult(success=False, output="Invalid skill name")
        skill_dir = cfg.skills_dir / safe_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        content = f"# {safe_name}\n\n{description}\n\n{body}\n"
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        return ToolResult(success=True, output=f"Skill saved: {safe_name}")
    except Exception as e:
        return ToolResult(success=False, output=str(e))


def tool_list_skills() -> ToolResult:
    try:
        skills = []
        for d in sorted(cfg.skills_dir.iterdir()):
            skill_file = d / "SKILL.md"
            if skill_file.exists():
                first = skill_file.read_text(encoding="utf-8").splitlines()[:2]
                skills.append(f"- {d.name}: {' | '.join(first)}")
        return ToolResult(
            success=True,
            output="\n".join(skills) if skills else "No skills yet.",
        )
    except Exception as e:
        return ToolResult(success=False, output=str(e))


def tool_spawn_subagent(task: str, max_turns: int = 6) -> ToolResult:
    """Run an isolated sub-agent and return its summary."""
    try:
        from core.subagent import run_subagent
        summary = run_subagent(task, max_turns=max_turns, include_memory=False)
        return ToolResult(success=True, output=summary)
    except Exception as e:
        return ToolResult(success=False, output=str(e))


def tool_web_search(query: str, max_results: int = 5) -> ToolResult:
    """Search the web (DuckDuckGo HTML). Always cite URLs in the answer."""
    import urllib.parse
    import urllib.request
    import re
    try:
        q = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={q}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CleanAgent/0.1 (local research bot)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        results = []
        for m in re.finditer(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            html,
            re.I | re.S,
        ):
            href = m.group(1)
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if "uddg=" in href:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                href = urllib.parse.unquote(parsed.get("uddg", [href])[0])
            if title and href.startswith("http"):
                results.append(f"- {title}\n  {href}")
            if len(results) >= max(1, min(max_results, 8)):
                break
        if not results:
            return ToolResult(success=False, output="No results parsed. Try a different query.")
        return ToolResult(success=True, output="Search results:\n" + "\n".join(results))
    except Exception as e:
        return ToolResult(success=False, output=f"web_search error: {e}")


TOOL_MAP: dict[str, Callable[..., ToolResult]] = {
    "bash": tool_bash,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "list_dir": tool_list_dir,
    "search_memory": tool_search_memory,
    "save_skill": tool_save_skill,
    "list_skills": tool_list_skills,
    "spawn_subagent": tool_spawn_subagent,
    "web_search": tool_web_search,
}

TOOLS_SPEC: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a shell command. Always inspect the real result. Do not invent output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout": {"type": "integer"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents. Use this instead of guessing what a file contains.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories. Use before claiming what exists on disk.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search long-term memory and past sessions",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_skill",
            "description": "Save a reusable skill learned from experience",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["name", "description", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_skills",
            "description": "List all saved skills",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_subagent",
            "description": "Spawn an isolated sub-agent for a focused subtask. Returns only a summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "max_turns": {"type": "integer", "default": 6},
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the public web. Use for current facts. Always cite returned URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
]


def execute_tool(name: str, arguments: dict[str, Any] | str) -> ToolResult:
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return ToolResult(success=False, output="Invalid JSON arguments")

    func = TOOL_MAP.get(name)
    if not func:
        return ToolResult(success=False, output=f"Unknown tool: {name}")

    try:
        return func(**arguments)
    except TypeError as e:
        return ToolResult(success=False, output=f"Bad arguments: {e}")
    except Exception as e:
        return ToolResult(success=False, output=f"Tool error: {e}")
