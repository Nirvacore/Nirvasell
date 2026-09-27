"""Regression coverage for Daily Briefing's new-customer KPI."""
from __future__ import annotations

import runpy
import shutil
import sys
import tempfile
import types
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import daily_briefing as briefing
import customers
import db


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _MetricColumn:
    def __init__(self, metrics: list[tuple[str, object]]):
        self._metrics = metrics

    def metric(self, label, value, **_kwargs):
        self._metrics.append((label, value))


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page(metrics: list[tuple[str, object]]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.session_state = {}
    fake_streamlit.button = lambda *_args, **_kwargs: False
    fake_streamlit.spinner = lambda *_args, **_kwargs: _Context()
    fake_streamlit.columns = lambda count: [
        _MetricColumn(metrics) for _ in range(count)
    ]
    fake_streamlit.title = lambda *_args, **_kwargs: None
    fake_streamlit.caption = lambda *_args, **_kwargs: None
    fake_streamlit.subheader = lambda *_args, **_kwargs: None
    fake_streamlit.divider = lambda: None
    fake_streamlit.info = lambda *_args, **_kwargs: None

    fake_briefing = _module(
        "daily_briefing",
        generate=lambda: {
            "date": "2026-09-28",
            "yesterday": {
                "orders": 6,
                "revenue": 1_250.0,
                "new_customers": 4,
            },
            "quick_stats": {},
            "alerts": [],
            "today_tasks": [],
        },
    )
    replacements = {
        "streamlit": fake_streamlit,
        "daily_briefing": fake_briefing,
        "theme": _module("theme", apply_theme=lambda: None),
        "auth": _module("auth", require_auth=lambda: None),
        "i18n": _module("i18n", t=lambda key: key),
        "i18n_inline": _module(
            "i18n_inline",
            brief_task_text=lambda task: str(task),
            brief_alert_text=lambda alert: str(alert),
        ),
        "sidebar": _module("sidebar", render_sidebar=lambda: None),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def test_daily_briefing_page_shows_new_customers_with_matching_label() -> None:
    metrics: list[tuple[str, object]] = []
    page = Path(__file__).parent / "pages" / "G7_🌅_DailyBriefing.py"

    with isolated_page(metrics):
        runpy.run_path(str(page), run_name="__daily_briefing_page_test__")

    assert metrics == [
        ("brief.y_orders", 6),
        ("brief.y_revenue", "฿1,250"),
        ("brief.y_customers", 4),
        ("brief.y_returns", 0),
    ]


def test_yesterday_summary_counts_only_first_time_customers() -> None:
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_briefing_customers_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    older = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
    try:
        db.init()
        customers.init()
        with db.conn() as connection:
            connection.executemany(
                """
                INSERT INTO orders
                    (order_id, sku, platform, qty, total_price, order_date,
                     buyer_phone, buyer_name)
                VALUES (?, ?, 'web', 1, 100, ?, ?, ?)
                """,
                [
                    ("old-first", "SKU-1", older, "0811111111", "Returning"),
                    ("old-again", "SKU-1", yesterday, "0811111111", "Returning"),
                    ("new-1", "SKU-1", yesterday, "0822222222", "New Phone"),
                    ("new-2", "SKU-2", yesterday, "0822222222", "New Phone"),
                    ("new-name", "SKU-1", yesterday, "", "New Name Only"),
                ],
            )

        returning_id = customers.find_or_create(name="Alice Smith")
        customers.record_order(
            customer_id=returning_id,
            order_id="old-first",
            order_date=older,
        )
        assert customers.find_or_create(name="alice smith") == returning_id
        customers.record_order(
            customer_id=returning_id,
            order_id="old-again",
            order_date=yesterday,
        )

        phone_later_id = customers.find_or_create(name="Phone Later")
        customers.record_order(
            customer_id=phone_later_id,
            order_id="phone-later-first",
            order_date=older,
        )
        assert customers.find_or_create(
            name="Phone Later", phone="0833333333"
        ) == phone_later_id
        customers.record_order(
            customer_id=phone_later_id,
            order_id="phone-later-again",
            order_date=yesterday,
        )

        new_phone_id = customers.find_or_create(
            name="New Phone", phone="0822222222"
        )
        customers.record_order(
            customer_id=new_phone_id,
            order_id="new-1",
            order_date=yesterday,
        )
        customers.record_order(
            customer_id=new_phone_id,
            order_id="new-2",
            order_date=yesterday,
        )
        new_name_id = customers.find_or_create(name="New Name Only")
        customers.record_order(
            customer_id=new_name_id,
            order_id="new-name",
            order_date=yesterday,
        )

        summary = briefing._yesterday_summary(yesterday)
        assert summary["new_customers"] == 2
    finally:
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_daily_briefing_page_shows_new_customers_with_matching_label()
    test_yesterday_summary_counts_only_first_time_customers()
    print("daily briefing new customers: 2 passed")
