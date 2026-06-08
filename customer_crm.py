"""Customer CRM — notes, tags, interaction history per customer.

Thai sellers remember regulars by feel. This makes it systematic:
tag VIPs, note preferences, track last contact, set follow-up dates."""
from __future__ import annotations

from datetime import datetime

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS customer_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_key TEXT NOT NULL,
                note TEXT NOT NULL,
                note_type TEXT DEFAULT 'general',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS customer_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_key TEXT NOT NULL,
                tag TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(customer_key, tag)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS customer_followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_key TEXT NOT NULL,
                followup_date TEXT NOT NULL,
                reason TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


NOTE_TYPES = {
    "general":    {"label": "ทั่วไป",      "icon": "📝"},
    "preference": {"label": "ความชอบ",     "icon": "❤️"},
    "complaint":  {"label": "ร้องเรียน",    "icon": "⚠️"},
    "feedback":   {"label": "ฟีดแบ็ค",     "icon": "💬"},
    "vip":        {"label": "VIP",         "icon": "💎"},
}

DEFAULT_TAGS = [
    "VIP", "ซื้อประจำ", "ชอบของแถม", "ชอบส่งด่วน", "ขอใบกำกับ",
    "ระวังเรื่องสี", "ส่งรีวิวดี", "เคยร้องเรียน", "รอติดตาม",
]


def add_note(customer_key: str, note: str, note_type: str = "general") -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO customer_notes (customer_key, note, note_type) VALUES (?,?,?)",
            (customer_key, note, note_type),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def delete_note(note_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM customer_notes WHERE id=?", (note_id,))


def notes_for(customer_key: str) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM customer_notes WHERE customer_key=? ORDER BY created_at DESC",
            (customer_key,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_tag(customer_key: str, tag: str):
    with db.conn() as c:
        try:
            c.execute(
                "INSERT OR IGNORE INTO customer_tags (customer_key, tag) VALUES (?,?)",
                (customer_key, tag),
            )
        except Exception:
            pass


def remove_tag(customer_key: str, tag: str):
    with db.conn() as c:
        c.execute(
            "DELETE FROM customer_tags WHERE customer_key=? AND tag=?",
            (customer_key, tag),
        )


def tags_for(customer_key: str) -> list[str]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT tag FROM customer_tags WHERE customer_key=? ORDER BY tag",
            (customer_key,),
        ).fetchall()
    return [r["tag"] for r in rows]


def add_followup(customer_key: str, followup_date: str, reason: str = "") -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO customer_followups (customer_key, followup_date, reason) VALUES (?,?,?)",
            (customer_key, followup_date, reason),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def complete_followup(followup_id: int):
    with db.conn() as c:
        c.execute(
            "UPDATE customer_followups SET status='done' WHERE id=?",
            (followup_id,),
        )


def pending_followups() -> list[dict]:
    with db.conn() as c:
        rows = c.execute("""
            SELECT * FROM customer_followups
            WHERE status='pending' AND followup_date <= date('now','localtime','+7 day')
            ORDER BY followup_date
        """).fetchall()
    return [dict(r) for r in rows]


def customer_profile(customer_key: str) -> dict:
    """Full profile: orders, notes, tags, followups."""
    notes = notes_for(customer_key)
    tags = tags_for(customer_key)
    followups_list = []
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM customer_followups WHERE customer_key=? ORDER BY followup_date DESC",
            (customer_key,),
        ).fetchall()
        followups_list = [dict(r) for r in rows]

        # Order stats
        orders = c.execute("""
            SELECT COUNT(*) AS cnt, COALESCE(SUM(total_amount), 0) AS total,
                   MAX(order_date) AS last_order
            FROM orders WHERE COALESCE(buyer_phone, buyer_name) = ?
        """, (customer_key,)).fetchone()

    return {
        "customer_key": customer_key,
        "orders": orders["cnt"] if orders else 0,
        "total_spent": orders["total"] if orders else 0,
        "last_order": orders["last_order"] if orders else None,
        "notes": notes,
        "tags": tags,
        "followups": followups_list,
    }


def all_customers_with_data() -> list[dict]:
    """List customers that have any CRM data (notes, tags, or followups)."""
    with db.conn() as c:
        keys = set()
        for table in ("customer_notes", "customer_tags", "customer_followups"):
            rows = c.execute(
                "SELECT DISTINCT customer_key FROM " + table
            ).fetchall()
            for r in rows:
                keys.add(r["customer_key"])

    return [customer_profile(k) for k in sorted(keys)]


def stats() -> dict:
    with db.conn() as c:
        notes_count = c.execute("SELECT COUNT(*) FROM customer_notes").fetchone()[0]
        tags_count = c.execute("SELECT COUNT(*) FROM customer_tags").fetchone()[0]
        followups_pending = c.execute(
            "SELECT COUNT(*) FROM customer_followups WHERE status='pending'"
        ).fetchone()[0]
        customers_with_data = c.execute(
            "SELECT COUNT(DISTINCT customer_key) FROM customer_notes"
        ).fetchone()[0]

    return {
        "notes": notes_count,
        "tags": tags_count,
        "followups_pending": followups_pending,
        "customers_tracked": customers_with_data,
    }
