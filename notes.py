"""Operational Notes — quick memos attached to SKUs, orders, or free-form."""
from __future__ import annotations
import db

NOTE_TYPES = {
    "sku":      {"label": "SKU", "icon": "📦"},
    "order":    {"label": "ออเดอร์", "icon": "🛒"},
    "customer": {"label": "ลูกค้า", "icon": "👤"},
    "supplier": {"label": "ซัพพลายเออร์", "icon": "🏭"},
    "general":  {"label": "ทั่วไป", "icon": "📝"},
}

PRIORITIES = {
    "normal": {"label": "ปกติ", "color": "#9a9485"},
    "important": {"label": "สำคัญ", "color": "#c5963d"},
    "urgent": {"label": "ด่วน!", "color": "#c54c4c"},
}


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                note_type   TEXT DEFAULT 'general',
                ref_key     TEXT DEFAULT '',
                title       TEXT NOT NULL,
                body        TEXT DEFAULT '',
                priority    TEXT DEFAULT 'normal',
                pinned      INTEGER DEFAULT 0,
                resolved    INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                updated_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def add(title: str, body: str = "", note_type: str = "general",
        ref_key: str = "", priority: str = "normal",
        pinned: bool = False) -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO notes (title,body,note_type,ref_key,priority,pinned) "
            "VALUES (?,?,?,?,?,?)",
            (title, body, note_type, ref_key, priority, int(pinned)),
        )
        return cur.lastrowid


def update(note_id: int, title: str = None, body: str = None,
           priority: str = None, pinned: bool = None) -> None:
    with db.conn() as c:
        if title is not None:
            c.execute("UPDATE notes SET title=?,updated_at=datetime('now','localtime') "
                      "WHERE id=?", (title, note_id))
        if body is not None:
            c.execute("UPDATE notes SET body=?,updated_at=datetime('now','localtime') "
                      "WHERE id=?", (body, note_id))
        if priority is not None:
            c.execute("UPDATE notes SET priority=? WHERE id=?",
                      (priority, note_id))
        if pinned is not None:
            c.execute("UPDATE notes SET pinned=? WHERE id=?",
                      (int(pinned), note_id))


def resolve(note_id: int) -> None:
    with db.conn() as c:
        c.execute("UPDATE notes SET resolved=1,"
                  "updated_at=datetime('now','localtime') WHERE id=?",
                  (note_id,))


def delete(note_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM notes WHERE id=?", (note_id,))


def all_notes(note_type: str = None, ref_key: str = None,
              include_resolved: bool = False,
              limit: int = 100) -> list[dict]:
    with db.conn() as c:
        conditions = []
        params = []
        if not include_resolved:
            conditions.append("resolved=0")
        if note_type:
            conditions.append("note_type=?")
            params.append(note_type)
        if ref_key:
            conditions.append("ref_key=?")
            params.append(ref_key)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = c.execute(
            "SELECT * FROM notes " + where +
            " ORDER BY pinned DESC, priority DESC, created_at DESC LIMIT ?",
            params + [limit],
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["type_info"] = NOTE_TYPES.get(r["note_type"], NOTE_TYPES["general"])
            d["priority_info"] = PRIORITIES.get(r["priority"], PRIORITIES["normal"])
            result.append(d)
        return result


def pinned() -> list[dict]:
    return all_notes(include_resolved=False, limit=10)


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM notes WHERE resolved=0").fetchone()[0]
        urgent = c.execute(
            "SELECT COUNT(*) FROM notes WHERE priority='urgent' AND resolved=0"
        ).fetchone()[0]
        pinned_count = c.execute(
            "SELECT COUNT(*) FROM notes WHERE pinned=1 AND resolved=0"
        ).fetchone()[0]
    return {"total": total, "urgent": urgent, "pinned": pinned_count}
