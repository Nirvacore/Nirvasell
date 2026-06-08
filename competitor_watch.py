"""Competitor Price Watch — track rival prices manually.

No API needed. Seller enters competitor prices for their SKUs.
System shows: are you cheaper or more expensive? By how much?
Alerts when a competitor undercuts you."""
from __future__ import annotations

from datetime import datetime

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS competitor_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                competitor TEXT NOT NULL,
                platform TEXT DEFAULT '',
                price REAL NOT NULL,
                url TEXT DEFAULT '',
                note TEXT DEFAULT '',
                recorded_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def add(sku: str, competitor: str, price: float,
        platform: str = "", url: str = "", note: str = "") -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO competitor_prices "
            "(sku, competitor, platform, price, url, note) "
            "VALUES (?,?,?,?,?,?)",
            (sku, competitor, platform, price, url, note),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def delete(entry_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM competitor_prices WHERE id=?", (entry_id,))


def for_sku(sku: str) -> list[dict]:
    """Get all competitor prices for a SKU, newest first."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM competitor_prices WHERE sku=? "
            "ORDER BY recorded_at DESC",
            (sku,),
        ).fetchall()
    return [dict(r) for r in rows]


def comparison() -> list[dict]:
    """Compare your prices vs competitors across all tracked SKUs."""
    with db.conn() as c:
        # Get latest competitor price per SKU per competitor
        rows = c.execute("""
            SELECT cp.sku, cp.competitor, cp.platform, cp.price, cp.recorded_at,
                   p.name, p.sell_price AS my_price
            FROM competitor_prices cp
            LEFT JOIN products p ON p.sku = cp.sku
            WHERE cp.id IN (
                SELECT MAX(id) FROM competitor_prices
                GROUP BY sku, competitor
            )
            ORDER BY cp.sku, cp.price
        """).fetchall()

    items = []
    for r in rows:
        d = dict(r)
        my = d.get("my_price") or 0
        their = d.get("price") or 0

        if my > 0 and their > 0:
            diff = my - their
            diff_pct = round(diff / their * 100, 1)
            d["diff"] = diff
            d["diff_pct"] = diff_pct
            d["position"] = "cheaper" if diff < 0 else ("same" if diff == 0 else "more_expensive")
        else:
            d["diff"] = 0
            d["diff_pct"] = 0
            d["position"] = "unknown"

        items.append(d)

    return items


def undercut_alerts() -> list[dict]:
    """SKUs where at least one competitor is cheaper than you."""
    return [c for c in comparison() if c["position"] == "more_expensive"]


def all_competitors() -> list[str]:
    """List all unique competitor names."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT DISTINCT competitor FROM competitor_prices ORDER BY competitor"
        ).fetchall()
    return [r["competitor"] for r in rows]


def tracked_skus() -> list[str]:
    """List all SKUs being tracked."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT DISTINCT sku FROM competitor_prices ORDER BY sku"
        ).fetchall()
    return [r["sku"] for r in rows]


def stats() -> dict:
    comp = comparison()
    cheaper = sum(1 for c in comp if c["position"] == "cheaper")
    same = sum(1 for c in comp if c["position"] == "same")
    more_exp = sum(1 for c in comp if c["position"] == "more_expensive")

    return {
        "tracked_skus": len(tracked_skus()),
        "competitors": len(all_competitors()),
        "total_entries": len(comp),
        "cheaper": cheaper,
        "same": same,
        "more_expensive": more_exp,
    }
