"""Permission gate for dangerous tool actions. Production safety layer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from config import cfg


class RiskLevel(str, Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


@dataclass
class PermissionDecision:
    allowed: bool
    level: RiskLevel
    reason: str = ""


BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+/\*",
    r"mkfs\.",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",
    r"dd\s+if=/dev/(zero|random|urandom)",
    r">\s*/dev/sd[a-z]",
    r"chmod\s+-R\s+777\s+/",
    r"curl\s+.*\|\s*(ba)?sh",
    r"wget\s+.*\|\s*(ba)?sh",
    r"shutdown",
    r"reboot",
    r"passwd",
    r"userdel",
    r"iptables\s+-F",
]

CAUTION_PATTERNS = [
    r"rm\s+-rf",
    r"rm\s+.*-r",
    r"sudo\s+",
    r"chmod\s+",
    r"chown\s+",
    r"mv\s+.*\s+/",
    r"dd\s+",
    r">\s*/etc/",
    r"systemctl\s+(stop|disable|mask)",
]


def assess_bash(command: str) -> PermissionDecision:
    cmd = command.strip()
    if not cfg.allow_bash:
        return PermissionDecision(False, RiskLevel.BLOCKED, "Bash disabled in config")

    for pat in BLOCKED_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            return PermissionDecision(
                False, RiskLevel.BLOCKED, f"Blocked pattern: {pat}"
            )

    for pat in cfg.bash_denylist:
        if pat.lower() in cmd.lower():
            return PermissionDecision(
                False, RiskLevel.BLOCKED, f"Denylist match: {pat}"
            )

    for pat in CAUTION_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            if cfg.require_confirmation:
                return PermissionDecision(
                    False,
                    RiskLevel.CAUTION,
                    f"Needs confirmation (matched: {pat}). Set confirm or disable require_confirmation.",
                )
            return PermissionDecision(True, RiskLevel.CAUTION, f"Caution: {pat}")

    return PermissionDecision(True, RiskLevel.SAFE, "OK")


def assess_write(path: str) -> PermissionDecision:
    forbidden_prefixes = (
        "/etc/",
        "/usr/",
        "/bin/",
        "/sbin/",
        "/boot/",
        "/lib/",
        "/proc/",
        "/sys/",
        "/dev/",
    )
    resolved = path
    try:
        from pathlib import Path
        resolved = str(Path(path).resolve())
    except Exception:
        pass

    for prefix in forbidden_prefixes:
        if resolved.startswith(prefix) or path.startswith(prefix):
            return PermissionDecision(
                False, RiskLevel.BLOCKED, f"Write to system path blocked: {prefix}"
            )
    return PermissionDecision(True, RiskLevel.SAFE, "OK")


_confirm_callback: Callable[[str], bool] | None = None


def set_confirm_callback(cb: Callable[[str], bool] | None) -> None:
    global _confirm_callback
    _confirm_callback = cb


def request_confirmation(message: str) -> bool:
    if _confirm_callback is None:
        return not cfg.require_confirmation
    return _confirm_callback(message)
