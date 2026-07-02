"""Business Health Score — one number to rule them all.

Aggregates 8 dimensions into a 0-100 score:
  Revenue growth, Profit margin, Stock health, Customer health,
  Cash flow, Return rate, Expense control, Channel diversity.

The CEO dashboard. Are we winning or losing?"""
from __future__ import annotations

import db


def calculate() -> dict:
    """Calculate overall business health score (0-100)."""
    scores = {}

    # 1. Revenue trend (0-100)
    scores["revenue"] = _revenue_score()

    # 2. Profit margin (0-100)
    scores["margin"] = _margin_score()

    # 3. Stock health (0-100)
    scores["stock"] = _stock_score()

    # 4. Customer health (0-100)
    scores["customers"] = _customer_score()

    # 5. Cash position (0-100)
    scores["cash"] = _cash_score()

    # 6. Return rate (0-100, lower returns = higher score)
    scores["returns"] = _return_score()

    # 7. Expense ratio (0-100)
    scores["expenses"] = _expense_score()

    # 8. Channel diversity (0-100)
    scores["channels"] = _channel_score()

    # Weighted overall
    weights = {
        "revenue": 0.20, "margin": 0.20, "stock": 0.10,
        "customers": 0.15, "cash": 0.10, "returns": 0.10,
        "expenses": 0.10, "channels": 0.05,
    }

    overall = sum(scores[k] * weights[k] for k in weights)

    # Grade
    if overall >= 80:
        grade = "A"
        status = "excellent"
    elif overall >= 60:
        grade = "B"
        status = "good"
    elif overall >= 40:
        grade = "C"
        status = "needs_work"
    else:
        grade = "D"
        status = "critical"

    return {
        "overall": round(overall, 0),
        "grade": grade,
        "status": status,
        "dimensions": scores,
        "weights": weights,
    }


def _revenue_score() -> float:
    """Score based on whether revenue is growing."""
    with db.conn() as c:
        this_month = c.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS rev
            FROM orders WHERE order_date >= date('now','start of month')
        """).fetchone()["rev"]

        last_month = c.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS rev
            FROM orders WHERE order_date >= date('now','start of month','-1 month')
              AND order_date < date('now','start of month')
        """).fetchone()["rev"]

    if last_month <= 0:
        return 50 if this_month > 0 else 0

    growth = (this_month - last_month) / last_month * 100
    if growth >= 20:
        return 100
    elif growth >= 0:
        return 60 + growth * 2
    else:
        return max(0, 60 + growth)


def _margin_score() -> float:
    """Score based on average profit margin."""
    with db.conn() as c:
        rows = c.execute("""
            SELECT COALESCE(SUM(oi.qty * oi.unit_price), 0) AS rev,
                   COALESCE(SUM(oi.qty * p.cost_price), 0) AS cogs
            FROM order_items oi
            LEFT JOIN products p ON p.sku = oi.sku
            JOIN orders o ON o.order_id = oi.order_id
            WHERE o.order_date >= date('now','-30 day')
        """).fetchone()

    rev = rows["rev"] or 0
    cogs = rows["cogs"] or 0
    if rev <= 0:
        return 0

    margin = (rev - cogs) / rev * 100
    if margin >= 30:
        return 100
    elif margin >= 15:
        return 50 + (margin - 15) / 15 * 50
    elif margin >= 0:
        return margin / 15 * 50
    else:
        return 0


def _stock_score() -> float:
    """Score based on out-of-stock and overstock ratio."""
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        oos = c.execute("SELECT COUNT(*) FROM products WHERE stock <= 0").fetchone()[0]
        low = c.execute("SELECT COUNT(*) FROM products WHERE stock > 0 AND stock <= 5").fetchone()[0]

    if total <= 0:
        return 50

    oos_pct = oos / total * 100
    low_pct = low / total * 100
    healthy_pct = 100 - oos_pct - low_pct
    return min(100, healthy_pct + low_pct * 0.5)


