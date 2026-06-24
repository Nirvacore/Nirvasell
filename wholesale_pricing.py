"""Wholesale Pricing — tiered pricing for bulk buyers.

ราคาส่ง: ซื้อ 10+ ได้ราคา A, ซื้อ 50+ ได้ราคา B, ซื้อ 100+ ได้ราคา C
Used by resellers selling to sub-resellers or corporate buyers."""
from __future__ import annotations
import json
import db
from i18n_inline import ws_tier_label

DEFAULT_TIERS = [
    {"min_qty": 1,   "tier_key": "retail",  "discount_pct": 0},
    {"min_qty": 10,  "tier_key": "small",   "discount_pct": 10},
    {"min_qty": 50,  "tier_key": "medium",  "discount_pct": 20},
    {"min_qty": 100, "tier_key": "large",   "discount_pct": 30},
]


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS wholesale_tiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                min_qty INTEGER NOT NULL,
                tier_label TEXT,
                price REAL,
                discount_pct REAL DEFAULT 0,
                UNIQUE(sku, min_qty)
            );
            CREATE INDEX IF NOT EXISTS idx_wt_sku ON wholesale_tiers(sku);
        """)


def set_tiers(sku: str, tiers: list) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM wholesale_tiers WHERE sku = ?", (sku,))
        for tier in tiers:
            c.execute("""
                INSERT INTO wholesale_tiers
                    (sku, min_qty, tier_label, price, discount_pct)
                VALUES (?, ?, ?, ?, ?)
            """, (sku, tier["min_qty"], tier.get("label", ""),
                  tier.get("price"), tier.get("discount_pct", 0)))


def get_tiers(sku: str) -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT wt.*, p.sell_price, p.cost_price
            FROM wholesale_tiers wt
            LEFT JOIN products p ON wt.sku = p.sku
            WHERE wt.sku = ?
            ORDER BY wt.min_qty ASC
        """, (sku,)).fetchall()

    result = []
    for r in rows:
        price = r["price"]
        if price is None and r["sell_price"] and r["discount_pct"]:
            price = round(r["sell_price"] * (1 - r["discount_pct"] / 100), 0)

        margin = None
        if price and r["cost_price"]:
            margin = round((price - r["cost_price"]) / price * 100, 1)

        result.append({
            "min_qty": r["min_qty"],
            "label": r["tier_label"],
            "price": price,
            "discount_pct": r["discount_pct"],
            "retail_price": r["sell_price"],
            "cost_price": r["cost_price"],
            "margin_pct": margin,
        })
    return result


def price_for_qty(sku: str, qty: int) -> dict:
    tiers = get_tiers(sku)
    if not tiers:
        with db.conn() as c:
            row = c.execute(
                "SELECT sell_price, cost_price FROM products WHERE sku = ?",
                (sku,)
            ).fetchone()
        if row:
            return {
                "sku": sku, "qty": qty,
                "price": row["sell_price"],
                "tier_label": ws_tier_label("retail"),
                "discount_pct": 0,
            }
        return {"sku": sku, "qty": qty, "price": None}

    applicable = tiers[0]
    for tier in tiers:
        if qty >= tier["min_qty"]:
            applicable = tier

    return {
        "sku": sku,
        "qty": qty,
        "price": applicable["price"],
        "tier_label": applicable["label"],
        "discount_pct": applicable["discount_pct"],
        "total": round((applicable["price"] or 0) * qty, 0),
    }


def quick_quote(items: list) -> dict:
    lines = []
    total = 0
    for item in items:
        sku = item.get("sku", "")
        qty = item.get("qty", 1)
        p = price_for_qty(sku, qty)
        line_total = round((p.get("price") or 0) * qty, 0)
        total += line_total
        lines.append({
            "sku": sku,
            "qty": qty,
            "unit_price": p.get("price"),
            "line_total": line_total,
            "tier": p.get("tier_label", ""),
            "discount_pct": p.get("discount_pct", 0),
        })
    return {"lines": lines, "total": round(total, 0)}


def skus_with_tiers() -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT wt.sku, p.name,
                   COUNT(wt.id) AS tier_count,
                   MIN(wt.min_qty) AS min_qty,
                   MIN(wt.price) AS lowest_price
            FROM wholesale_tiers wt
            LEFT JOIN products p ON wt.sku = p.sku
            GROUP BY wt.sku
            ORDER BY tier_count DESC
        """).fetchall()
    return [dict(r) for r in rows]


def stats() -> dict:
    with db.conn() as c:
        skus = c.execute(
            "SELECT COUNT(DISTINCT sku) FROM wholesale_tiers"
        ).fetchone()[0]
        tiers = c.execute("SELECT COUNT(*) FROM wholesale_tiers").fetchone()[0]
    return {"skus_with_wholesale": skus, "total_tiers": tiers}
