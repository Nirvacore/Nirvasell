"""Per-email login rate limiter — prevents brute-force password guessing.

Default: 5 failed attempts within 15 minutes locks the account for the rest
of that window. Successful login clears the counter.

Stored in the shared accounts.db so all login attempts (across sessions and
sub-processes) hit the same counter.
"""
from __future__ import annotations
import sqlite3
import time

import auth


_SCHEMA = """
CREATE TABLE IF NOT EXISTS login_attempts (
    email TEXT PRIMARY KEY,
    failures INTEGER NOT NULL DEFAULT 0,
    window_started_at REAL NOT NULL,
    locked_until REAL
);
"""

# Tunables — sane defaults; if you ever want to relax these, move to env.
WINDOW_SECONDS = 15 * 60
MAX_FAILURES = 5
LOCK_SECONDS = 15 * 60


def _conn():
    auth.init()
    p = auth.DATA / "accounts.db"
    c = sqlite3.connect(str(p))
    c.row_factory = sqlite3.Row
    return c


def init():
    c = _conn()
    try:
        c.executescript(_SCHEMA)
        c.commit()
    finally:
        c.close()


def check(email: str) -> tuple[bool, int]:
    """Returns (allowed, retry_in_seconds). Call BEFORE attempting login —
    skip the password compare if not allowed."""
    if not email:
        return True, 0
    init()
    c = _conn()
    try:
        row = c.execute(
            "SELECT failures, window_started_at, locked_until FROM login_attempts WHERE email = ?",
            (email.lower(),),
        ).fetchone()
        now = time.time()
        if not row:
            return True, 0
        # Locked window still active?
        if row["locked_until"] and float(row["locked_until"]) > now:
            return False, int(float(row["locked_until"]) - now)
        # Window expired → counter resets next failure call
        return True, 0
    finally:
        c.close()


def record_failure(email: str) -> tuple[bool, int]:
    """Bump the counter. Returns (still_allowed, retry_in_seconds_if_locked)."""
    if not email:
        return True, 0
    init()
    now = time.time()
    c = _conn()
    try:
        row = c.execute(
            "SELECT failures, window_started_at, locked_until FROM login_attempts WHERE email = ?",
            (email.lower(),),
        ).fetchone()
        if row and (now - float(row["window_started_at"])) < WINDOW_SECONDS:
            failures = int(row["failures"]) + 1
            window_started_at = float(row["window_started_at"])
        else:
            # New window
            failures = 1
            window_started_at = now

        locked_until = None
        still_allowed = True
        retry = 0
        if failures >= MAX_FAILURES:
            locked_until = now + LOCK_SECONDS
            still_allowed = False
            retry = LOCK_SECONDS

        c.execute(
            """INSERT INTO login_attempts (email, failures, window_started_at, locked_until)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(email) DO UPDATE SET
                 failures = excluded.failures,
                 window_started_at = excluded.window_started_at,
                 locked_until = excluded.locked_until""",
            (email.lower(), failures, window_started_at, locked_until),
        )
        c.commit()
        return still_allowed, retry
    finally:
        c.close()


def clear(email: str) -> None:
    """Wipe the counter — call this after a SUCCESSFUL login."""
    if not email:
        return
    init()
    c = _conn()
    try:
        c.execute("DELETE FROM login_attempts WHERE email = ?", (email.lower(),))
        c.commit()
    finally:
        c.close()


def stats(email: str) -> dict:
    """Diagnostic: how many failures, how long until unlock."""
    init()
    c = _conn()
    try:
        row = c.execute(
            "SELECT failures, locked_until FROM login_attempts WHERE email = ?",
            (email.lower(),),
        ).fetchone()
        if not row:
            return {"failures": 0, "remaining": MAX_FAILURES, "locked": False}
        now = time.time()
        locked = bool(row["locked_until"] and float(row["locked_until"]) > now)
        return {
            "failures": int(row["failures"]),
            "remaining": max(0, MAX_FAILURES - int(row["failures"])),
            "locked": locked,
            "unlock_in": int(float(row["locked_until"]) - now) if locked else 0,
        }
    finally:
        c.close()
