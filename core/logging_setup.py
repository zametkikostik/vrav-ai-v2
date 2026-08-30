"""Simple structured logging for production."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import cfg


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("clean_agent")
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, cfg.log_level.upper(), logging.INFO))
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    if cfg.log_to_file:
        log_file = cfg.log_dir / f"agent_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


log = setup_logging()