def _customer_score() -> float:
    """Score based on repeat rate and customer growth."""
    with db.conn() as c:
        total = c.execute("""
            SELECT COUNT(DISTINCT COALESCE(buyer_phone, buyer_name)) AS cnt
            FROM orders WHERE order_date >= date('now','-90 day')
        """).fetchone()["cnt"]

        repeat = c.execute("""
            SELECT COUNT(*) AS cnt FROM (
                SELECT COALESCE(buyer_phone, buyer_name) AS buyer
                FROM orders WHERE order_date >= date('now','-90 day')
                GROUP BY buyer HAVING COUNT(*) >= 2
            )
        """).fetchone()["cnt"]

    if total <= 0:
        return 0

    repeat_rate = repeat / total * 100
    if repeat_rate >= 40:
        return 100
    elif repeat_rate >= 20:
        return 50 + (repeat_rate - 20) / 20 * 50
    else:
        return repeat_rate / 20 * 50


def _cash_score() -> float:
    """Score based on cash flow health."""
    try:
        import cashflow as cf
        f = cf.forecast(30)
        health = f.get("health", "tight")
        if health == "positive":
            return 100
        elif health == "tight":
            return 50
        else:
            return 20
    except Exception:
        return 50


def _return_score() -> float:
    """Lower return rate = higher score."""
    try:
        import returns as ret
        ret.init()
        s = ret.stats()
        rate = s.get("return_rate", 0)
        if rate <= 1:
            return 100
        elif rate <= 3:
            return 80
        elif rate <= 5:
            return 60
        elif rate <= 10:
            return 40
        else:
            return 20
    except Exception:
        return 80  # assume good if no data


def _expense_score() -> float:
    """Score based on expense-to-revenue ratio."""
    with db.conn() as c:
        rev = c.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM orders
            WHERE order_date >= date('now','-30 day')
        """).fetchone()[0]

        exp = c.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses
            WHERE expense_date >= date('now','-30 day')
        """).fetchone()[0]

    if rev <= 0:
        return 50

    ratio = exp / rev * 100
    if ratio <= 10:
        return 100
    elif ratio <= 20:
        return 80
    elif ratio <= 30:
        return 60
    elif ratio <= 50:
        return 40
    else:
        return 20


def _channel_score() -> float:
    """Score based on platform diversity (avoid single-channel risk)."""
    with db.conn() as c:
        rows = c.execute("""
            SELECT platform, COUNT(*) AS cnt FROM orders
            WHERE order_date >= date('now','-30 day')
            GROUP BY platform
        """).fetchall()

    if not rows:
        return 0

    channels = len(rows)
    if channels >= 4:
        return 100
    elif channels >= 3:
        return 80
    elif channels >= 2:
        return 60
    else:
        return 30


def dimension_details() -> list[dict]:
    """Details for each dimension with advice."""
    result = calculate()
    dims = result["dimensions"]

    details = [
        {"key": "revenue",   "icon": "📈", "score": dims["revenue"],   "weight": 20},
        {"key": "margin",    "icon": "💰", "score": dims["margin"],    "weight": 20},
        {"key": "customers", "icon": "👥", "score": dims["customers"], "weight": 15},
        {"key": "stock",     "icon": "📦", "score": dims["stock"],     "weight": 10},
        {"key": "cash",      "icon": "💧", "score": dims["cash"],      "weight": 10},
        {"key": "returns",   "icon": "↩️", "score": dims["returns"],   "weight": 10},
        {"key": "expenses",  "icon": "💸", "score": dims["expenses"],  "weight": 10},
        {"key": "channels",  "icon": "🌐", "score": dims["channels"],  "weight": 5},
    ]

    for d in details:
        s = d["score"]
        if s >= 80:
            d["status"] = "excellent"
        elif s >= 60:
            d["status"] = "good"
        elif s >= 40:
            d["status"] = "needs_work"
        else:
            d["status"] = "critical"

    return sorted(details, key=lambda x: x["score"])
