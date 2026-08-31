"""Configuration for Clean Agent — production defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path


@dataclass
class Config:
    model: str = "bggpt-gemma3-12b"
    temperature: float = 0.12
    num_ctx: int = 16384
    max_turns: int = 14
    force_reflection: bool = True
    use_verifier: bool = True
    structured_output: bool = True
    tg_max_calls: int = 20
    tg_window_seconds: float = 60.0
    dream_cron_hours: float = 6.0

    root: Path = field(default_factory=lambda: Path(os.environ.get("CLEAN_AGENT_ROOT", Path(__file__).resolve().parent)))
    memory_dir: Path = field(init=False)
    skills_dir: Path = field(init=False)
    db_path: Path = field(init=False)
    log_dir: Path = field(init=False)

    allow_bash: bool = True
    bash_timeout: int = 30
    require_confirmation: bool = False
    bash_denylist: tuple[str, ...] = (
        "rm -rf /",
        "mkfs",
        ":(){",
        "dd if=/dev/zero",
        "> /dev/sd",
        "chmod -R 777 /",
    )

    dream_limit: int = 30
    memory_max_chars: int = 4000
    max_tool_output_chars: int = 12000

    log_level: str = "INFO"
    log_to_file: bool = True

    def __post_init__(self) -> None:
        self.memory_dir = self.root / "memory"
        self.skills_dir = self.root / "skills"
        self.db_path = self.root / "agent_memory.db"
        self.log_dir = self.root / "logs"
        self.memory_dir.mkdir(exist_ok=True)
        self.skills_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)


cfg = Config()
