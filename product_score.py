"""Product Score — combined performance rank per SKU.

Score = weighted composite of revenue, margin, velocity, stock health.
Used to identify stars, cash cows, dogs, and question marks."""
from __future__ import annotations
import db


WEIGHTS = {
    "revenue":   0.35,
    "margin":    0.30,
    "velocity":  0.25,
    "stock":     0.10,
}


def _normalize(values: list) -> list:
    if not values:
        return []
    max_v = max(values)
    if max_v == 0:
        return [0.0] * len(values)
    return [v / max_v for v in values]


def calculate(days: int = 30) -> list:
    with db.conn() as c:
        products = c.execute("""
            SELECT p.sku, p.name, p.cost_price, p.sell_price, p.stock
            FROM products p
            ORDER BY p.sku
        """).fetchall()

        sales = c.execute("""
            SELECT sku,
                   SUM(qty) AS total_qty,
                   SUM(total_amount) AS total_revenue
            FROM orders
            WHERE order_date >= date('now', ? || ' days')
              AND status NOT IN ('cancelled', 'returned')
            GROUP BY sku
        """, (str(-days),)).fetchall()

    sales_map = {s["sku"]: s for s in sales}
    raw = []

    for p in products:
        sku = p["sku"]
        s = sales_map.get(sku)
        revenue = float(s["total_revenue"] or 0) if s else 0
        qty = int(s["total_qty"] or 0) if s else 0
        cost = float(p["cost_price"] or 0)
        sell = float(p["sell_price"] or 0)
        stock = int(p["stock"] or 0)
        velocity = qty / days if days > 0 else 0

        if sell > 0 and cost > 0:
            margin_pct = (sell - cost) / sell * 100
        else:
            margin_pct = 0

        stock_score = min(stock / max(velocity * 30, 1), 2) if velocity > 0 else (
            1 if stock > 0 else 0
        )

        raw.append({
            "sku": sku,
            "name": p["name"],
            "revenue": revenue,
            "margin_pct": round(margin_pct, 1),
            "velocity": round(velocity, 2),
            "stock": stock,
            "stock_score": stock_score,
        })

    rev_norm = _normalize([r["revenue"] for r in raw])
    mar_norm = _normalize([r["margin_pct"] for r in raw])
    vel_norm = _normalize([r["velocity"] for r in raw])
    stk_norm = _normalize([r["stock_score"] for r in raw])

    result = []
    for i, item in enumerate(raw):
        score = (
            rev_norm[i] * WEIGHTS["revenue"] +
            mar_norm[i] * WEIGHTS["margin"] +
            vel_norm[i] * WEIGHTS["velocity"] +
            stk_norm[i] * WEIGHTS["stock"]
        ) * 100

        quadrant = _quadrant(item["revenue"], item["margin_pct"])

        result.append({
            **item,
            "score": round(score, 1),
            "quadrant": quadrant,
            "quadrant_icon": {"star": "⭐", "cash_cow": "🐄",
                               "question": "❓", "dog": "🐕"}.get(quadrant, "?"),
        })

    result.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(result):
        r["rank"] = i + 1

    return result


def _quadrant(revenue: float, margin_pct: float) -> str:
    high_rev = revenue > 0
    high_mar = margin_pct >= 25

    if high_rev and high_mar:
        return "star"
    elif high_rev and not high_mar:
        return "cash_cow"
    elif not high_rev and high_mar:
        return "question"
    else:
        return "dog"


def top_performers(n: int = 10) -> list:
    return calculate()[:n]


def bottom_performers(n: int = 10) -> list:
    return list(reversed(calculate()))[:n]


def by_quadrant(quadrant: str) -> list:
    return [p for p in calculate() if p["quadrant"] == quadrant]


def summary() -> dict:
    scored = calculate()
    quadrants = {"star": 0, "cash_cow": 0, "question": 0, "dog": 0}
    for p in scored:
        q = p.get("quadrant")
        if q in quadrants:
            quadrants[q] += 1

    avg_score = sum(p["score"] for p in scored) / len(scored) if scored else 0
    return {
        "total_skus": len(scored),
        "avg_score": round(avg_score, 1),
        "quadrants": quadrants,
    }
