"""Health check: Ollama reachability, model presence, disk paths."""

from __future__ import annotations

from pathlib import Path

from config import cfg


def health_report() -> str:
    lines: list[str] = []
    lines.append("=== Clean Agent status ===")
    lines.append(f"model: {cfg.model}")
    lines.append(f"temperature: {cfg.temperature}")
    lines.append(f"max_turns: {cfg.max_turns}")
    lines.append(f"force_reflection: {cfg.force_reflection}")
    lines.append(f"require_confirmation: {cfg.require_confirmation}")
    lines.append(f"root: {cfg.root}")

    for label, p in [
        ("memory_dir", cfg.memory_dir),
        ("skills_dir", cfg.skills_dir),
        ("db", cfg.db_path),
        ("logs", cfg.log_dir),
    ]:
        exists = p.exists() if isinstance(p, Path) else False
        lines.append(f"{label}: {p} ({'ok' if exists else 'missing'})")

    try:
        import ollama
        tags = ollama.list()
        models = []
        raw = tags.get("models") if isinstance(tags, dict) else getattr(tags, "models", [])
        for m in raw or []:
            name = m.get("name") if isinstance(m, dict) else getattr(m, "model", None) or getattr(m, "name", str(m))
            models.append(str(name))
        lines.append(f"ollama: reachable, models={len(models)}")
        if cfg.model in models or any(cfg.model in m for m in models):
            lines.append(f"configured model present: yes ({cfg.model})")
        else:
            lines.append(f"configured model present: NO — pull/create '{cfg.model}'")
            if models:
                lines.append("available: " + ", ".join(models[:12]))
    except Exception as e:
        lines.append(f"ollama: ERROR — {e}")

    skills = list(cfg.skills_dir.glob("*/SKILL.md")) if cfg.skills_dir.exists() else []
    lines.append(f"skills: {len(skills)}")

    return "\n".join(lines)


def check_ready() -> bool:
    try:
        import ollama
        tags = ollama.list()
        raw = tags.get("models") if isinstance(tags, dict) else getattr(tags, "models", [])
        models = []
        for m in raw or []:
            name = m.get("name") if isinstance(m, dict) else getattr(m, "model", None) or getattr(m, "name", str(m))
            models.append(str(name))
        return any(cfg.model in m for m in models)
    except Exception:
        return False
