"""Unified event log — everything that happens in the platform writes here,
so the Alerts page can show a single chronological "Slack-channel for your
shop" feed.

Examples of what flows through:
  • New order imported from Shopee/Lazada/TikTok
  • AI generation errored / hit rate limit
  • Policy diff detected (Shopee fee change, etc.)
  • Donation received (PromptPay / Stripe)
  • New user signup (admin sees this)
  • Compliance flag (listing failed pre-flight)
  • Stock dropped to zero on a SKU

Each event has: category (filterable), severity (info/warn/error/success),
title, body, target page (where to go to act on it), and read state.

Storage: per-user `events` table in SQLite. Read-only after write — events
are immutable, only the `read_at` flag changes."""
from __future__ import annotations
import json
from typing import Any

import db


SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL,
    severity    TEXT NOT NULL DEFAULT 'info',
    title       TEXT NOT NULL,
    body        TEXT,
    target_page TEXT,
    meta        TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    read_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_unread  ON events(read_at) WHERE read_at IS NULL;
"""


CATEGORIES = ("order", "ai", "policy", "compliance", "payment", "stock",
              "user", "system")
SEVERITIES = ("info", "success", "warn", "error")


def init():
    with db.conn() as c:
        c.executescript(SCHEMA)


# ---- Write ---------------------------------------------------------------

def log(*, category: str, title: str, body: str = "",
        severity: str = "info", target_page: str = "",
        meta: dict | None = None) -> int | None:
    """Append an event. NEVER raises — silent failure is preferred to
    crashing the calling code path."""
    try:
        init()
        cat = category if category in CATEGORIES else "system"
        sev = severity if severity in SEVERITIES else "info"
        meta_json = json.dumps(meta or {}, ensure_ascii=False)[:1000]
        with db.conn() as c:
            cur = c.execute(
                """INSERT INTO events (category, severity, title, body,
                                       target_page, meta)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (cat, sev, title[:200], body[:1000], target_page, meta_json),
            )
            return cur.lastrowid
    except Exception:
        return None


# ---- Read ---------------------------------------------------------------

def recent(limit: int = 50, category: str | None = None,
           unread_only: bool = False) -> list[dict]:
    init()
    where, params = [], []
    if category and category != "all":
        where.append("category = ?")
        params.append(category)
    if unread_only:
        where.append("read_at IS NULL")
    sql = "SELECT * FROM events"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with db.conn() as c:
        rows = c.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def unread_count(category: str | None = None) -> int:
    init()
    sql = "SELECT COUNT(*) FROM events WHERE read_at IS NULL"
    params: tuple = ()
    if category and category != "all":
        sql += " AND category = ?"
        params = (category,)
    with db.conn() as c:
        return int(c.execute(sql, params).fetchone()[0])


def category_counts() -> dict[str, int]:
    """{category: unread_count} for the filter chips."""
    init()
    out = {c: 0 for c in CATEGORIES}
    with db.conn() as c:
        rows = c.execute(
            "SELECT category, COUNT(*) FROM events "
            "WHERE read_at IS NULL GROUP BY category"
        ).fetchall()
    for r in rows:
        out[r[0]] = int(r[1])
    return out


def mark_read(event_id: int) -> None:
    init()
    with db.conn() as c:
        c.execute(
            "UPDATE events SET read_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND read_at IS NULL", (event_id,),
        )


def mark_all_read(category: str | None = None) -> int:
    init()
    sql = "UPDATE events SET read_at = CURRENT_TIMESTAMP WHERE read_at IS NULL"
    params: tuple = ()
    if category and category != "all":
        sql += " AND category = ?"
        params = (category,)
    with db.conn() as c:
        cur = c.execute(sql, params)
        return cur.rowcount


def clear_older_than(days: int = 90) -> int:
    """Housekeeping — prune ancient events (read or not). Called by cron."""
    init()
    with db.conn() as c:
        cur = c.execute(
            f"DELETE FROM events WHERE created_at < date('now', '-{int(days)} days')"
        )
        return cur.rowcount


def _row_to_dict(row) -> dict:
    d = dict(row)
    if d.get("meta"):
        try:
            d["meta"] = json.loads(d["meta"])
        except Exception:
            d["meta"] = {}
    return d


# ---- Severity / category UI mappings -----------------------------------

SEVERITY_ICONS = {
    "info":    "ℹ️",
    "success": "✅",
    "warn":    "⚠",
    "error":   "🔴",
}

CATEGORY_ICONS = {
    "order":      "📦",
    "ai":         "🤖",
    "policy":     "📋",
    "compliance": "⚖",
    "payment":    "💰",
    "stock":      "📊",
    "user":       "👤",
    "system":     "⚙",
}
