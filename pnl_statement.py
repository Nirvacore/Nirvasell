"""P&L Statement — formal monthly/quarterly income statement.

Revenue - COGS = Gross Profit
Gross Profit - Expenses = Net Profit

Used for tax filing, business review, investor reporting."""
from __future__ import annotations
import db


def _fetch_period(year: int, month: int | None = None) -> dict:
    if month:
        date_from = "{:04d}-{:02d}-01".format(year, month)
        date_to = "{:04d}-{:02d}-31".format(year, month)
        label = "{:04d}-{:02d}".format(year, month)
    else:
        date_from = "{:04d}-01-01".format(year)
        date_to = "{:04d}-12-31".format(year)
        label = str(year)

    with db.conn() as c:
        rev_row = c.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS revenue,
                   COALESCE(SUM(qty), 0) AS units
            FROM orders
            WHERE order_date BETWEEN ? AND ?
              AND status NOT IN ('cancelled', 'returned')
        """, (date_from, date_to)).fetchone()

        cogs_row = c.execute("""
            SELECT COALESCE(SUM(o.qty * COALESCE(p.cost_price, 0)), 0) AS cogs
            FROM orders o
            LEFT JOIN products p ON o.sku = p.sku
            WHERE o.order_date BETWEEN ? AND ?
              AND o.status NOT IN ('cancelled', 'returned')
        """, (date_from, date_to)).fetchone()

        exp_rows = c.execute("""
            SELECT category, COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total DESC
        """, (date_from, date_to)).fetchall()

        returns_row = c.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM orders
            WHERE order_date BETWEEN ? AND ?
              AND status = 'returned'
        """, (date_from, date_to)).fetchone()

    revenue = float(rev_row["revenue"] or 0)
    returns = float(returns_row["total"] or 0)
    net_revenue = revenue - returns
    cogs = float(cogs_row["cogs"] or 0)
    gross_profit = net_revenue - cogs
    gross_margin = (gross_profit / net_revenue * 100) if net_revenue > 0 else 0

    expenses = {r["category"]: float(r["total"]) for r in exp_rows}
    total_expenses = sum(expenses.values())

    net_profit = gross_profit - total_expenses
    net_margin = (net_profit / net_revenue * 100) if net_revenue > 0 else 0

    return {
        "label": label,
        "date_from": date_from,
        "date_to": date_to,
        "revenue": round(revenue, 2),
        "returns": round(returns, 2),
        "net_revenue": round(net_revenue, 2),
        "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin": round(gross_margin, 1),
        "expenses": {k: round(v, 2) for k, v in expenses.items()},
        "total_expenses": round(total_expenses, 2),
        "net_profit": round(net_profit, 2),
        "net_margin": round(net_margin, 1),
        "units_sold": int(rev_row["units"] or 0),
        "profitable": net_profit > 0,
    }


def monthly(year: int, month: int) -> dict:
    return _fetch_period(year, month)


def annual(year: int) -> dict:
    return _fetch_period(year)


def quarterly(year: int, quarter: int) -> dict:
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 2

    with db.conn() as c:
        rev_row = c.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS revenue,
                   COALESCE(SUM(qty), 0) AS units
            FROM orders
            WHERE strftime('%Y', order_date) = ?
              AND CAST(strftime('%m', order_date) AS INTEGER) BETWEEN ? AND ?
              AND status NOT IN ('cancelled', 'returned')
        """, (str(year), start_month, end_month)).fetchone()

        cogs_row = c.execute("""
            SELECT COALESCE(SUM(o.qty * COALESCE(p.cost_price, 0)), 0) AS cogs
            FROM orders o
            LEFT JOIN products p ON o.sku = p.sku
            WHERE strftime('%Y', o.order_date) = ?
              AND CAST(strftime('%m', o.order_date) AS INTEGER) BETWEEN ? AND ?
              AND o.status NOT IN ('cancelled', 'returned')
        """, (str(year), start_month, end_month)).fetchone()

        exp_rows = c.execute("""
            SELECT category, COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE strftime('%Y', date) = ?
              AND CAST(strftime('%m', date) AS INTEGER) BETWEEN ? AND ?
            GROUP BY category
        """, (str(year), start_month, end_month)).fetchall()

        returns_row = c.execute("""
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM orders
            WHERE strftime('%Y', order_date) = ?
              AND CAST(strftime('%m', order_date) AS INTEGER) BETWEEN ? AND ?
              AND status = 'returned'
        """, (str(year), start_month, end_month)).fetchone()

    revenue = float(rev_row["revenue"] or 0)
    returns = float(returns_row["total"] or 0)
    net_revenue = revenue - returns
    cogs = float(cogs_row["cogs"] or 0)
    gross_profit = net_revenue - cogs
    gross_margin = (gross_profit / net_revenue * 100) if net_revenue > 0 else 0
    expenses = {r["category"]: float(r["total"]) for r in exp_rows}
    total_expenses = sum(expenses.values())
    net_profit = gross_profit - total_expenses
    net_margin = (net_profit / net_revenue * 100) if net_revenue > 0 else 0

    return {
        "label": "Q{} {}".format(quarter, year),
        "revenue": round(revenue, 2),
        "returns": round(returns, 2),
        "net_revenue": round(net_revenue, 2),
        "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin": round(gross_margin, 1),
        "expenses": {k: round(v, 2) for k, v in expenses.items()},
        "total_expenses": round(total_expenses, 2),
        "net_profit": round(net_profit, 2),
        "net_margin": round(net_margin, 1),
        "units_sold": int(rev_row["units"] or 0),
        "profitable": net_profit > 0,
    }


def monthly_trend(months: int = 6) -> list:
    from datetime import datetime, timedelta
    results = []
    today = datetime.today()
    for i in range(months - 1, -1, -1):
        d = today.replace(day=1)
        for _ in range(i):
            d = (d - timedelta(days=1)).replace(day=1)
        p = monthly(d.year, d.month)
        results.append({
            "month": d.strftime("%Y-%m"),
            "revenue": p["net_revenue"],
            "gross_profit": p["gross_profit"],
            "net_profit": p["net_profit"],
        })
    return results
