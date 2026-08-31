"""Telegram channel for Clean Agent."""

from __future__ import annotations

import asyncio
import os
from typing import Set

from config import cfg
from core.logging_setup import log
from core.loop import run_agent
from core.ratelimit import RateLimiter
from core.response import AgentAnswer
from memory.dream import dream


def _make_limiter() -> RateLimiter:
    db = getattr(cfg, "tg_rate_db", None)
    db_path = None
    if db:
        db_path = cfg.root / db if not str(db).startswith("/") else db
    return RateLimiter(
        max_calls=getattr(cfg, "tg_max_calls", 20),
        window_seconds=getattr(cfg, "tg_window_seconds", 60.0),
        db_path=db_path,
    )


_limiter = _make_limiter()


def _allowed_users() -> Set[int] | None:
    raw = os.environ.get("TELEGRAM_ALLOWED_USERS", "").strip()
    if not raw:
        return None
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


def _format_answer(result: str | AgentAnswer) -> str:
    if isinstance(result, AgentAnswer):
        return result.to_text()
    return str(result)


def run_telegram() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN env var.")

    try:
        from telegram import Update
        from telegram.ext import (
            Application, CommandHandler, MessageHandler, ContextTypes, filters,
        )
    except ImportError as e:
        raise SystemExit("pip install 'python-telegram-bot>=21'") from e

    allowed = _allowed_users()

    async def _authorized(update: Update) -> bool:
        user = update.effective_user
        if user is None:
            return False
        if allowed is not None and user.id not in allowed:
            await update.effective_message.reply_text("Access denied.")
            return False
        return True

    async def _rate_ok(update: Update) -> bool:
        user = update.effective_user
        key = str(user.id) if user else "anon"
        if not _limiter.allow(key):
            await update.effective_message.reply_text(
                f"Rate limit exceeded. Try again later. (remaining={_limiter.remaining(key)})"
            )
            return False
        return True

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update):
            return
        await update.message.reply_text("Clean Agent online. /dream /status /help")

    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update):
            return
        await update.message.reply_text("/start /dream /status /help + free text")

    async def cmd_dream(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update) or not await _rate_ok(update):
            return
        await update.message.reply_text("Running dream…")
        result = await asyncio.to_thread(dream)
        await update.message.reply_text(result[:4000])

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update):
            return
        from core.health import health_report
        report = await asyncio.to_thread(health_report)
        extra = f"\nrate_limit remaining={_limiter.remaining(str(update.effective_user.id))}"
        await update.message.reply_text((report + extra)[:4000])

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _authorized(update) or not await _rate_ok(update):
            return
        text = (update.message.text or "").strip()
        if not text:
            return
        await update.message.chat.send_action("typing")

        def _run() -> str:
            return _format_answer(run_agent(text, verbose=False, as_structured=True))

        try:
            answer = await asyncio.to_thread(_run)
        except Exception as e:
            answer = f"Error: {e}"

        for i in range(0, max(len(answer), 1), 4000):
            await update.message.reply_text(answer[i : i + 4000] or "(empty)")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("dream", cmd_dream))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    print("Telegram bot running.")
    app.run_polling(drop_pending_updates=True)
