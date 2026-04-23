"""
Logging configuration for the trading bot.

Sets up:
  - File handler  → logs/app.log  (DEBUG and above)
  - Console handler → stderr      (WARNING and above — keeps CLI output clean)
"""

import logging
from pathlib import Path

LOG_DIR  = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"

LOG_FORMAT  = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.DEBUG) -> None:
    """
    Configure the root logger.  Call once at application startup.
    Safe to call multiple times — subsequent calls are no-ops.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    if root.handlers:
        return  # already configured

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # ── File handler (DEBUG+) ──────────────────────────────────────────────────
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    # ── Console handler (WARNING+ — won't pollute normal CLI output) ───────────
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(formatter)

    root.addHandler(fh)
    root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    """Return a named child logger.  Always call setup_logging() first."""
    return logging.getLogger(name)