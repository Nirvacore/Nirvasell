"""Flash Sale Scheduler — time-limited sales with auto-status."""
from __future__ import annotations
from datetime import datetime
import db

STATUSES = {
    "draft":    {"label": "ร่าง", "icon": "📝", "color": "#9a9485"},
    "upcoming": {"label": "กำลังจะมาถึง", "icon": "⏰", "color": "#4a7ab5"},
    "active":   {"label": "กำลังดำเนินการ!", "icon": "🔥", "color": "#c54c4c"},
    "ended":    {"label": "สิ้นสุด", "icon": "✓", "color": "#4d6c5c"},
    "cancelled":{"label": "ยกเลิก", "icon": "✕", "color": "#4a4a4a"},
}

DISCOUNT_TYPES = {
    "percentage": "ลดเปอร์เซ็นต์",
    "fixed":      "ลดเป็นบาท",
    "free_shipping": "ส่งฟรี",
}


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS flash_sales (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                title           TEXT NOT NULL,
                discount_type   TEXT DEFAULT 'percentage',
                discount_value  REAL DEFAULT 10.0,
                min_order       REAL DEFAULT 0,
                max_uses        INTEGER DEFAULT 0,
                current_uses    INTEGER DEFAULT 0,
                platform        TEXT DEFAULT 'all',
                sku_filter      TEXT DEFAULT '',
                start_dt        TEXT NOT NULL,
                end_dt          TEXT NOT NULL,
                status          TEXT DEFAULT 'draft',
                notes           TEXT DEFAULT '',
                created_at      TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def _compute_status(start_dt: str, end_dt: str, stored_status: str) -> str:
    if stored_status in ("cancelled", "draft"):
        return stored_status
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if now < start_dt:
        return "upcoming"
    if now > end_dt:
        return "ended"
    return "active"


def create(title: str, discount_type: str = "percentage",
           discount_value: float = 10.0, min_order: float = 0,
           max_uses: int = 0, platform: str = "all",
           sku_filter: str = "", start_dt: str = "",
           end_dt: str = "", notes: str = "") -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO flash_sales (title,discount_type,discount_value,"
            "min_order,max_uses,platform,sku_filter,start_dt,end_dt,notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (title, discount_type, discount_value, min_order,
             max_uses, platform, sku_filter, start_dt, end_dt, notes),
        )
        return cur.lastrowid


def cancel(sale_id: int) -> None:
    with db.conn() as c:
        c.execute("UPDATE flash_sales SET status='cancelled' WHERE id=?", (sale_id,))


def delete(sale_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM flash_sales WHERE id=?", (sale_id,))


def record_use(sale_id: int) -> None:
    with db.conn() as c:
        c.execute(
            "UPDATE flash_sales SET current_uses=current_uses+1 WHERE id=?",
            (sale_id,),
        )


def all_sales(status_filter: str = None, limit: int = 50) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM flash_sales ORDER BY start_dt DESC LIMIT ?",
            (limit,),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            real_status = _compute_status(
                r["start_dt"], r["end_dt"], r["status"]
            )
            d["real_status"] = real_status
            d["status_info"] = STATUSES.get(real_status, STATUSES["draft"])
            if status_filter and real_status != status_filter:
                continue
            # Time remaining
            try:
                end = datetime.strptime(r["end_dt"], "%Y-%m-%d %H:%M")
                delta = end - datetime.now()
                if delta.total_seconds() > 0:
                    h = int(delta.total_seconds() // 3600)
                    m = int((delta.total_seconds() % 3600) // 60)
                    d["time_remaining"] = str(h) + "h " + str(m) + "m"
                else:
                    d["time_remaining"] = "สิ้นสุด"
            except Exception:
                d["time_remaining"] = "—"
            result.append(d)
        return result


def active_now() -> list[dict]:
    return [s for s in all_sales() if s["real_status"] == "active"]


def stats() -> dict:
    all_s = all_sales()
    active = [s for s in all_s if s["real_status"] == "active"]
    upcoming = [s for s in all_s if s["real_status"] == "upcoming"]
    return {
        "total": len(all_s),
        "active": len(active),
        "upcoming": len(upcoming),
        "active_titles": [s["title"] for s in active],
    }
