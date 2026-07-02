"""Thai Seller Tax Report — income summary for personal income tax filing."""
from __future__ import annotations
import db

# Thai PIT deduction: Standard deduction for business income = 60% of revenue
# (or actual expenses if higher). Used as a guide only — not official tax advice.
STANDARD_DEDUCTION_PCT = 60.0
VAT_THRESHOLD = 1_800_000  # Revenue above this requires VAT registration

EXPENSE_CATEGORIES = [
    "packaging", "shipping", "platform_fee", "advertising",
    "staff", "rent", "utilities", "equipment", "other",
]


def quarterly(year: int, quarter: int) -> dict:
    """Revenue and expense summary for a quarter (Q1=1, Q4=4)."""
    q_months = {
        1: ("01", "02", "03"),
        2: ("04", "05", "06"),
        3: ("07", "08", "09"),
        4: ("10", "11", "12"),
    }
    months = q_months.get(quarter, ("01",))
    month_conditions = " OR ".join(
        "strftime('%m',order_date)='" + m + "'" for m in months
    )
    year_cond = "strftime('%Y',order_date)='" + str(year) + "'"

    with db.conn() as c:
        revenue_row = c.execute(
            "SELECT COALESCE(SUM(total_price),0) rev, COUNT(*) orders "
            "FROM orders "
            "WHERE (" + month_conditions + ") AND " + year_cond +
            " AND status NOT IN ('cancelled','returned')"
        ).fetchone()
        returns_row = c.execute(
            "SELECT COALESCE(SUM(refund_amount),0) amount FROM returns "
            "WHERE (" +
            " OR ".join(
                "strftime('%m',created_at)='" + m + "'" for m in months
            ) +
            ") AND strftime('%Y',created_at)='" + str(year) + "'"
        ).fetchone()

        exp_cond_m = " OR ".join(
            "strftime('%m',expense_date)='" + m + "'" for m in months
        )
        expense_rows = c.execute(
            "SELECT category, COALESCE(SUM(amount),0) total "
            "FROM expenses "
            "WHERE (" + exp_cond_m + ") "
            "AND strftime('%Y',expense_date)='" + str(year) + "' "
            "GROUP BY category"
        ).fetchall()

    revenue = revenue_row["rev"] or 0
    returns_amt = returns_row["amount"] or 0
    net_revenue = revenue - returns_amt
    expenses_by_cat = {r["category"]: r["total"] for r in expense_rows}
    total_expenses = sum(expenses_by_cat.values())
    gross_profit = net_revenue - total_expenses
    std_deduction = round(net_revenue * STANDARD_DEDUCTION_PCT / 100, 2)

    return {
        "year": year,
        "quarter": quarter,
        "revenue": round(revenue, 2),
        "returns": round(returns_amt, 2),
        "net_revenue": round(net_revenue, 2),
        "expenses": expenses_by_cat,
        "total_expenses": round(total_expenses, 2),
        "gross_profit": round(gross_profit, 2),
        "standard_deduction": std_deduction,
        "taxable_income_std": max(0, round(net_revenue - std_deduction, 2)),
        "taxable_income_actual": max(0, round(net_revenue - total_expenses, 2)),
        "orders": revenue_row["orders"],
    }


def annual(year: int) -> dict:
    quarters = [quarterly(year, q) for q in range(1, 5)]
    revenue = sum(q["revenue"] for q in quarters)
    net_revenue = sum(q["net_revenue"] for q in quarters)
    total_expenses = sum(q["total_expenses"] for q in quarters)
    std_deduction = round(net_revenue * STANDARD_DEDUCTION_PCT / 100, 2)

    expense_merged: dict[str, float] = {}
    for q in quarters:
        for cat, amt in q["expenses"].items():
            expense_merged[cat] = expense_merged.get(cat, 0) + amt

    return {
        "year": year,
        "revenue": round(revenue, 2),
        "net_revenue": round(net_revenue, 2),
        "total_expenses": round(total_expenses, 2),
        "gross_profit": round(net_revenue - total_expenses, 2),
        "standard_deduction": std_deduction,
        "taxable_income_std": max(0, round(net_revenue - std_deduction, 2)),
        "taxable_income_actual": max(0, round(net_revenue - total_expenses, 2)),
        "vat_required": revenue >= VAT_THRESHOLD,
        "vat_threshold": VAT_THRESHOLD,
        "by_quarter": quarters,
        "expenses": expense_merged,
        "orders": sum(q["orders"] for q in quarters),
    }


def vat_check(year: int) -> dict:
    """Check if revenue crossed VAT registration threshold."""
    with db.conn() as c:
        row = c.execute(
            "SELECT COALESCE(SUM(total_price),0) rev FROM orders "
            "WHERE strftime('%Y',order_date)=? "
            "AND status NOT IN ('cancelled','returned')",
            (str(year),),
        ).fetchone()
    rev = row["rev"] if row else 0
    return {
        "year": year,
        "revenue": round(rev, 2),
        "threshold": VAT_THRESHOLD,
        "requires_vat": rev >= VAT_THRESHOLD,
        "remaining_headroom": max(0, round(VAT_THRESHOLD - rev, 2)),
        "pct_of_threshold": round(rev / VAT_THRESHOLD * 100, 1),
    }


def stats() -> dict:
    from datetime import datetime
    year = datetime.now().year
    try:
        vat = vat_check(year)
        return {
            "current_year": year,
            "ytd_revenue": vat["revenue"],
            "vat_required": vat["requires_vat"],
            "vat_headroom": vat["remaining_headroom"],
        }
    except Exception:
        return {"current_year": year, "ytd_revenue": 0,
                "vat_required": False, "vat_headroom": VAT_THRESHOLD}
