"""
Persistent storage (SQLite) for users, their output settings, and job history.

Replaces the in-memory USER_STORE from the old aiogram skeleton and the two
half-finished sqlite prototypes from the OCR bot (database.py / database1.py)
with a single schema that covers everything both bots needed.
"""
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone

from config import DB_PATH, DEFAULT_LANGUAGE, SIGNUP_BONUS_CREDITS, ADMIN_IDS


class Database:
    def __init__(self, path: str = DB_PATH):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    credits INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0,
                    lang TEXT DEFAULT '{DEFAULT_LANGUAGE}',
                    fit_to_size INTEGER DEFAULT 1,
                    regenerate_qr INTEGER DEFAULT 0,
                    mirror_layout INTEGER DEFAULT 1,
                    file_type TEXT DEFAULT 'JPEG',
                    color_mode TEXT DEFAULT 'Both',
                    template TEXT DEFAULT 'default',
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    pairs INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    package_id TEXT NOT NULL,
                    credits INTEGER NOT NULL,
                    price INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    admin_message_id INTEGER,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )

    # --- Users --------------------------------------------------------------
    def get_user(self, user_id: int) -> sqlite3.Row:
        with self._lock, self.conn:
            row = self.conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if row is None:
                is_admin = 1 if user_id in ADMIN_IDS else 0
                self.conn.execute(
                    "INSERT INTO users (user_id, credits, is_admin) VALUES (?, ?, ?)",
                    (user_id, SIGNUP_BONUS_CREDITS, is_admin),
                )
                row = self.conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
            return row

    def get_language(self, user_id: int) -> str:
        return self.get_user(user_id)["lang"]

    def set_language(self, user_id: int, lang_code: str) -> None:
        self.get_user(user_id)
        with self._lock, self.conn:
            self.conn.execute(
                "UPDATE users SET lang = ? WHERE user_id = ?", (lang_code, user_id)
            )

    def get_credits(self, user_id: int) -> int:
        return self.get_user(user_id)["credits"]

    def add_credits(self, user_id: int, amount: int) -> int:
        self.get_user(user_id)
        with self._lock, self.conn:
            self.conn.execute(
                "UPDATE users SET credits = credits + ? WHERE user_id = ?",
                (amount, user_id),
            )
        return self.get_credits(user_id)

    def spend_credit(self, user_id: int, amount: int = 1) -> bool:
        user = self.get_user(user_id)
        if user["credits"] < amount:
            return False
        with self._lock, self.conn:
            self.conn.execute(
                "UPDATE users SET credits = credits - ? WHERE user_id = ?",
                (amount, user_id),
            )
        return True

    def is_admin(self, user_id: int) -> bool:
        if user_id in ADMIN_IDS:
            return True
        return bool(self.get_user(user_id)["is_admin"])

    def set_admin(self, user_id: int, is_admin: bool) -> None:
        self.get_user(user_id)
        with self._lock, self.conn:
            self.conn.execute(
                "UPDATE users SET is_admin = ? WHERE user_id = ?",
                (1 if is_admin else 0, user_id),
            )

    def get_settings(self, user_id: int) -> dict:
        row = self.get_user(user_id)
        return {
            "fit_to_size": bool(row["fit_to_size"]),
            "regenerate_qr": bool(row["regenerate_qr"]),
            "mirror_layout": bool(row["mirror_layout"]),
            "file_type": row["file_type"],
            "color_mode": row["color_mode"],
            "template": row["template"],
        }

    def set_setting(self, user_id: int, key: str, value) -> None:
        allowed = {
            "fit_to_size",
            "regenerate_qr",
            "mirror_layout",
            "file_type",
            "color_mode",
            "template",
        }
        if key not in allowed:
            raise ValueError(f"Unknown setting: {key}")
        self.get_user(user_id)
        with self._lock, self.conn:
            self.conn.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))

    def toggle_setting(self, user_id: int, key: str) -> bool:
        current = self.get_settings(user_id)[key]
        new_value = not current
        self.set_setting(user_id, key, int(new_value))
        return new_value

    def all_user_ids(self) -> list[int]:
        with self._lock, self.conn:
            rows = self.conn.execute("SELECT user_id FROM users").fetchall()
        return [r["user_id"] for r in rows]

    # --- Jobs -----------------------------------------------------------------
    def log_job(self, user_id: int, kind: str, pairs: int = 1) -> None:
        with self._lock, self.conn:
            self.conn.execute(
                "INSERT INTO jobs (user_id, kind, pairs) VALUES (?, ?, ?)",
                (user_id, kind, pairs),
            )

    def recent_jobs(self, user_id: int, hours: int) -> list[sqlite3.Row]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        with self._lock, self.conn:
            return self.conn.execute(
                "SELECT * FROM jobs WHERE user_id = ? AND created_at >= ? ORDER BY created_at DESC",
                (user_id, cutoff),
            ).fetchall()

    # --- Payment requests -------------------------------------------------------
    def create_payment_request(self, user_id: int, package_id: str, credits: int, price: int) -> int:
        with self._lock, self.conn:
            cur = self.conn.execute(
                "INSERT INTO payment_requests (user_id, package_id, credits, price) VALUES (?, ?, ?, ?)",
                (user_id, package_id, credits, price),
            )
            return cur.lastrowid

    def set_payment_admin_message(self, request_id: int, message_id: int) -> None:
        with self._lock, self.conn:
            self.conn.execute(
                "UPDATE payment_requests SET admin_message_id = ? WHERE id = ?",
                (message_id, request_id),
            )

    def get_payment_request(self, request_id: int) -> sqlite3.Row | None:
        with self._lock, self.conn:
            return self.conn.execute(
                "SELECT * FROM payment_requests WHERE id = ?", (request_id,)
            ).fetchone()

    def resolve_payment_request(self, request_id: int, status: str) -> None:
        with self._lock, self.conn:
            self.conn.execute(
                "UPDATE payment_requests SET status = ? WHERE id = ?", (status, request_id)
            )

    # --- Stats ------------------------------------------------------------------
    def stats(self) -> dict:
        with self._lock, self.conn:
            user_count = self.conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
            credit_sum = self.conn.execute(
                "SELECT COALESCE(SUM(credits), 0) c FROM users"
            ).fetchone()["c"]
            job_count = self.conn.execute("SELECT COUNT(*) c FROM jobs").fetchone()["c"]
            pending_payments = self.conn.execute(
                "SELECT COUNT(*) c FROM payment_requests WHERE status = 'pending'"
            ).fetchone()["c"]
        return {
            "users": user_count,
            "credits_outstanding": credit_sum,
            "jobs_processed": job_count,
            "pending_payments": pending_payments,
        }


# Single shared instance, imported by handlers/utils.
db = Database()
