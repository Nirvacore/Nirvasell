"""Bundle Engine — increase average order value with smart bundles.

Uses order history to find products frequently bought together,
then suggests bundle pricing with a small discount that still
increases total revenue per customer."""
from __future__ import annotations

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS bundles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                skus TEXT NOT NULL,
                individual_total REAL DEFAULT 0,
                bundle_price REAL DEFAULT 0,
                discount_pct REAL DEFAULT 0,
                times_sold INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


def suggest_bundles(limit: int = 10) -> list[dict]:
    """Find products frequently bought together in the same order."""
    with db.conn() as c:
        combos = c.execute(
            "SELECT a.sku as sku_a, b.sku as sku_b, "
            "COUNT(*) as freq, "
            "MIN(a.unit_price) as price_a, MIN(b.unit_price) as price_b "
            "FROM orders a JOIN orders b ON a.order_id = b.order_id "
            "AND a.sku < b.sku "
            "WHERE a.order_id IS NOT NULL AND a.order_id != '' "
            "AND a.sku IS NOT NULL AND b.sku IS NOT NULL "
            "GROUP BY a.sku, b.sku HAVING freq >= 2 "
            "ORDER BY freq DESC LIMIT ?",
            (limit,),
        ).fetchall()

    suggestions = []
    for c in combos:
        price_a = float(c["price_a"] or 0)
        price_b = float(c["price_b"] or 0)
        individual = price_a + price_b
        # 5-10% discount for bundle
        discount = 0.07
        bundle_price = round(individual * (1 - discount))
        # Psychological pricing
        bundle_price = _psych_round(bundle_price)
        saving = individual - bundle_price

        suggestions.append({
            "sku_a": c["sku_a"],
            "sku_b": c["sku_b"],
            "freq": c["freq"],
            "price_a": price_a,
            "price_b": price_b,
            "individual_total": individual,
            "bundle_price": bundle_price,
            "saving": saving,
            "discount_pct": round(saving / individual * 100, 1) if individual else 0,
        })
    return suggestions


def _psych_round(price: float) -> float:
    """Round to psychological price point (e.g. 999 not 1012)."""
    if price <= 0:
        return price
    if price < 100:
        return round(price / 10) * 10 - 1
    if price < 1000:
        r = round(price / 50) * 50
        return r - 1 if r > 50 else r
    r = round(price / 100) * 100
    return r - 1 if r > 100 else r


def create_bundle(name: str, skus: list[str],
                  individual_total: float, bundle_price: float) -> int:
    discount = round((individual_total - bundle_price) / individual_total * 100, 1) if individual_total else 0
    sku_str = ",".join(skus)
    with db.conn() as c:
        c.execute(
            "INSERT INTO bundles (name, skus, individual_total, bundle_price, discount_pct) "
            "VALUES (?,?,?,?,?)",
            (name, sku_str, individual_total, bundle_price, discount),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def all_bundles() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM bundles ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def update_bundle(bundle_id: int, **kwargs):
    sets = []
    vals = []
    for k in ("name", "bundle_price", "status", "times_sold"):
        if k in kwargs:
            sets.append(k + "=?")
            vals.append(kwargs[k])
    if not sets:
        return
    vals.append(bundle_id)
    with db.conn() as c:
        c.execute(
            "UPDATE bundles SET " + ",".join(sets) + " WHERE id=?",
            vals,
        )


def delete_bundle(bundle_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM bundles WHERE id=?", (bundle_id,))


def record_sale(bundle_id: int):
    with db.conn() as c:
        c.execute(
            "UPDATE bundles SET times_sold = times_sold + 1 WHERE id=?",
            (bundle_id,),
        )


def stats() -> dict:
    with db.conn() as c:
        r = c.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) as active, "
            "COALESCE(SUM(times_sold),0) as total_sold, "
            "COALESCE(SUM(times_sold * bundle_price),0) as total_revenue "
            "FROM bundles"
        ).fetchone()
    return {
        "total": r["total"],
        "active": int(r["active"] or 0),
        "total_sold": int(r["total_sold"]),
        "total_revenue": float(r["total_revenue"]),
    }
