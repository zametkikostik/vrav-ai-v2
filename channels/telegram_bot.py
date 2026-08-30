"""Telegram channel for Clean Agent.

Requires:
  pip install 'python-telegram-bot>=21'
  export TELEGRAM_BOT_TOKEN=...
  optionally TELEGRAM_ALLOWED_USERS=123,456  (comma-separated user ids)
"""

from __future__ import annotations

import asyncio
import os
from typing import Set

from core.logging_setup import log
from core.loop import run_agent
from memory.dream import dream


def _allowed_users() -> Set[int] | None:
    raw = os.environ.get("TELEGRAM_ALLOWED_USERS", "").strip()
    if not raw:
        return None  # allow everyone (dev mode)
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


def run_telegram() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "Set TELEGRAM_BOT_TOKEN env var.\n"
            "Optional: TELEGRAM_ALLOWED_USERS=id1,id2"
        )

    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            MessageHandler,
            ContextTypes,
            filters,
        )
    except ImportError as e:
        raise SystemExit(
            "Install telegram support: pip install 'python-telegram-bot>=21'"
        ) from e

    allowed = _allowed_users()

    async def _authorized(update: Update) -> bool:
        user = update.effective_user
        if user is None:
            return False
        if allowed is not None and user.id not in allowed:
            await update.effective_message.reply_text("Access denied.")
            log.warning("telegram denied user_id=%s", user.id)
            return False
        return True

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update):
            return
        await update.message.reply_text(
            "Clean Agent online.\n"
            "Send a task in plain text.\n"
            "Commands: /dream /status /help"
        )

    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update):
            return
        await update.message.reply_text(
            "/start — hello\n"
            "/dream — consolidate memory\n"
            "/status — model & config\n"
            "/help — this message\n"
            "Any other text — run the agent"
        )

    async def cmd_dream(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update):
            return
        await update.message.reply_text("Running dream…")
        result = await asyncio.to_thread(dream)
        await update.message.reply_text(result[:4000])

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update):
            return
        from core.health import health_report
        report = await asyncio.to_thread(health_report)
        await update.message.reply_text(report[:4000])

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update):
            return
        text = (update.message.text or "").strip()
        if not text:
            return
        await update.message.chat.send_action("typing")
        log.info("telegram user=%s text=%s", update.effective_user.id, text[:200])

        def _run() -> str:
            return run_agent(text, verbose=False)

        try:
            answer = await asyncio.to_thread(_run)
        except Exception as e:
            log.exception("telegram agent error")
            answer = f"Error: {e}"

        if len(answer) <= 4000:
            await update.message.reply_text(answer)
        else:
            for i in range(0, len(answer), 4000):
                await update.message.reply_text(answer[i : i + 4000])

    app = (
        Application.builder()
        .token(token)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("dream", cmd_dream))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    log.info("telegram bot starting (allowed=%s)", allowed or "all")
    print("Telegram bot running. Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)
