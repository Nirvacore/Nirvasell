"""Regression coverage for channel performance on canonical order evidence."""
from __future__ import annotations

import tempfile
import sys
import types
import runpy
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import channel_perf
import db


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 9, 28, tzinfo=tz)


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def metric(self, *_args, **_kwargs):
        return None


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_channel_perf_") as temp:
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def test_platform_totals_use_canonical_order_lines_and_statuses() -> None:
    with isolated_database():
        today = date.today().isoformat()
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                [
                    ("SKU-SHOPEE", "Shopee product", 40.0, 100.0, 10),
                    ("SKU-DIRECT", "Direct product", 25.0, 75.0, 10),
                ],
            )
            connection.executemany(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,unit_price,total_price,order_date,status,"
                " buyer_name,buyer_phone) VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    ("paid-shopee", "SKU-SHOPEE", "shopee", 3, 100.0, 270.0,
                     today, "paid", "Alice", "111"),
                    ("paid-direct", "SKU-DIRECT", None, 2, 75.0, 150.0,
                     today, "paid", "Bob", "222"),
                    ("cancelled", "SKU-SHOPEE", "shopee", 50, 100.0, 5000.0,
                     today, "Cancelled", "Cancelled", "333"),
                    ("returned", "SKU-SHOPEE", "lazada", 25, 100.0, 2500.0,
                     today, "RETURNED", "Returned", "444"),
                    ("returned-direct", "SKU-DIRECT", None, 1, 75.0, 75.0,
                     today, "returned", "Direct return", "555"),
                ],
            )
            connection.execute(
                "CREATE TABLE returns (order_id TEXT, return_date TEXT)"
            )
            connection.execute(
                "INSERT INTO returns (order_id, return_date) VALUES (?, ?)",
                ("returned-direct", today),
            )

        rows = channel_perf.platform_comparison(days=30)
        by_platform = {row["platform"]: row for row in rows}

        assert set(by_platform) == {"shopee", "direct"}
        assert by_platform["shopee"] == {
            "platform": "shopee",
            "orders": 1,
            "customers": 1,
            "revenue": 270.0,
            "items_sold": 3,
            "aov": 270.0,
            "missing_total_price_rows": 0,
            "missing_qty_rows": 0,
            "missing_product_rows": 0,
            "missing_cost_rows": 0,
            "revenue_complete": True,
            "quantity_complete": True,
            "cogs_complete": True,
            "evidence_complete": True,
            "revenue_pct": 64.3,
            "cogs": 120.0,
            "gross_profit": 150.0,
            "margin": 55.6,
            "returns": 0,
            "return_rate": 0.0,
        }
        assert by_platform["direct"]["revenue"] == 150.0
        assert by_platform["direct"]["items_sold"] == 2
        assert by_platform["direct"]["cogs"] == 50.0
        assert by_platform["direct"]["returns"] == 1
        assert by_platform["direct"]["return_rate"] == 100.0

        summary = channel_perf.summary(days=30)
        assert summary["active_platforms"] == 2
        assert summary["total_orders"] == 2
        assert summary["total_revenue"] == 420.0


def test_platform_totals_fail_closed_on_incomplete_order_evidence() -> None:
    with isolated_database():
        today = date.today().isoformat()
        with db.conn() as connection:
            connection.execute(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES ('SKU-NO-COST','No cost',NULL,100,10)"
            )
            connection.executemany(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,unit_price,total_price,order_date,status) "
                "VALUES (?,?,?,?,?,?,?,'paid')",
                [
                    ("missing-product", "SKU-MISSING", "shopee", 1, 100.0, 100.0, today),
                    ("missing-cost", "SKU-NO-COST", "shopee", 1, 100.0, 100.0, today),
                    ("missing-qty", "SKU-NO-COST", "shopee", None, 100.0, 100.0, today),
                    ("missing-total", "SKU-NO-COST", "shopee", 1, 100.0, None, today),
                ],
            )

        row = channel_perf.platform_comparison(days=30)[0]

        assert row["missing_total_price_rows"] == 1
        assert row["missing_qty_rows"] == 1
        assert row["missing_product_rows"] == 1
        assert row["missing_cost_rows"] == 3
        assert row["revenue_complete"] is False
        assert row["quantity_complete"] is False
        assert row["cogs_complete"] is False
        assert row["evidence_complete"] is False
        assert row["revenue"] is None
        assert row["aov"] is None
        assert row["items_sold"] is None
        assert row["cogs"] is None
        assert row["gross_profit"] is None
        assert row["margin"] is None
        assert row["revenue_pct"] is None


