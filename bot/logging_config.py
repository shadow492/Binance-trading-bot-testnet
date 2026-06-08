"""
Logging configuration for the trading bot.
Sets up structured logging to both a timestamped log file (DEBUG)
and the console (WARNING+), so rich CLI output stays clean.
"""

import logging
import os
from datetime import datetime


def setup_logging(log_dir: str = "logs") -> str:
    """
    Configure root logger with a file handler (DEBUG) and a console
    handler (WARNING). Returns the path to the log file created.
    """
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"trading_bot_{timestamp}.log")

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── File handler: captures everything (DEBUG and above) ──────────────────
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # ── Console handler: only WARNING+ so rich output isn't polluted ──────────
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Avoid duplicate handlers when module is re-imported in tests
    if not root.handlers:
        root.addHandler(fh)
        root.addHandler(ch)
    else:
        root.handlers.clear()
        root.addHandler(fh)
        root.addHandler(ch)

    logging.getLogger("urllib3").setLevel(logging.WARNING)  # quieten HTTP noise

    return log_file
