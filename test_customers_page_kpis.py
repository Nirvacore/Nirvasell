"""Regression coverage for the Customers page KPI contract."""
from __future__ import annotations

import runpy
import shutil
import sys
import tempfile
import types
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import customers
import db


class _TabsReached(Exception):
    pass


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
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_customers_kpi_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path

    fake_streamlit = _module("streamlit")
    fake_streamlit.columns = lambda count: [
        _MetricColumn(metrics) for _ in range(count)
    ]
    fake_streamlit.title = lambda *_args, **_kwargs: None
    fake_streamlit.caption = lambda *_args, **_kwargs: None
    fake_streamlit.divider = lambda: None
    fake_streamlit.tabs = (
        lambda _labels: (_ for _ in ()).throw(_TabsReached())
    )

    replacements = {
        "streamlit": fake_streamlit,
        "theme": _module("theme", apply_theme=lambda: None),
        "auth": _module("auth", require_auth=lambda: None),
        "i18n": _module("i18n", t=lambda key: key),
        "sidebar": _module("sidebar", render_sidebar=lambda: None),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        customers.init()
        today = datetime.now().strftime("%Y-%m-%d")
        exact_cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        dormant = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        with db.conn() as connection:
            connection.executemany(
                """
                INSERT INTO customers
                    (name, last_order, order_count, total_spent)
                VALUES (?, ?, ?, ?)
                """,
                [
                    ("Current buyer", today, 1, 300.0),
                    ("Exact cutoff buyer", exact_cutoff, 1, 200.0),
                    ("Dormant buyer", dormant, 1, 100.0),
                    ("No orders yet", "", 0, 10_000.0),
                ],
            )
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_customers_page_uses_canonical_kpi_sources() -> None:
    metrics: list[tuple[str, object]] = []
    page = Path(__file__).parent / "pages" / "E3_👥_Customers.py"

    with isolated_page(metrics):
        try:
            runpy.run_path(str(page), run_name="__customers_page_test__")
        except _TabsReached:
            pass
        else:
            raise AssertionError("Customers page did not reach its tabs")

    assert metrics == [
        ("cust.kpi_total", 4),
        ("cust.kpi_vip", 0),
        ("cust.kpi_dormant", 2),
        ("cust.kpi_avg_spend", "฿200"),
    ]


if __name__ == "__main__":
    test_customers_page_uses_canonical_kpi_sources()
    print("customers page KPIs: 1 passed")
