"""Regression coverage for the shared Bangkok order business-date contract."""
from __future__ import annotations

import math
import sys
import tempfile
import types
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        fake_pandas.isna = lambda value: value is None or (
            isinstance(value, float) and math.isnan(value)
        )
        fake_pandas.notna = lambda value: not fake_pandas.isna(value)
        sys.modules["pandas"] = fake_pandas

if "streamlit" not in sys.modules:
    fake_streamlit = types.ModuleType("streamlit")
    fake_streamlit.session_state = {}
    sys.modules["streamlit"] = fake_streamlit

import daily_briefing
import db
import goals
import order_import
import profit_calendar
import sku_trends
import stock_turnover


BANGKOK = ZoneInfo("Asia/Bangkok")


class _Rows:
    def __init__(self, rows: list[tuple[object, dict]]):
        self._rows = rows

    @property
    def empty(self) -> bool:
        return not self._rows

    def iterrows(self):
        return iter(self._rows)


def _today_at(hour: int, minute: int) -> datetime:
    return datetime.combine(date.today(), time(hour, minute), tzinfo=BANGKOK)


def test_legacy_iso_datetimes_use_the_bangkok_calendar_date() -> None:
    cases = [
        (date.today().isoformat(), date.today()),
        (f"{date.today().isoformat()} 09:15:00", date.today()),
        (_today_at(0, 30).astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
         date.today()),
        (_today_at(23, 30).astimezone(timezone.utc).isoformat(), date.today()),
        ("2026-09-01T18:30:00Z", date(2026, 9, 2)),
        ("2026-09-01 00:30:00+07:00", date(2026, 9, 1)),
    ]

    for module in (goals, stock_turnover, profit_calendar, sku_trends):
        for value, expected in cases:
            assert module._canonical_date(value) == expected, (module.__name__, value)

    for module in (goals, stock_turnover, profit_calendar, sku_trends):
        for value in (
            None,
            "",
            "not-a-date",
            "2026-9-1",
            "2026-01-01T00:00",
            "2026-01-01T00:00:00.1234567890",
            "2026-01-01T00:00:00+0700",
        ):
            assert module._canonical_date(value) is None, (module.__name__, value)


def test_legacy_iso_datetime_is_included_in_bangkok_daily_briefing() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-date-briefing-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            legacy_utc = _today_at(0, 30).astimezone(timezone.utc).isoformat()
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO orders "
                    "(order_id,sku,platform,qty,total_price,order_date,status) "
                    "VALUES (?,?,?,?,?,?,?)",
                    ("legacy-utc", "SKU-1", "direct", 1, 125.0, legacy_utc, "paid"),
                )

            summary = daily_briefing._yesterday_summary(date.today().isoformat())
            assert summary["orders"] == 1
            assert summary["revenue"] == 125.0
        finally:
            db._resolve_path = original_resolver


def test_imported_datetimes_persist_one_business_date_for_every_consumer() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-date-import-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO products (sku,name,stock,cost_price,sell_price) "
                    "VALUES (?,?,?,?,?)",
                    ("SKU-1", "Product", 10, 25.0, 100.0),
                )

            rows = _Rows([
                (1, {
                    "order_id": "naive-local",
                    "sku": "SKU-1",
                    "platform": "direct",
                    "qty": 1,
                    "total_price": 100.0,
                    "order_date": datetime.combine(date.today(), time(9, 15)),
                    "buyer_name": "Buyer",
                    "buyer_phone": "0812345678",
                }),
                (2, {
                    "order_id": "aware-utc",
                    "sku": "SKU-1",
                    "platform": "direct",
                    "qty": 1,
                    "total_price": 150.0,
                    "order_date": _today_at(0, 30).astimezone(timezone.utc),
                    "buyer_name": "Buyer",
                    "buyer_phone": "0812345678",
                }),
            ])

            result = order_import.save_orders_report(rows)
            assert result.inserted == 2
            assert result.errors == ()

            expected = date.today().isoformat()
            with db.conn() as connection:
                saved_order_dates = [
                    row[0] for row in connection.execute(
                        "SELECT order_date FROM orders ORDER BY order_id"
                    )
                ]
                saved_customer_dates = [
                    row[0] for row in connection.execute(
                        "SELECT order_date FROM customer_orders ORDER BY order_id"
                    )
                ]
            assert saved_order_dates == [expected, expected]
            assert saved_customer_dates == [expected, expected]

            goal = goals._actual_evidence("orders", date.today().strftime("%Y-%m"))
            assert goal["complete"] is True
            assert goal["value"] == 2
            assert stock_turnover._analysis()["evidence_complete"] is True
            assert profit_calendar.daily_summary(days=1)["evidence_complete"] is True
            assert sku_trends.trend_summary(weeks=1)["evidence_complete"] is True
            briefing = daily_briefing._yesterday_summary(expected)
            assert briefing["orders"] == 2
            assert briefing["revenue"] == 250.0
        finally:
            db._resolve_path = original_resolver


def test_duplicate_legacy_order_normalizes_customer_history_date() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-order-date-duplicate-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            legacy_utc = _today_at(0, 30).astimezone(timezone.utc).isoformat()
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO orders "
                    "(order_id,sku,platform,qty,total_price,order_date,status,"
                    "buyer_name,buyer_phone) VALUES (?,?,?,?,?,?,?,?,?)",
                    ("legacy-duplicate", "SKU-1", "direct", 1, 125.0,
                     legacy_utc, "paid", "Buyer", "0812345678"),
                )

            result = order_import.save_orders_report(_Rows([
                (1, {
                    "order_id": "legacy-duplicate",
                    "sku": "SKU-1",
                    "platform": "direct",
                }),
            ]))

            assert result.inserted == 0
            assert result.skipped == 1
            assert result.errors == ()
            with db.conn() as connection:
                customer_date = connection.execute(
                    "SELECT order_date FROM customer_orders WHERE order_id = ?",
                    ("legacy-duplicate",),
                ).fetchone()[0]
            assert customer_date == date.today().isoformat()
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_legacy_iso_datetimes_use_the_bangkok_calendar_date()
    test_legacy_iso_datetime_is_included_in_bangkok_daily_briefing()
    test_imported_datetimes_persist_one_business_date_for_every_consumer()
    test_duplicate_legacy_order_normalizes_customer_history_date()
    print("order business date contract: 4 passed")