def test_aov_uses_platform_revenue_per_distinct_order() -> None:
    with isolated_database():
        today = date.today().isoformat()
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO products (sku,name,cost_price,sell_price,stock) "
                "VALUES (?,?,?,?,?)",
                [
                    ("SKU-A", "Product A", 30.0, 100.0, 10),
                    ("SKU-B", "Product B", 20.0, 50.0, 10),
                ],
            )
            connection.executemany(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,total_price,order_date,status) "
                "VALUES (?,?,?,?,?,?,?)",
                [
                    ("order-one", "SKU-A", "shopee", 1, 100.0, today, "paid"),
                    ("order-one", "SKU-B", "shopee", 1, 50.0, today, "paid"),
                    ("order-two", "SKU-B", "shopee", 1, 50.0, today, "paid"),
                ],
            )

        row = channel_perf.platform_comparison(days=30)[0]

        assert row["orders"] == 2
        assert row["revenue"] == 200.0
        assert row["aov"] == 100.0


def test_summary_fails_closed_when_any_platform_totals_are_incomplete() -> None:
    with isolated_database():
        today = date.today().isoformat()
        with db.conn() as connection:
            connection.execute(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,total_price,order_date,status) "
                "VALUES ('unknown-cost','MISSING','shopee',1,100,?,'paid')",
                (today,),
            )

        result = channel_perf.summary(days=30)

        assert result["evidence_complete"] is False
        assert result["active_platforms"] == 1
        assert result["total_orders"] == 1
        assert result["top_platform"] == "—"
        assert result["top_revenue"] is None
        assert result["total_revenue"] is None
        assert result["best_margin"] == "—"
        assert result["best_margin_pct"] is None


def test_growth_uses_canonical_totals_and_fails_closed_per_month() -> None:
    with isolated_database():
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,total_price,order_date,status) "
                "VALUES (?,?,?,?,?,?,?)",
                [
                    ("direct-aug", "SKU-1", None, 1, 200.0, "2026-08-20", "paid"),
                    ("direct-sep", "SKU-1", None, 1, 300.0, "2026-09-15", "paid"),
                    ("direct-cancelled", "SKU-1", None, 1, 900.0,
                     "2026-08-20", "CANCELLED"),
                    ("shopee-missing-total", "SKU-2", "shopee", 1, None,
                     "2026-08-20", "paid"),
                ],
            )

        original_datetime = channel_perf.datetime
        channel_perf.datetime = _FixedDateTime
        try:
            rows = channel_perf.growth_by_platform(months=2)
        finally:
            channel_perf.datetime = original_datetime

        by_platform = {row["platform"]: row for row in rows}
        assert by_platform["direct"]["months"] == {
            "2026-08": 200.0,
            "2026-09": 300.0,
        }
        assert by_platform["direct"]["evidence_complete"] is True
        assert by_platform["direct"]["growth_pct"] == 50.0
        assert by_platform["shopee"]["months"] == {"2026-08": None}
        assert by_platform["shopee"]["evidence_complete"] is False
        assert by_platform["shopee"]["growth_pct"] is None


def test_channels_page_renders_unavailable_profit_without_false_zero() -> None:
    rendered_html = []
    fake_streamlit = _module("streamlit")
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.selectbox = lambda *_args, **_kwargs: 30
    fake_streamlit.info = lambda *_args, **_kwargs: None
    fake_streamlit.stop = lambda: None
    fake_streamlit.columns = lambda count: [_Context() for _ in range(count)]
    fake_streamlit.divider = lambda: None
    fake_streamlit.markdown = lambda value, **_kwargs: rendered_html.append(value)
    fake_streamlit.warning = lambda value: rendered_html.append(value)

    incomplete_platform = {
        "platform": "shopee",
        "revenue": None,
        "revenue_pct": None,
        "orders": 1,
        "customers": 1,
        "aov": None,
        "gross_profit": None,
        "margin": None,
        "return_rate": 0.0,
        "evidence_complete": False,
    }
    fake_channel_perf = _module(
        "channel_perf",
        platform_comparison=lambda _days: [incomplete_platform],
        summary=lambda _days: {
            "total_platforms": 1,
            "top_platform": "—",
            "top_revenue": None,
            "total_revenue": None,
            "best_margin": "—",
            "best_margin_pct": None,
            "evidence_complete": False,
        },
        growth_by_platform=lambda _months: [],
    )
    replacements = {
        "streamlit": fake_streamlit,
        "channel_perf": fake_channel_perf,
        "db": _module("db", init=lambda: None),
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *_args, **_kwargs: None,
        ),
        "i18n": _module("i18n", t=lambda key, **_kwargs: key),
        "i18n_inline": _module("i18n_inline", platform_name=lambda value: value),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    page = Path(__file__).parent / "pages" / "w_🌐_Channels.py"
    try:
        runpy.run_path(str(page), run_name="__channel_evidence_page_test__")
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original

    assert any("—" in html for html in rendered_html)


