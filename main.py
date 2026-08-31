#!/usr/bin/env python3
"""Entry point for Clean Agent (production)."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean Agent — local tool-using AI agent for Ollama / BgGPT"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="cli",
        choices=["cli", "dream", "telegram", "status", "cron-dream"],
        help="cli | dream | telegram | status | cron-dream",
    )
    parser.add_argument("-m", "--model", help="Override Ollama model tag")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--no-reflection", action="store_true")
    parser.add_argument("--json", action="store_true", help="CLI: structured JSON answers")
    parser.add_argument("--interval-hours", type=float, default=None,
                        help="cron-dream interval hours")
    args = parser.parse_args()

    from config import cfg
    from core.logging_setup import log

    if args.model:
        cfg.model = args.model
    if args.confirm:
        cfg.require_confirmation = True
    if args.no_reflection:
        cfg.force_reflection = False

    log.info("start cmd=%s model=%s", args.command, cfg.model)

    if args.command == "dream":
        from memory.dream import dream
        print(dream())
    elif args.command == "status":
        from core.health import health_report
        print(health_report())
    elif args.command == "telegram":
        from channels.telegram_bot import run_telegram
        run_telegram()
    elif args.command == "cron-dream":
        from core.scheduler import run_dream_cron
        hours = args.interval_hours if args.interval_hours is not None else cfg.dream_cron_hours
        run_dream_cron(interval_hours=hours)
    else:
        from channels.cli import run_cli
        run_cli(json_mode=args.json)


if __name__ == "__main__":
    main()
