"""
Shared helper functions. User state now lives in the SQLite-backed
`database.db` singleton instead of an in-memory dict.
"""
import logging
import math
from datetime import datetime, timezone

from database import db

logger = logging.getLogger("bot")


def get_language(user_id: int) -> str:
    return db.get_language(user_id)


def set_language(user_id: int, lang_code: str) -> None:
    db.set_language(user_id, lang_code)


def get_credits(user_id: int) -> int:
    return db.get_credits(user_id)


def add_credits(user_id: int, amount: int) -> int:
    return db.add_credits(user_id, amount)


def spend_credit(user_id: int, amount: int = 1) -> bool:
    return db.spend_credit(user_id, amount)


def is_admin(user_id: int) -> bool:
    return db.is_admin(user_id)


def get_settings(user_id: int) -> dict:
    return db.get_settings(user_id)


# --- Generic, non-domain-specific helpers -----------------------------------
def paginate(items: list, page: int, page_size: int = 10) -> tuple[list, int]:
    """
    Slice `items` for 1-based `page`. Returns (page_items, total_pages).
    Clamps `page` into range so callers don't need to bounds-check first.
    """
    total_pages = max(1, math.ceil(len(items) / page_size))
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    return items[start : start + page_size], total_pages


def truncate(text: str, max_len: int = 80, suffix: str = "…") -> str:
    """Shorten `text` for display (e.g. in a button label or log line)."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)].rstrip() + suffix


def format_currency(amount: float, currency: str = "ETB") -> str:
    return f"{amount:,.0f} {currency}"


def format_timestamp(dt: datetime | None = None) -> str:
    """Human-readable UTC timestamp, e.g. for logs or 'last updated' text."""
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def parse_callback_data(data: str, sep: str = ":") -> tuple[str, list[str]]:
    """
    Split callback_data like 'settings:format:JPEG' into
    ("settings", ["format", "JPEG"]). Keeps handlers from repeating
    `.split(":", n)[i]` everywhere.
    """
    parts = data.split(sep)
    return parts[0], parts[1:]


def setup_logging(level: int = logging.INFO, log_path: str = "logs/bot.log") -> None:
    """
    Configure root + 'bot' loggers to write to both console and a rotating
    file under logs/. Call this once from main.py before starting the bot.
    """
    import os
    from logging.handlers import RotatingFileHandler

    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
