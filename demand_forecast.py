"""Demand Forecast — predict next 30/60/90 days sales per SKU.

Simple moving average + trend detection. No ML needed.
Shows expected units + revenue so seller can plan stock/orders."""
from __future__ import annotations
from datetime import datetime, timedelta
import db


def _weekly_sales(sku: str, weeks: int = 8) -> list:
    sales = []
    today = datetime.today()
    for i in range(weeks - 1, -1, -1):
        week_end = today - timedelta(weeks=i)
        week_start = week_end - timedelta(weeks=1)
        with db.conn() as c:
            row = c.execute("""
                SELECT COALESCE(SUM(qty), 0) AS qty
                FROM orders
                WHERE sku = ?
                  AND order_date > ?
                  AND order_date <= ?
                  AND status NOT IN ('cancelled', 'returned')
            """, (sku,
                  week_start.strftime("%Y-%m-%d"),
                  week_end.strftime("%Y-%m-%d"))).fetchone()
        sales.append(int(row["qty"] or 0))
    return sales


def forecast_sku(sku: str, horizon_days: int = 30) -> dict:
    weekly = _weekly_sales(sku, 8)

    if all(w == 0 for w in weekly):
        return {
            "sku": sku,
            "has_data": False,
            "forecast_qty": 0,
            "forecast_revenue": 0,
            "weekly_avg": 0,
            "trend": "flat",
            "confidence": "low",
        }

    last_4 = weekly[-4:]
    avg_weekly = sum(last_4) / 4 if last_4 else 0

    first_half = weekly[:4]
    second_half = weekly[4:]
    avg_first = sum(first_half) / 4 if first_half else 0
    avg_second = sum(second_half) / 4 if second_half else 0

    if avg_first > 0:
        trend_pct = (avg_second - avg_first) / avg_first * 100
    else:
        trend_pct = 0

    if trend_pct > 15:
        trend = "rising"
        trend_multiplier = 1 + (trend_pct / 200)
    elif trend_pct < -15:
        trend = "declining"
        trend_multiplier = max(0.5, 1 + (trend_pct / 200))
    else:
        trend = "stable"
        trend_multiplier = 1.0

    non_zero = [w for w in last_4 if w > 0]
    if len(non_zero) >= 3:
        confidence = "high"
    elif len(non_zero) >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    forecast_weekly = avg_weekly * trend_multiplier
    forecast_qty = round(forecast_weekly * (horizon_days / 7), 0)

    with db.conn() as c:
        prod = c.execute(
            "SELECT sell_price, cost_price FROM products WHERE sku = ?",
            (sku,)
        ).fetchone()

    sell_price = float(prod["sell_price"] or 0) if prod else 0
    forecast_revenue = round(forecast_qty * sell_price, 0)

    return {
        "sku": sku,
        "has_data": True,
        "weekly_history": weekly,
        "avg_weekly_recent": round(avg_weekly, 1),
        "trend": trend,
        "trend_pct": round(trend_pct, 1),
        "trend_multiplier": round(trend_multiplier, 2),
        "forecast_qty": int(forecast_qty),
        "forecast_revenue": forecast_revenue,
        "sell_price": sell_price,
        "confidence": confidence,
        "horizon_days": horizon_days,
    }


def forecast_all(horizon_days: int = 30, limit: int = 50) -> list:
    with db.conn() as c:
        skus = c.execute("""
            SELECT sku FROM products
            WHERE sku IN (
                SELECT DISTINCT sku FROM orders
                WHERE order_date >= date('now', '-60 days')
            )
            ORDER BY sku LIMIT ?
        """, (limit,)).fetchall()

    results = []
    for row in skus:
        f = forecast_sku(row["sku"], horizon_days)
        if f["has_data"]:
            results.append(f)

    results.sort(key=lambda x: x["forecast_revenue"], reverse=True)
    return results


def stockout_risk(horizon_days: int = 30) -> list:
    forecasts = forecast_all(horizon_days)
    risks = []

    with db.conn() as c:
        for f in forecasts:
            prod = c.execute(
                "SELECT stock FROM products WHERE sku = ?", (f["sku"],)
            ).fetchone()
            if not prod:
                continue

            stock = prod["stock"] or 0
            needed = f["forecast_qty"]

            if needed > 0:
                coverage_days = int(stock / (needed / horizon_days)) if needed > 0 else 999
            else:
                coverage_days = 999

            if coverage_days < horizon_days:
                deficit = max(0, needed - stock)
                risks.append({
                    "sku": f["sku"],
                    "current_stock": stock,
                    "forecast_need": needed,
                    "deficit": int(deficit),
                    "coverage_days": min(coverage_days, 999),
                    "risk_level": "high" if coverage_days < 7 else "medium",
                })

    risks.sort(key=lambda x: x["coverage_days"])
    return risks


def summary() -> dict:
    forecasts = forecast_all(30)
    total_revenue = sum(f["forecast_revenue"] for f in forecasts)
    rising = sum(1 for f in forecasts if f["trend"] == "rising")
    declining = sum(1 for f in forecasts if f["trend"] == "declining")
    risks = stockout_risk(30)
    return {
        "skus_forecasted": len(forecasts),
        "forecast_revenue_30d": round(total_revenue, 0),
        "rising_skus": rising,
        "declining_skus": declining,
        "stockout_risks": len(risks),
    }
