"""Interactive CLI channel with confirmation support."""

from __future__ import annotations

from core.loop import run_agent
from core.permissions import set_confirm_callback
from memory.dream import dream


def _confirm(message: str) -> bool:
    print(f"\n⚠️  {message}")
    try:
        ans = input("Confirm? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return ans in {"y", "yes", "д", "да"}


def run_cli() -> None:
    set_confirm_callback(_confirm)
    print("Clean Agent (production). Commands: dream | exit")
    print("Anti-hallucination: ON | tool-first | low temperature")
    while True:
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not raw:
            continue
        lower = raw.lower()
        if lower in {"exit", "quit", "q"}:
            print("Bye.")
            break
        if lower == "dream":
            print(dream())
            continue

        answer = run_agent(raw, verbose=True)
        print("\n" + answer)
