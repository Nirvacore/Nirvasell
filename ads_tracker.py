"""Ads ROI Tracker — know which campaigns make money.

Thai sellers spend on Facebook Ads, TikTok Ads, Shopee Ads, Lazada
Sponsored — but rarely track ROAS. This module connects ad spend to
actual revenue to show true return on every baht spent."""
from __future__ import annotations

from datetime import datetime, date

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS ad_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT DEFAULT '',
                start_date TEXT DEFAULT (date('now','localtime')),
                end_date TEXT,
                budget REAL DEFAULT 0,
                spent REAL DEFAULT 0,
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                orders INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


AD_PLATFORMS = ["facebook", "tiktok", "shopee_ads", "lazada_ads", "google", "instagram", "line", "other"]

PLATFORM_ICONS = {
    "facebook": "📘", "tiktok": "🎵", "shopee_ads": "🛒",
    "lazada_ads": "🟧", "google": "🔍", "instagram": "📸",
    "line": "💚", "other": "📣",
}


def add(name: str, platform: str, budget: float = 0,
        spent: float = 0, note: str = "", **kwargs) -> int:
    cols = ["name", "platform", "budget", "spent", "note"]
    vals = [name, platform, budget, spent, note]
    for k in ("impressions", "clicks", "orders", "revenue",
              "start_date", "end_date", "status"):
        if k in kwargs and kwargs[k] is not None:
            cols.append(k)
            vals.append(kwargs[k])
    placeholders = ",".join("?" * len(vals))
    col_str = ",".join(cols)
    with db.conn() as c:
        c.execute(
            "INSERT INTO ad_campaigns (" + col_str + ") VALUES (" + placeholders + ")",
            vals,
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def update(ad_id: int, **kwargs):
    sets = []
    vals = []
    for k in ("name", "platform", "budget", "spent", "impressions",
              "clicks", "orders", "revenue", "status", "start_date",
              "end_date", "note"):
        if k in kwargs:
            sets.append(k + "=?")
            vals.append(kwargs[k])
    if not sets:
        return
    vals.append(ad_id)
    with db.conn() as c:
        c.execute(
            "UPDATE ad_campaigns SET " + ",".join(sets) + " WHERE id=?",
            vals,
        )


def delete(ad_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM ad_campaigns WHERE id=?", (ad_id,))


def all_campaigns(status: str | None = None) -> list[dict]:
    with db.conn() as c:
        if status:
            rows = c.execute(
                "SELECT * FROM ad_campaigns WHERE status=? "
                "ORDER BY created_at DESC", (status,),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM ad_campaigns ORDER BY created_at DESC"
            ).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        spent = float(d.get("spent") or 0)
        revenue = float(d.get("revenue") or 0)
        clicks = int(d.get("clicks") or 0)
        impressions = int(d.get("impressions") or 0)
        orders = int(d.get("orders") or 0)
        d["roas"] = round(revenue / spent, 2) if spent > 0 else 0
        d["profit"] = round(revenue - spent, 2)
        d["cpc"] = round(spent / clicks, 2) if clicks > 0 else 0
        d["ctr"] = round(clicks / impressions * 100, 2) if impressions > 0 else 0
        d["conv_rate"] = round(orders / clicks * 100, 2) if clicks > 0 else 0
        d["cpa"] = round(spent / orders, 2) if orders > 0 else 0
        results.append(d)
    return results


def stats() -> dict:
    with db.conn() as c:
        r = c.execute(
            "SELECT COUNT(*) as total, "
            "COALESCE(SUM(spent),0) as total_spent, "
            "COALESCE(SUM(revenue),0) as total_revenue, "
            "COALESCE(SUM(orders),0) as total_orders, "
            "COALESCE(SUM(clicks),0) as total_clicks "
            "FROM ad_campaigns"
        ).fetchone()
    total_spent = float(r["total_spent"])
    total_rev = float(r["total_revenue"])
    return {
        "total": r["total"],
        "total_spent": total_spent,
        "total_revenue": total_rev,
        "total_orders": int(r["total_orders"]),
        "total_clicks": int(r["total_clicks"]),
        "overall_roas": round(total_rev / total_spent, 2) if total_spent else 0,
        "overall_profit": round(total_rev - total_spent, 2),
    }


def by_platform() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT platform, COUNT(*) as campaigns, "
            "SUM(spent) as spent, SUM(revenue) as revenue, "
            "SUM(orders) as orders, SUM(clicks) as clicks "
            "FROM ad_campaigns GROUP BY platform ORDER BY SUM(revenue) DESC"
        ).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        sp = float(d.get("spent") or 0)
        rv = float(d.get("revenue") or 0)
        d["roas"] = round(rv / sp, 2) if sp > 0 else 0
        d["profit"] = round(rv - sp, 2)
        results.append(d)
    return results
