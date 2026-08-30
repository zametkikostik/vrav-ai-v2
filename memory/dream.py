"""Background memory consolidation (Dream) + auto triggers."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

import ollama

from config import cfg
from core.logging_setup import log
from memory.store import init_memory

STATE_FILE = cfg.memory_dir / "dream_state.json"


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_dream": None, "sessions_since_dream": 0}


def _save_state(state: dict) -> None:
    cfg.memory_dir.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def note_session() -> None:
    state = _load_state()
    state["sessions_since_dream"] = int(state.get("sessions_since_dream") or 0) + 1
    _save_state(state)


def should_auto_dream(min_sessions: int = 5) -> bool:
    state = _load_state()
    return int(state.get("sessions_since_dream") or 0) >= min_sessions


def dream() -> str:
    init_memory()
    conn = sqlite3.connect(cfg.db_path)
    rows = conn.execute(
        "SELECT content FROM mem ORDER BY created DESC LIMIT ?",
        (cfg.dream_limit,),
    ).fetchall()
    conn.close()

    if not rows:
        return "Nothing to consolidate."

    text = "\n\n".join(r[0] for r in rows)
    prompt = f"""You are the memory consolidation system of a local AI agent.
Analyze the session fragments below and produce a clean MEMORY.md.

Keep only:
- user preferences and style
- important facts
- recurring patterns
- useful conclusions

Remove duplicates and noise. Output pure markdown, max ~150 lines.
Do not invent anything that is not present in the fragments.

Fragments:
{text[:10000]}
"""

    log.info("dream start fragments=%s", len(rows))
    resp = ollama.chat(
        model=cfg.model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1, "num_ctx": cfg.num_ctx},
    )
    content = resp["message"]["content"]
    out_path = cfg.memory_dir / "MEMORY.md"
    out_path.write_text(content, encoding="utf-8")

    state = _load_state()
    state["last_dream"] = datetime.now(timezone.utc).isoformat()
    state["sessions_since_dream"] = 0
    _save_state(state)

    log.info("dream done → %s", out_path)
    return f"Dream complete → {out_path}"


def maybe_auto_dream(min_sessions: int = 5) -> str | None:
    if should_auto_dream(min_sessions):
        return dream()
    return None
