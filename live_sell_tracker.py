"""Live Sell Tracker — track what sold during Facebook/TikTok live sessions.

During a live, orders come fast. Log each sale, track totals,
see which products performed, compare sessions."""
from __future__ import annotations
from datetime import datetime
import db


PLATFORMS = ["facebook", "tiktok", "instagram", "shopee_live", "lazada_live",
             "youtube", "other"]


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS live_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                platform TEXT DEFAULT 'facebook',
                started_at TEXT,
                ended_at TEXT,
                status TEXT DEFAULT 'planned',
                viewers_peak INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS live_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER REFERENCES live_sessions(id) ON DELETE CASCADE,
                sku TEXT,
                product_name TEXT,
                qty INTEGER DEFAULT 1,
                unit_price REAL DEFAULT 0,
                buyer_name TEXT,
                ordered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                notes TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_lo_session
                ON live_orders(session_id);
        """)


def create_session(title: str, platform: str = "facebook",
                   started_at: str = None, notes: str = "") -> int:
    ts = started_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db.conn() as c:
        c.execute("""
            INSERT INTO live_sessions (title, platform, started_at, status, notes)
            VALUES (?, ?, ?, 'live', ?)
        """, (title, platform, ts, notes))
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def end_session(session_id: int, viewers_peak: int = 0) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db.conn() as c:
        c.execute("""
            UPDATE live_sessions
            SET status = 'ended', ended_at = ?, viewers_peak = ?
            WHERE id = ?
        """, (now, viewers_peak, session_id))


def add_order(session_id: int, sku: str, qty: int = 1,
              unit_price: float = 0, buyer_name: str = "",
              notes: str = "") -> int:
    product_name = ""
    with db.conn() as c:
        prod = c.execute(
            "SELECT name, sell_price FROM products WHERE sku = ?", (sku,)
        ).fetchone()
        if prod:
            product_name = prod["name"] or ""
            if unit_price == 0:
                unit_price = prod["sell_price"] or 0

        c.execute("""
            INSERT INTO live_orders
                (session_id, sku, product_name, qty, unit_price, buyer_name, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, sku, product_name, qty, unit_price, buyer_name, notes))
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def remove_order(order_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM live_orders WHERE id = ?", (order_id,))


def session_summary(session_id: int) -> dict:
    with db.conn() as c:
        sess = c.execute(
            "SELECT * FROM live_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not sess:
            return {}

        orders = c.execute("""
            SELECT lo.*, (lo.qty * lo.unit_price) AS line_total
            FROM live_orders lo
            WHERE lo.session_id = ?
            ORDER BY lo.ordered_at DESC
        """, (session_id,)).fetchall()

        sku_totals = c.execute("""
            SELECT sku, product_name,
                   SUM(qty) AS total_qty,
                   SUM(qty * unit_price) AS total_revenue
            FROM live_orders WHERE session_id = ?
            GROUP BY sku ORDER BY total_revenue DESC
        """, (session_id,)).fetchall()

    order_list = [dict(o) for o in orders]
    total_revenue = sum(o["line_total"] for o in order_list)
    total_qty = sum(o["qty"] for o in order_list)

    started = sess["started_at"] or ""
    ended = sess["ended_at"] or ""
    duration_min = 0
    if started and ended:
        try:
            s = datetime.strptime(started[:19], "%Y-%m-%d %H:%M:%S")
            e = datetime.strptime(ended[:19], "%Y-%m-%d %H:%M:%S")
            duration_min = int((e - s).total_seconds() / 60)
        except Exception:
            pass

    return {
        "id": sess["id"],
        "title": sess["title"],
        "platform": sess["platform"],
        "status": sess["status"],
        "started_at": started,
        "ended_at": ended,
        "duration_min": duration_min,
        "viewers_peak": sess["viewers_peak"],
        "orders": order_list,
        "total_orders": len(order_list),
        "total_qty": total_qty,
        "total_revenue": round(total_revenue, 2),
        "avg_order_value": round(total_revenue / len(order_list), 0) if order_list else 0,
        "top_skus": [dict(s) for s in sku_totals],
    }


def active_sessions() -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT ls.*, COUNT(lo.id) AS order_count,
                   COALESCE(SUM(lo.qty * lo.unit_price), 0) AS revenue
            FROM live_sessions ls
            LEFT JOIN live_orders lo ON ls.id = lo.session_id
            WHERE ls.status = 'live'
            GROUP BY ls.id ORDER BY ls.started_at DESC
        """).fetchall()
    return [dict(r) for r in rows]


def all_sessions(limit: int = 20) -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT ls.*, COUNT(lo.id) AS order_count,
                   COALESCE(SUM(lo.qty * lo.unit_price), 0) AS revenue
            FROM live_sessions ls
            LEFT JOIN live_orders lo ON ls.id = lo.session_id
            GROUP BY ls.id ORDER BY ls.created_at DESC LIMIT ?
        """, (limit,)).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item["status_icon"] = {"live": "🔴", "ended": "✅",
                                "planned": "📋"}.get(r["status"], "?")
        result.append(item)
    return result


def stats() -> dict:
    with db.conn() as c:
        sessions = c.execute("SELECT COUNT(*) FROM live_sessions").fetchone()[0]
        live_now = c.execute(
            "SELECT COUNT(*) FROM live_sessions WHERE status = 'live'"
        ).fetchone()[0]
        total_revenue = c.execute("""
            SELECT COALESCE(SUM(lo.qty * lo.unit_price), 0)
            FROM live_orders lo
        """).fetchone()[0]
        best = c.execute("""
            SELECT ls.title, SUM(lo.qty * lo.unit_price) AS rev
            FROM live_sessions ls
            JOIN live_orders lo ON ls.id = lo.session_id
            GROUP BY ls.id ORDER BY rev DESC LIMIT 1
        """).fetchone()
    return {
        "total_sessions": sessions,
        "live_now": live_now,
        "total_revenue": round(total_revenue, 2),
        "best_session": best["title"] if best else None,
        "best_revenue": round(best["rev"], 0) if best else 0,
    }
