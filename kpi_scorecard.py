"""KPI Scorecard — aggregate key business metrics from all modules."""
from __future__ import annotations
import db


def _safe(fn):
    try:
        return fn()
    except Exception:
        return None


def health_score(metrics: dict) -> int:
    """0-100 overall business health score."""
    score = 50
    if metrics.get("margin_pct", 0) > 30:
        score += 10
    elif metrics.get("margin_pct", 0) < 10:
        score -= 10
    if metrics.get("repeat_rate", 0) > 30:
        score += 10
    elif metrics.get("repeat_rate", 0) < 10:
        score -= 5
    if metrics.get("low_stock_count", 0) == 0:
        score += 5
    elif metrics.get("low_stock_count", 0) > 5:
        score -= 10
    if metrics.get("avg_rating", 0) >= 4.5:
        score += 10
    elif metrics.get("avg_rating", 0) < 3.5 and metrics.get("avg_rating", 0) > 0:
        score -= 10
    if metrics.get("cod_return_rate", 0) < 5:
        score += 5
    elif metrics.get("cod_return_rate", 0) > 15:
        score -= 10
    if metrics.get("unanswered_reviews", 0) == 0:
        score += 5
    elif metrics.get("unanswered_reviews", 0) > 5:
        score -= 5
    return max(0, min(100, score))


def all_kpis(days: int = 30) -> dict:
    with db.conn() as c:
        # Revenue & orders
        rev_row = _safe(lambda: c.execute(
            "SELECT COALESCE(SUM(total_price),0) rev, "
            "COUNT(*) orders, COALESCE(AVG(total_price),0) aov "
            "FROM orders "
            "WHERE date(order_date) >= date('now','-' || ? || ' days','localtime') "
            "  AND status NOT IN ('cancelled','returned')",
            (days,),
        ).fetchone())
        revenue = rev_row["rev"] if rev_row else 0
        orders = rev_row["orders"] if rev_row else 0
        aov = round(rev_row["aov"] if rev_row else 0, 2)

        # COGS and margin
        cogs_row = _safe(lambda: c.execute(
            "SELECT COALESCE(SUM(oi.quantity * p.cost_price),0) cogs "
            "FROM order_items oi "
            "JOIN orders o ON oi.order_id=o.id "
            "JOIN products p ON oi.sku=p.sku "
            "WHERE date(o.order_date) >= date('now','-' || ? || ' days','localtime') "
            "  AND o.status NOT IN ('cancelled','returned')",
            (days,),
        ).fetchone())
        cogs = cogs_row["cogs"] if cogs_row else 0
        gross_profit = revenue - cogs
        margin_pct = round(gross_profit / revenue * 100, 1) if revenue > 0 else 0

        # Expenses
        exp_row = _safe(lambda: c.execute(
            "SELECT COALESCE(SUM(amount),0) total FROM expenses "
            "WHERE date(expense_date) >= date('now','-' || ? || ' days','localtime')",
            (days,),
        ).fetchone())
        expenses = exp_row["total"] if exp_row else 0
        net_profit = gross_profit - expenses

        # Stock
        stock_row = _safe(lambda: c.execute(
            "SELECT COUNT(*) low FROM products WHERE stock <= 5 AND stock > 0"
        ).fetchone())
        low_stock = stock_row["low"] if stock_row else 0
        out_stock = _safe(lambda: c.execute(
            "SELECT COUNT(*) FROM products WHERE stock = 0"
        ).fetchone()[0]) or 0

        # Reviews
        rev_stats = _safe(lambda: c.execute(
            "SELECT COUNT(*) total, AVG(rating) avg, "
            "SUM(CASE WHEN status='new' THEN 1 ELSE 0 END) unanswered "
            "FROM reviews"
        ).fetchone())
        avg_rating = round(rev_stats["avg"] or 0, 2) if rev_stats else 0
        unanswered = rev_stats["unanswered"] if rev_stats else 0

        # COD
        cod_row = _safe(lambda: c.execute(
            "SELECT COALESCE(SUM(amount),0) pending, "
            "COUNT(*) total, "
            "SUM(CASE WHEN status='returned' THEN 1 ELSE 0 END) returned "
            "FROM cod_orders WHERE payment_type='cod'"
        ).fetchone())
        cod_pending = cod_row["pending"] if cod_row else 0
        cod_total = cod_row["total"] if cod_row else 0
        cod_returned = cod_row["returned"] if cod_row else 0
        cod_return_rate = round(cod_returned / cod_total * 100, 1) if cod_total else 0

        # Customers
        cust_row = _safe(lambda: c.execute(
            "SELECT COUNT(DISTINCT COALESCE(buyer_name,'') || COALESCE(buyer_phone,'')) "
            "total FROM orders "
            "WHERE date(order_date) >= date('now','-' || ? || ' days','localtime') "
            "  AND status NOT IN ('cancelled','returned')",
            (days,),
        ).fetchone())
        customers = cust_row[0] if cust_row else 0

    metrics = {
        "revenue": round(revenue, 2),
        "orders": orders,
        "aov": aov,
        "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "margin_pct": margin_pct,
        "expenses": round(expenses, 2),
        "net_profit": round(net_profit, 2),
        "low_stock_count": low_stock,
        "out_of_stock": out_stock,
        "avg_rating": avg_rating,
        "unanswered_reviews": unanswered,
        "cod_pending": round(cod_pending, 2),
        "cod_return_rate": cod_return_rate,
        "customers": customers,
        "days": days,
    }
    metrics["health_score"] = health_score(metrics)
    return metrics


def trend_comparison(days: int = 30) -> dict:
    """Compare current period vs previous period."""
    curr = all_kpis(days)
    with db.conn() as c:
        prev_row = _safe(lambda: c.execute(
            "SELECT COALESCE(SUM(total_price),0) rev, COUNT(*) orders "
            "FROM orders "
            "WHERE date(order_date) >= date('now','-' || ? || ' days','localtime') "
            "  AND date(order_date) < date('now','-' || ? || ' days','localtime') "
            "  AND status NOT IN ('cancelled','returned')",
            (days * 2, days),
        ).fetchone())
    prev_rev = prev_row["rev"] if prev_row else 0
    prev_orders = prev_row["orders"] if prev_row else 0
    rev_change = round((curr["revenue"] - prev_rev) / prev_rev * 100, 1) if prev_rev else 0
    orders_change = round((curr["orders"] - prev_orders) / prev_orders * 100, 1) if prev_orders else 0
    return {
        "current": curr,
        "prev_revenue": round(prev_rev, 2),
        "prev_orders": prev_orders,
        "revenue_change_pct": rev_change,
        "orders_change_pct": orders_change,
    }
