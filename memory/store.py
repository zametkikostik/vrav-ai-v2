"""Persistent memory backed by SQLite FTS5 + markdown files."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import cfg


def init_memory() -> None:
    cfg.memory_dir.mkdir(exist_ok=True)
    cfg.skills_dir.mkdir(exist_ok=True)
    conn = sqlite3.connect(cfg.db_path)
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS mem USING fts5(
            content,
            source,
            created
        )
        """
    )
    conn.commit()
    conn.close()


def add_memory(text: str, source: str = "session") -> None:
    if not text.strip():
        return
    conn = sqlite3.connect(cfg.db_path)
    conn.execute(
        "INSERT INTO mem(content, source, created) VALUES (?, ?, ?)",
        (text.strip(), source, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def search_memory(query: str, limit: int = 6) -> str:
    if not query.strip():
        return "Empty query."
    conn = sqlite3.connect(cfg.db_path)
    try:
        rows = conn.execute(
            "SELECT content, source, created FROM mem WHERE content MATCH ? LIMIT ?",
            (query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = conn.execute(
            "SELECT content, source, created FROM mem WHERE content LIKE ? LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return "No relevant memory found."
    return "\n---\n".join(f"[{src} | {ts}]\n{txt}" for txt, src, ts in rows)


def load_static_context() -> str:
    parts: list[str] = []
    mem_file = cfg.memory_dir / "MEMORY.md"
    if mem_file.exists():
        text = mem_file.read_text(encoding="utf-8")
        parts.append("### Long-term memory\n" + text[: cfg.memory_max_chars])
    for skill_path in sorted(cfg.skills_dir.glob("*/SKILL.md")):
        body = skill_path.read_text(encoding="utf-8")
        parts.append(f"### Skill: {skill_path.parent.name}\n" + body[:1200])
    return "\n\n".join(parts)
