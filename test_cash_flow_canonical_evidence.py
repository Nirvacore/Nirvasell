"""Regression coverage for canonical, fail-closed cash-flow evidence."""

from __future__ import annotations

import math
import sys
import tempfile
import types
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import cash_flow
import db
from order_dates import order_business_date


def business_today() -> date:
    result = order_business_date(datetime.now(timezone.utc))
    assert result is not None
    return result


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_cash_flow_") as temp:
        db._resolve_path = lambda: Path(temp) / "user.db"
        try:
            db.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def insert_order(connection, label: str, **overrides) -> None:
    values = {
        "order_id": label,
        "sku": "SKU-1",
        "platform": "direct",
        "qty": 1,
        "unit_price": 999.0,
        "total_price": 125.0,
        "order_date": business_today().isoformat(),
        "status": "paid",
    }
    values.update(overrides)
    connection.execute(
        "INSERT INTO orders "
        "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
        "VALUES (?,?,?,?,?,?,?,?)",
        tuple(values[key] for key in (
            "order_id", "sku", "platform", "qty", "unit_price",
            "total_price", "order_date", "status",
        )),
    )


def test_fresh_user_db_and_canonical_daily_monthly_contract() -> None:
    with isolated_database():
        empty = cash_flow.daily_summary(days=7)
        assert empty["evidence_complete"] is True
        assert empty["days"] == []

        today = business_today()
        represented_today = datetime.combine(
            today, time(0, 30), tzinfo=ZoneInfo("Asia/Bangkok")
        ).astimezone(timezone.utc).isoformat()
        with db.conn() as connection:
            insert_order(connection, "paid", order_date=represented_today)
            insert_order(connection, "cancelled", total_price=9999.0,
                         status=" Cancelled ")
            insert_order(connection, "returned", total_price=9999.0,
                         status="RETURNED")
            connection.execute(
                "INSERT INTO expenses (date,category,amount) VALUES (?,?,?)",
                (today.isoformat(), "shipping", 25.0),
            )

        daily = cash_flow.daily_summary(days=7)
        assert daily["evidence_complete"] is True
        assert daily["missing_order_evidence_rows"] == 0
        assert daily["missing_expense_evidence_rows"] == 0
        assert daily["days"] == [{
            "day": today.isoformat(),
            "income": 125.0,
            "expenses": 25.0,
            "net": 100.0,
            "cumulative": 100.0,
        }]
        assert cash_flow.daily(days=7) == daily["days"]

        monthly = cash_flow.monthly_summary(months=1)
        assert monthly["evidence_complete"] is True
        assert monthly["months"] == [{
            "month": today.strftime("%Y-%m"),
            "income": 125.0,
            "expenses": 25.0,
            "net": 100.0,
            "margin_pct": 80.0,
        }]
        assert cash_flow.monthly(months=1) == monthly["months"]

        forecast = cash_flow.current_month_forecast()
        assert forecast["evidence_complete"] is True
        assert forecast["this_month_so_far"] == 125.0
        assert forecast["this_month_expenses"] == 25.0


def test_in_window_incomplete_order_or_expense_fails_closed() -> None:
    order_cases = [
        ("blank-status", {"status": "   "}),
        ("missing-total", {"total_price": None}),
        ("negative-total", {"total_price": -1.0}),
        ("infinite-total", {"total_price": math.inf}),
    ]
    for name, overrides in order_cases:
        with isolated_database():
            with db.conn() as connection:
                insert_order(connection, name, **overrides)
            result = cash_flow.daily_summary(days=7)
            assert result["evidence_complete"] is False, name
            assert result["missing_order_evidence_rows"] == 1, name
            assert result["missing_expense_evidence_rows"] == 0, name
            assert result["days"] == [], name

    for name, expense_date, amount in [
        ("blank-date", "   ", 10.0),
        ("negative-amount", business_today().isoformat(), -1.0),
    ]:
        with isolated_database():
            cash_flow.daily_summary(days=7)  # creates the canonical table
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO expenses (date,category,amount) VALUES (?,?,?)",
                    (expense_date, "other", amount),
                )
            result = cash_flow.daily_summary(days=7)
            assert result["evidence_complete"] is False, name
            assert result["missing_order_evidence_rows"] == 0, name
            assert result["missing_expense_evidence_rows"] == 1, name
            assert result["days"] == [], name


def test_known_out_of_window_defects_do_not_suppress_current_evidence() -> None:
    with isolated_database():
        old = (business_today() - timedelta(days=40)).isoformat()
        future = (business_today() + timedelta(days=2)).isoformat()
        with db.conn() as connection:
            insert_order(connection, "current")
            insert_order(connection, "old-invalid", order_date=old,
                         status="   ", total_price=None)
            insert_order(connection, "future-invalid", order_date=future,
                         status="   ", total_price=None)

        result = cash_flow.daily_summary(days=7)
        assert result["evidence_complete"] is True
        assert result["days"][0]["income"] == 125.0

    with isolated_database():
        with db.conn() as connection:
            insert_order(connection, "unknown-membership", order_date="not-a-date")
        result = cash_flow.daily_summary(days=7)
        assert result["evidence_complete"] is False
        assert result["missing_order_evidence_rows"] == 1
        assert result["days"] == []


def test_forecast_fails_closed_when_prior_month_evidence_is_incomplete() -> None:
    with isolated_database():
        prior_month = business_today().replace(day=1) - timedelta(days=1)
        with db.conn() as connection:
            insert_order(connection, "current")
            insert_order(connection, "prior-incomplete",
                         order_date=prior_month.isoformat(), status="   ",
                         total_price=None)

        assert cash_flow.monthly_summary(months=1)["evidence_complete"] is True
        forecast = cash_flow.current_month_forecast()
        assert forecast["evidence_complete"] is False
        assert forecast["missing_order_evidence_rows"] == 1
        assert forecast["projected_net"] is None
        summary = cash_flow.summary()
        assert summary["evidence_complete"] is False
        assert summary["avg_monthly_net"] is None
        assert summary["trend"] is None


def test_expense_only_month_preserves_zero_income_without_inventing_margin() -> None:
    with isolated_database():
        cash_flow.daily_summary(days=7)
        with db.conn() as connection:
            connection.execute(
                "INSERT INTO expenses (date,category,amount) VALUES (?,?,?)",
                (business_today().isoformat(), "shipping", 25.0),
            )

        result = cash_flow.monthly_summary(months=1)
        assert result["evidence_complete"] is True
        assert result["months"] == [{
            "month": business_today().strftime("%Y-%m"),
            "income": 0.0,
            "expenses": 25.0,
            "net": -25.0,
            "margin_pct": None,
        }]


if __name__ == "__main__":
    test_fresh_user_db_and_canonical_daily_monthly_contract()
    test_in_window_incomplete_order_or_expense_fails_closed()
    test_known_out_of_window_defects_do_not_suppress_current_evidence()
    test_forecast_fails_closed_when_prior_month_evidence_is_incomplete()
    test_expense_only_month_preserves_zero_income_without_inventing_margin()
    print("cash flow canonical evidence: 5 passed")
