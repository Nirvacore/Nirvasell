"""Sales Goals — set targets, track progress, celebrate wins.

Monthly revenue target, order count target, new customer target.
Visual progress bars. Alert when behind pace."""
from __future__ import annotations

from datetime import datetime, date
import math

import db
from i18n_inline import goal_type_label, goal_type_unit
from order_dates import order_business_date


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS sales_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                metric TEXT NOT NULL,
                target REAL NOT NULL,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)


METRICS = {
    "revenue":       {"icon": "💰"},
    "orders":        {"icon": "📦"},
    "profit":        {"icon": "💵"},
    "new_customers": {"icon": "👥"},
    "avg_order":     {"icon": "🎯"},
}


def set_goal(period: str, metric: str, target: float) -> int:
    """Set or update a goal. period = YYYY-MM."""
    with db.conn() as c:
        existing = c.execute(
            "SELECT id FROM sales_goals WHERE period=? AND metric=?",
            (period, metric),
        ).fetchone()
        if existing:
            c.execute("UPDATE sales_goals SET target=? WHERE id=?",
                      (target, existing["id"]))
            return existing["id"]
        else:
            c.execute(
                "INSERT INTO sales_goals (period, metric, target) VALUES (?,?,?)",
                (period, metric, target),
            )
            return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def delete_goal(goal_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM sales_goals WHERE id=?", (goal_id,))


def goals_for_period(period: str = "") -> list[dict]:
    """Get all goals for a period with actual progress."""
    if not period:
        period = date.today().strftime("%Y-%m")

    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM sales_goals WHERE period=? ORDER BY metric",
            (period,),
        ).fetchall()

    results = []
    for r in rows:
        d = dict(r)
        evidence = _actual_evidence(d["metric"], period)
        actual = evidence["value"]
        target = d["target"]
        pct = round(actual / target * 100, 1) if actual is not None and target > 0 else None

        # Days progress
        today = date.today()
        days_in_month = 30
        days_elapsed = today.day
        pace_pct = round(days_elapsed / days_in_month * 100, 1)

        # Status
        if not evidence["complete"]:
            status = "unavailable"
        elif pct is not None and pct >= 100:
            status = "achieved"
        elif pct is not None and pct >= pace_pct * 0.9:
            status = "on_track"
        elif pct is not None and pct >= pace_pct * 0.7:
            status = "behind"
        else:
            status = "at_risk"

        d["actual"] = actual
        d["pct"] = min(pct, 200) if pct is not None else None  # cap display at 200%
        d["pace_pct"] = pace_pct
        d["status"] = status
        d["evidence_complete"] = evidence["complete"]
        d["missing_evidence_rows"] = evidence["missing_evidence_rows"]
        d["days_elapsed"] = days_elapsed
        d["days_remaining"] = max(days_in_month - days_elapsed, 0)

        info = METRICS.get(d["metric"], {})
        d["label"] = goal_type_label(d["metric"])
        d["icon"] = info.get("icon", "🎯")
        d["unit"] = goal_type_unit(d["metric"])

        results.append(d)

    return results


def _nonblank(value) -> bool:
    return value is not None and str(value).strip() != ""


_canonical_date = order_business_date


def _number(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _actual_evidence(metric: str, period: str) -> dict:
    """Return an actual only when every contributing row is provable.

    Orders are line-level in the canonical schema. Revenue uses the imported
    line total, while order count and average order value aggregate by the
    canonical ``(platform, order_id)`` identity. Rows without enough evidence
    suppress the exact metric instead of silently becoming zero.
    """
    if metric not in METRICS:
        return {"value": None, "complete": False, "missing_evidence_rows": 0}
    try:
        parsed_period = datetime.strptime(period, "%Y-%m")
    except ValueError:
        return {"value": None, "complete": False, "missing_evidence_rows": 0}
    if parsed_period.strftime("%Y-%m") != period:
        return {"value": None, "complete": False, "missing_evidence_rows": 0}

    with db.conn() as c:
        rows = [dict(row) for row in c.execute("SELECT * FROM orders")]
        products = {
            str(row["sku"]).strip(): dict(row)
            for row in c.execute("SELECT sku, cost_price FROM products")
            if _nonblank(row["sku"])
        }

    included = []
    missing = 0
    for row in rows:
        order_date = _canonical_date(row["order_date"])
        if order_date is None:
            missing += 1
            continue
        if order_date.strftime("%Y-%m") != period:
            continue

        status = str(row["status"]).strip().lower() if _nonblank(row["status"]) else ""
        if not status:
            missing += 1
            continue
        if status in {"cancelled", "returned"}:
            continue

        if not all(_nonblank(row[key]) for key in ("order_id", "platform", "sku")):
            missing += 1
            continue
        if metric in {"revenue", "profit", "avg_order"} and _number(row["total_price"]) is None:
            missing += 1
            continue
        if metric == "new_customers" and not (
            _nonblank(row["buyer_phone"]) or _nonblank(row["buyer_name"])
        ):
            missing += 1
            continue
        if metric == "profit":
            sku = str(row["sku"]).strip()
            product = products.get(sku)
            if (_number(row["qty"]) is None or product is None
                    or _number(product["cost_price"]) is None):
                missing += 1
                continue

        included.append(row)

    if missing:
        return {"value": None, "complete": False, "missing_evidence_rows": missing}

    if metric == "revenue":
        value = sum(_number(row["total_price"]) for row in included)
    elif metric == "orders":
        value = len({
            (str(row["platform"]).strip(), str(row["order_id"]).strip())
            for row in included
        })
    elif metric == "profit":
        value = sum(
            _number(row["total_price"])
            - _number(row["qty"]) * _number(products[str(row["sku"]).strip()]["cost_price"])
            for row in included
        )
    elif metric == "new_customers":
        value = len({
            str(row["buyer_phone"]).strip()
            if _nonblank(row["buyer_phone"])
            else str(row["buyer_name"]).strip().casefold()
            for row in included
        })
    else:
        order_totals: dict[tuple[str, str], float] = {}
        for row in included:
            identity = (str(row["platform"]).strip(), str(row["order_id"]).strip())
            order_totals[identity] = order_totals.get(identity, 0.0) + _number(row["total_price"])
        value = sum(order_totals.values()) / len(order_totals) if order_totals else 0.0

    return {"value": value, "complete": True, "missing_evidence_rows": 0}


def _get_actual(metric: str, period: str) -> float | None:
    """Compatibility wrapper for callers that only need the value."""
    return _actual_evidence(metric, period)["value"]


def summary(period: str = "") -> dict:
    goals = goals_for_period(period)
    achieved = sum(1 for g in goals if g["status"] == "achieved")
    on_track = sum(1 for g in goals if g["status"] == "on_track")
    behind = sum(1 for g in goals if g["status"] == "behind")
    at_risk = sum(1 for g in goals if g["status"] == "at_risk")
    unavailable = sum(1 for g in goals if g["status"] == "unavailable")

    return {
        "total": len(goals),
        "achieved": achieved,
        "on_track": on_track,
        "behind": behind,
        "at_risk": at_risk,
        "unavailable": unavailable,
    }
