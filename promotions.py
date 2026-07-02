"""Promotions — flash sales, coupons, percentage/fixed discounts."""
from __future__ import annotations
import db

PROMO_TYPES = {
    "percentage_off": {"icon": "🏷"},
    "fixed_off":      {"icon": "💴"},
    "flash_sale":     {"icon": "⚡"},
    "buy_x_get_y":    {"icon": "🎁"},
    "free_shipping":  {"icon": "🚚"},
    "bundle_deal":    {"icon": "📦"},
}

STATUSES = {
    "draft":  {"icon": "📝", "color": "#9a9485"},
    "active": {"icon": "✅", "color": "#4d6c5c"},
    "paused": {"icon": "⏸", "color": "#c5963d"},
    "ended":  {"icon": "⏹", "color": "#7a7569"},
}


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                promo_type      TEXT NOT NULL DEFAULT 'percentage_off',
                title           TEXT NOT NULL,
                discount_value  REAL DEFAULT 0,
                min_order_amount REAL DEFAULT 0,
                min_qty         INTEGER DEFAULT 1,
                max_uses        INTEGER DEFAULT 0,
                use_count       INTEGER DEFAULT 0,
                coupon_code     TEXT,
                sku_filter      TEXT,
                start_dt        TEXT,
                end_dt          TEXT,
                status          TEXT DEFAULT 'draft',
                notes           TEXT,
                created_at      TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def create(promo_type: str, title: str, discount_value: float = 0,
           min_order: float = 0, min_qty: int = 1, max_uses: int = 0,
           coupon_code: str = "", sku_filter: str = "",
           start_dt: str = "", end_dt: str = "", notes: str = "") -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO promotions (promo_type,title,discount_value,"
            "min_order_amount,min_qty,max_uses,coupon_code,sku_filter,"
            "start_dt,end_dt,notes,status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,'draft')",
            (promo_type, title, discount_value, min_order, min_qty,
             max_uses, coupon_code, sku_filter, start_dt, end_dt, notes),
        )
        return cur.lastrowid


def _set_status(promo_id: int, status: str) -> None:
    with db.conn() as c:
        c.execute("UPDATE promotions SET status=? WHERE id=?",
                  (status, promo_id))


def activate(promo_id: int) -> None:
    _set_status(promo_id, "active")


def pause(promo_id: int) -> None:
    _set_status(promo_id, "paused")


def end(promo_id: int) -> None:
    _set_status(promo_id, "ended")


def delete(promo_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM promotions WHERE id=? AND status='draft'",
                  (promo_id,))


def active_promos() -> list[dict]:
    with db.conn() as c:
        today = "date('now','localtime')"
        rows = c.execute(
            "SELECT * FROM promotions WHERE status='active' "
            "AND (start_dt='' OR date(start_dt)<=" + today + ") "
            "AND (end_dt='' OR date(end_dt)>=" + today + ") "
            "ORDER BY created_at DESC"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["promo_info"] = PROMO_TYPES.get(r["promo_type"], PROMO_TYPES["percentage_off"])
            d["status_info"] = STATUSES.get(r["status"], STATUSES["draft"])
            result.append(d)
        return result


def all_promos(status: str = None, limit: int = 50) -> list[dict]:
    with db.conn() as c:
        if status:
            rows = c.execute(
                "SELECT * FROM promotions WHERE status=? "
                "ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM promotions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["promo_info"] = PROMO_TYPES.get(r["promo_type"], PROMO_TYPES["percentage_off"])
            d["status_info"] = STATUSES.get(r["status"], STATUSES["draft"])
            result.append(d)
        return result


def apply_to_order(order_total: float, promo_id: int) -> dict:
    """Calculate discount for a given order total. Returns discount amount."""
    with db.conn() as c:
        row = c.execute(
            "SELECT * FROM promotions WHERE id=? AND status='active'",
            (promo_id,),
        ).fetchone()
        if not row:
            return {"discount": 0, "final": order_total, "error": "promo_not_found"}
        if row["min_order_amount"] and order_total < row["min_order_amount"]:
            min_str = "฿{:,.0f}".format(row["min_order_amount"])
            return {"discount": 0, "final": order_total,
                    "error": "min_order_" + min_str}
        if row["promo_type"] in ("percentage_off", "flash_sale"):
            discount = round(order_total * row["discount_value"] / 100, 2)
        elif row["promo_type"] == "fixed_off":
            discount = min(row["discount_value"], order_total)
        elif row["promo_type"] == "free_shipping":
            discount = 0
        else:
            discount = 0
        c.execute("UPDATE promotions SET use_count=use_count+1 WHERE id=?",
                  (promo_id,))
        return {
            "discount": discount,
            "final": round(order_total - discount, 2),
            "promo_type": row["promo_type"],
            "title": row["title"],
        }


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM promotions").fetchone()[0]
        active = c.execute(
            "SELECT COUNT(*) FROM promotions WHERE status='active'"
        ).fetchone()[0]
        total_uses = c.execute(
            "SELECT COALESCE(SUM(use_count),0) FROM promotions"
        ).fetchone()[0]
    return {"total": total, "active": active, "total_uses": total_uses}
