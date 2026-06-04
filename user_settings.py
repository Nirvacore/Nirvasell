"""Per-user persistent settings. Stored in the user's own SQLite — survives
session refreshes so users don't re-type their Anthropic key every login.

Settings are key/value JSON pairs, free-form. We define a few well-known keys:
  • anthropic_api_key
  • cloudinary_*
  • notify_prefs (which events fire which channel kinds)
  • markup_percent, round_to, currency, target_lang, ...

Security note: stored in plaintext within the user's per-user DB file. The
DB is per-tenant (data/users/{id}.db) and only readable by the OS user who
runs nirva.sell. For SaaS hosting, the DB should sit on encrypted disk.
"""
from __future__ import annotations
import json

import db


SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init():
    with db.conn() as c:
        c.executescript(SCHEMA)


def get(key: str, default=None):
    init()
    with db.conn() as c:
        row = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    raw = row["value"]
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def set(key: str, value) -> None:
    init()
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    with db.conn() as c:
        c.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
            (key, value),
        )


def delete(key: str) -> None:
    init()
    with db.conn() as c:
        c.execute("DELETE FROM settings WHERE key = ?", (key,))


def all_settings() -> dict:
    init()
    with db.conn() as c:
        rows = c.execute("SELECT key, value FROM settings").fetchall()
    out = {}
    for r in rows:
        try:
            out[r["key"]] = json.loads(r["value"])
        except Exception:
            out[r["key"]] = r["value"]
    return out


# ---- Notification preferences -------------------------------------------

DEFAULT_NOTIFY_PREFS = {
    "batch_done":    True,    # AI batch generation completes
    "policy_change": True,    # marketplace policy fee/rule changes
    "review_block":  True,    # AI Review finds blockers in a listing
    "low_stock":     False,   # supplier stock below threshold
    "import_done":   False,   # CSV / order import done
}


def notify_prefs() -> dict:
    saved = get("notify_prefs", DEFAULT_NOTIFY_PREFS)
    return {**DEFAULT_NOTIFY_PREFS, **(saved if isinstance(saved, dict) else {})}


def set_notify_prefs(prefs: dict) -> None:
    set("notify_prefs", {**DEFAULT_NOTIFY_PREFS, **prefs})
