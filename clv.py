"""Customer Lifetime Value (CLV) — predict future customer worth.

Simple CLV model for Thai resellers:
  CLV = Average Order Value × Purchase Frequency × Customer Lifespan

Helps decide: how much to spend acquiring each customer type,
which customers deserve VIP treatment, where marketing budget goes."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def calculate_clv() -> list[dict]:
    """Calculate CLV for all customers with purchase history."""
    with db.conn() as c:
        rows = c.execute("""
            SELECT
                o.buyer_name,
                o.buyer_phone,
                COUNT(DISTINCT o.order_id) AS order_count,
                SUM(o.total_amount) AS total_spent,
                AVG(o.total_amount) AS avg_order_value,
                MIN(o.order_date) AS first_order,
                MAX(o.order_date) AS last_order,
                julianday('now','localtime') - julianday(MIN(o.order_date)) AS tenure_days
            FROM orders o
            WHERE o.buyer_name IS NOT NULL AND o.buyer_name != ''
            GROUP BY COALESCE(o.buyer_phone, o.buyer_name)
            HAVING order_count >= 1
            ORDER BY total_spent DESC
        """).fetchall()

    if not rows:
        return []

    items = []
    for r in rows:
        d = dict(r)
        tenure_days = max(d.get("tenure_days") or 1, 1)
        order_count = d.get("order_count") or 1
        avg_order = d.get("avg_order_value") or 0
        total_spent = d.get("total_spent") or 0

        # Purchase frequency (orders per 30 days)
        freq_monthly = order_count / (tenure_days / 30) if tenure_days > 0 else 0

        # Estimated lifespan (months) — simple: based on tenure so far
        # with a minimum of 3 months for new customers
        lifespan_months = max(tenure_days / 30, 3)

        # Projected annual CLV
        projected_annual = avg_order * freq_monthly * 12

        # Historical CLV (actual spending)
        d["freq_monthly"] = round(freq_monthly, 2)
        d["avg_order_value"] = round(avg_order, 0)
        d["total_spent"] = round(total_spent, 0)
        d["tenure_days"] = int(tenure_days)
        d["lifespan_months"] = round(lifespan_months, 1)
        d["projected_annual_clv"] = round(projected_annual, 0)

        # Segment by CLV
        if projected_annual >= 50000:
            d["tier"] = "platinum"
        elif projected_annual >= 20000:
            d["tier"] = "gold"
        elif projected_annual >= 5000:
            d["tier"] = "silver"
        else:
            d["tier"] = "bronze"

        # Recency
        last_order = d.get("last_order")
        if last_order:
            try:
                last_dt = datetime.strptime(str(last_order)[:10], "%Y-%m-%d")
                d["days_since_last"] = (datetime.now() - last_dt).days
            except Exception:
                d["days_since_last"] = 999
        else:
            d["days_since_last"] = 999

        # Churn risk
        if d["days_since_last"] > 90:
            d["churn_risk"] = "high"
        elif d["days_since_last"] > 45:
            d["churn_risk"] = "medium"
        else:
            d["churn_risk"] = "low"

        items.append(d)

    return items


def summary() -> dict:
    """CLV summary stats."""
    items = calculate_clv()
    if not items:
        return {
            "total_customers": 0,
            "avg_clv": 0,
            "total_projected": 0,
            "tiers": {"platinum": 0, "gold": 0, "silver": 0, "bronze": 0},
            "churn_risk": {"high": 0, "medium": 0, "low": 0},
        }

    tiers = {"platinum": 0, "gold": 0, "silver": 0, "bronze": 0}
    churn = {"high": 0, "medium": 0, "low": 0}
    for i in items:
        tiers[i["tier"]] = tiers.get(i["tier"], 0) + 1
        churn[i["churn_risk"]] = churn.get(i["churn_risk"], 0) + 1

    total_proj = sum(i["projected_annual_clv"] for i in items)
    avg_clv = total_proj / len(items) if items else 0

    return {
        "total_customers": len(items),
        "avg_clv": round(avg_clv, 0),
        "total_projected": round(total_proj, 0),
        "tiers": tiers,
        "churn_risk": churn,
    }


def tier_customers(tier: str) -> list[dict]:
    """Get customers in a specific tier."""
    return [i for i in calculate_clv() if i["tier"] == tier]


def at_risk_high_value() -> list[dict]:
    """High-value customers with high churn risk — save them first!"""
    return [i for i in calculate_clv()
            if i["tier"] in ("platinum", "gold") and i["churn_risk"] in ("high", "medium")]