def test_g0_page_renders_unavailable_revenue_without_false_zero() -> None:
    rendered_html = []
    fake_streamlit = _module("streamlit")
    fake_streamlit.title = lambda *_args, **_kwargs: None
    fake_streamlit.caption = lambda *_args, **_kwargs: None
    fake_streamlit.segmented_control = lambda *_args, **_kwargs: 30
    fake_streamlit.columns = lambda count: [_Context() for _ in range(count)]
    fake_streamlit.divider = lambda: None
    fake_streamlit.tabs = lambda _labels: [_Context(), _Context()]
    fake_streamlit.info = lambda *_args, **_kwargs: None
    fake_streamlit.html = lambda value: rendered_html.append(value)
    fake_streamlit.slider = lambda *_args, **_kwargs: 3
    fake_streamlit.write = lambda *_args, **_kwargs: None
    fake_streamlit.warning = lambda value: rendered_html.append(value)

    incomplete_platform = {
        "platform": "direct",
        "revenue": None,
        "orders": 1,
        "aov": None,
        "return_rate": 0.0,
        "evidence_complete": False,
    }
    replacements = {
        "streamlit": fake_streamlit,
        "channel_perf": _module(
            "channel_perf",
            summary=lambda days: {
                "total_revenue": None,
                "total_orders": 1,
                "active_platforms": 1,
                "evidence_complete": False,
            },
            platform_comparison=lambda days: [incomplete_platform],
            growth_by_platform=lambda months: [{
                "platform": "direct",
                "months": {"2026-07": 100.0, "2026-08": None},
                "growth_pct": None,
                "evidence_complete": False,
            }],
        ),
        "theme": _module("theme", apply_theme=lambda: None),
        "auth": _module("auth", require_auth=lambda: None),
        "sidebar": _module("sidebar", render_sidebar=lambda: None),
        "i18n": _module("i18n", t=lambda key, **_kwargs: key),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    page = Path(__file__).parent / "pages" / "G0_📡_ChannelPerf.py"
    try:
        runpy.run_path(str(page), run_name="__g0_channel_evidence_page_test__")
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original

    assert any("—" in html for html in rendered_html)
    assert any("2026-07" in html and "฿100" in html for html in rendered_html)


def test_focused_workflow_runs_channel_performance_regression() -> None:
    workflow = (Path(__file__).parent / ".github" / "workflows" /
                "python-focused.yml").read_text(encoding="utf-8")
    assert '"channel_perf.py"' in workflow
    assert '"test_channel_perf_canonical_totals.py"' in workflow
    assert '"pages/G0_📡_ChannelPerf.py"' in workflow
    assert "python test_channel_perf_canonical_totals.py" in workflow
    assert "            channel_perf.py " + "\\" in workflow
    assert "            test_channel_perf_canonical_totals.py " + "\\" in workflow
    assert '            "pages/G0_📡_ChannelPerf.py" ' + "\\" in workflow


if __name__ == "__main__":
    test_platform_totals_use_canonical_order_lines_and_statuses()
    test_platform_totals_fail_closed_on_incomplete_order_evidence()
    test_aov_uses_platform_revenue_per_distinct_order()
    test_summary_fails_closed_when_any_platform_totals_are_incomplete()
    test_growth_uses_canonical_totals_and_fails_closed_per_month()
    test_channels_page_renders_unavailable_profit_without_false_zero()
    test_g0_page_renders_unavailable_revenue_without_false_zero()
    test_focused_workflow_runs_channel_performance_regression()
    print("Channel performance canonical totals: 8 passed")
