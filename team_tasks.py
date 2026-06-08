"""Team Tasks — assign and track small-team todo items."""
from __future__ import annotations
import db

PRIORITIES = {
    "low":    {"label": "ต่ำ", "color": "#9a9485", "icon": "⬇"},
    "normal": {"label": "ปกติ", "color": "#7a7569", "icon": "➡"},
    "high":   {"label": "สูง", "color": "#c5963d", "icon": "⬆"},
    "urgent": {"label": "ด่วน!", "color": "#c54c4c", "icon": "🔥"},
}

STATUSES = {
    "todo":        {"label": "รอทำ", "icon": "⬜", "color": "#9a9485"},
    "in_progress": {"label": "กำลังทำ", "icon": "🔄", "color": "#4a7ab5"},
    "done":        {"label": "เสร็จ", "icon": "✅", "color": "#4d6c5c"},
    "cancelled":   {"label": "ยกเลิก", "icon": "❌", "color": "#c54c4c"},
}

CATEGORIES = ["packing", "shipping", "customer_reply", "inventory",
               "content", "finance", "purchasing", "other"]


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL UNIQUE,
                role        TEXT DEFAULT '',
                active      INTEGER DEFAULT 1
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT DEFAULT '',
                category    TEXT DEFAULT 'other',
                priority    TEXT DEFAULT 'normal',
                status      TEXT DEFAULT 'todo',
                assignee_id INTEGER,
                due_date    TEXT,
                ref_key     TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                updated_at  TEXT DEFAULT (datetime('now','localtime')),
                done_at     TEXT,
                FOREIGN KEY (assignee_id) REFERENCES team_members(id)
            )
        """)


def add_member(name: str, role: str = "") -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT OR IGNORE INTO team_members (name,role) VALUES (?,?)",
            (name, role),
        )
        return cur.lastrowid or 0


def all_members() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM team_members WHERE active=1 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]


def add_task(title: str, description: str = "", category: str = "other",
             priority: str = "normal", assignee_id: int = None,
             due_date: str = "", ref_key: str = "") -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO tasks (title,description,category,priority,"
            "assignee_id,due_date,ref_key) VALUES (?,?,?,?,?,?,?)",
            (title, description, category, priority,
             assignee_id, due_date, ref_key),
        )
        return cur.lastrowid


def update_status(task_id: int, status: str) -> None:
    from datetime import datetime
    with db.conn() as c:
        done_at = datetime.now().strftime("%Y-%m-%d %H:%M") if status == "done" else None
        c.execute(
            "UPDATE tasks SET status=?,done_at=?,"
            "updated_at=datetime('now','localtime') WHERE id=?",
            (status, done_at, task_id),
        )


def assign(task_id: int, assignee_id: int) -> None:
    with db.conn() as c:
        c.execute("UPDATE tasks SET assignee_id=? WHERE id=?",
                  (assignee_id, task_id))


def delete(task_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM tasks WHERE id=?", (task_id,))


def all_tasks(status: str = None, assignee_id: int = None,
              limit: int = 100) -> list[dict]:
    with db.conn() as c:
        conditions = []
        params = []
        if status:
            conditions.append("t.status=?")
            params.append(status)
        if assignee_id:
            conditions.append("t.assignee_id=?")
            params.append(assignee_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = c.execute(
            "SELECT t.*, m.name assignee_name FROM tasks t "
            "LEFT JOIN team_members m ON t.assignee_id=m.id "
            + where +
            " ORDER BY CASE t.priority "
            "WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 "
            "WHEN 'normal' THEN 2 ELSE 3 END, t.created_at DESC LIMIT ?",
            params + [limit],
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["priority_info"] = PRIORITIES.get(r["priority"], PRIORITIES["normal"])
            d["status_info"] = STATUSES.get(r["status"], STATUSES["todo"])
            result.append(d)
        return result


def overdue() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT t.*, m.name assignee_name FROM tasks t "
            "LEFT JOIN team_members m ON t.assignee_id=m.id "
            "WHERE t.status NOT IN ('done','cancelled') "
            "AND t.due_date != '' "
            "AND date(t.due_date) < date('now','localtime') "
            "ORDER BY t.due_date"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["priority_info"] = PRIORITIES.get(r["priority"], PRIORITIES["normal"])
            d["status_info"] = STATUSES.get(r["status"], STATUSES["todo"])
            result.append(d)
        return result


def stats() -> dict:
    with db.conn() as c:
        total = c.execute(
            "SELECT COUNT(*) FROM tasks WHERE status NOT IN ('done','cancelled')"
        ).fetchone()[0]
        urgent = c.execute(
            "SELECT COUNT(*) FROM tasks "
            "WHERE priority='urgent' AND status NOT IN ('done','cancelled')"
        ).fetchone()[0]
        done_today = c.execute(
            "SELECT COUNT(*) FROM tasks "
            "WHERE status='done' AND date(done_at)=date('now','localtime')"
        ).fetchone()[0]
        overdue_count = len(overdue())
    return {
        "total_open": total,
        "urgent": urgent,
        "done_today": done_today,
        "overdue": overdue_count,
    }
