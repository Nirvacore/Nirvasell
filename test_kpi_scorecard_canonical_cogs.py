"""Regression coverage for KPI COGS on the canonical orders schema."""
from __future__ import annotations

import sys
import tempfile
import types
import runpy
from contextlib import contextmanager
from datetime import date
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import db
import kpi_scorecard


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _MetricColumn:
    def __init__(self, metrics):
        self._metrics = metrics

    def metric(self, label, value, **_kwargs):
        self._metrics.append((label, value))


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


def test_kpi_scorecard_calculates_cogs_from_canonical_order_lines() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell_kpi_cogs_") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            today = date.today().isoformat()
            with db.conn() as connection:
                connection.execute(
                    """
                    INSERT INTO products
                        (sku, name, cost_price, sell_price, stock)
                    VALUES ('SKU-1', 'Product 1', 30, 100, 20)
                    """
                )
                connection.executemany(
                    """
                    INSERT INTO orders
                        (order_id, sku, platform, qty, unit_price,
                         total_price, order_date, status)
                    VALUES (?, 'SKU-1', 'web', ?, 100, ?, ?, ?)
                    """,
                    [
                        ("paid-1", 2, 200.0, today, "paid"),
                        ("cancelled-1", 10, 1_000.0, today, "cancelled"),
                    ],
                )

            metrics = kpi_scorecard.all_kpis(days=30)
            assert metrics["revenue"] == 200.0
            assert metrics["cogs"] == 60.0
            assert metrics["gross_profit"] == 140.0
            assert metrics["margin_pct"] == 70.0
        finally:
            db._resolve_path = original_resolver


def test_kpi_scorecard_marks_incomplete_cost_basis_unavailable() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell_kpi_missing_cogs_") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            today = date.today().isoformat()
            with db.conn() as connection:
                connection.execute(
                    """
                    INSERT INTO products
                        (sku, name, cost_price, sell_price, stock)
                    VALUES ('SKU-NO-COST', 'No cost yet', NULL, 100, 20)
                    """
                )
                connection.executemany(
                    """
                    INSERT INTO orders
                        (order_id, sku, platform, qty, unit_price,
                         total_price, order_date, status)
                    VALUES (?, ?, 'web', 1, 100, 100, ?, 'paid')
                    """,
                    [
                        ("missing-product", "SKU-MISSING", today),
                        ("missing-cost", "SKU-NO-COST", today),
                    ],
                )

            metrics = kpi_scorecard.all_kpis(days=30)
            assert metrics["cogs_complete"] is False
            assert metrics["missing_cost_rows"] == 2
            assert metrics["cogs"] is None
            assert metrics["gross_profit"] is None
            assert metrics["margin_pct"] is None
            assert metrics["net_profit"] is None
            assert isinstance(metrics["health_score"], int)
        finally:
            db._resolve_path = original_resolver


@contextmanager
def isolated_incomplete_page(metrics, warnings):
    fake_streamlit = _module("streamlit")
    fake_streamlit.segmented_control = lambda *_args, **_kwargs: 30
    fake_streamlit.columns = lambda count: [
        _MetricColumn(metrics) for _ in range(count)
    ]
    fake_streamlit.title = lambda *_args, **_kwargs: None
    fake_streamlit.caption = lambda *_args, **_kwargs: None
    fake_streamlit.html = lambda *_args, **_kwargs: None
    fake_streamlit.divider = lambda: None
    fake_streamlit.subheader = lambda *_args, **_kwargs: None
    fake_streamlit.warning = lambda message: warnings.append(message)
    fake_streamlit.write = lambda *_args, **_kwargs: None

    incomplete = {
        "health_score": 50,
        "revenue": 200.0,
        "orders": 2,
        "aov": 100.0,
        "customers": 2,
        "cogs": None,
        "cogs_complete": False,
        "missing_cost_rows": 1,
        "gross_profit": None,
        "margin_pct": None,
        "expenses": 25.0,
        "net_profit": None,
        "low_stock_count": 0,
        "out_of_stock": 0,
        "avg_rating": 0,
        "unanswered_reviews": 0,
        "cod_pending": 0,
        "cod_return_rate": 0,
    }
    fake_kpis = _module(
        "kpi_scorecard",
        all_kpis=lambda _days: incomplete,
        trend_comparison=lambda _days: {
            "revenue_change_pct": 0,
            "orders_change_pct": 0,
        },
    )
    replacements = {
        "streamlit": fake_streamlit,
        "kpi_scorecard": fake_kpis,
        "theme": _module("theme", apply_theme=lambda: None),
        "auth": _module("auth", require_auth=lambda: None),
        "i18n": _module("i18n", t=lambda key: key),
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


def test_kpi_page_does_not_present_profit_when_cost_basis_is_incomplete() -> None:
    metrics = []
    warnings = []
    page = Path(__file__).parent / "pages" / "E2_🏆_KPIs.py"
    with isolated_incomplete_page(metrics, warnings):
        runpy.run_path(str(page), run_name="__kpi_incomplete_page_test__")

    rendered = dict(metrics)
    assert rendered["kpi.gross_profit"] == "—"
    assert rendered["kpi.margin"] == "—"
    assert rendered["kpi.net_profit"] == "—"
    assert warnings


if __name__ == "__main__":
    test_kpi_scorecard_calculates_cogs_from_canonical_order_lines()
    test_kpi_scorecard_marks_incomplete_cost_basis_unavailable()
    test_kpi_page_does_not_present_profit_when_cost_basis_is_incomplete()
    print("KPI canonical COGS: 3 passed")
