#!/usr/bin/env python3
"""Entry point for Clean Agent (production)."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean Agent — local tool-using AI agent for Ollama / BgGPT"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="cli",
        choices=["cli", "dream", "telegram", "status"],
        help="cli | dream | telegram | status",
    )
    parser.add_argument("-m", "--model", help="Override Ollama model tag")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Require confirmation for caution-level bash commands",
    )
    parser.add_argument(
        "--no-reflection",
        action="store_true",
        help="Disable forced reflection pass",
    )
    args = parser.parse_args()

    from config import cfg
    from core.logging_setup import log

    if args.model:
        cfg.model = args.model
    if args.confirm:
        cfg.require_confirmation = True
    if args.no_reflection:
        cfg.force_reflection = False

    log.info(
        "start cmd=%s model=%s temp=%s confirm=%s reflection=%s",
        args.command,
        cfg.model,
        cfg.temperature,
        cfg.require_confirmation,
        cfg.force_reflection,
    )

    if args.command == "dream":
        from memory.dream import dream
        print(dream())
    elif args.command == "status":
        from core.health import health_report
        print(health_report())
    elif args.command == "telegram":
        from channels.telegram_bot import run_telegram
        run_telegram()
    else:
        from channels.cli import run_cli
        run_cli()


if __name__ == "__main__":
    main()
