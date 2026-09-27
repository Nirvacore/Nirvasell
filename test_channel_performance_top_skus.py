"""Canonical evidence tests for channel-performance top SKUs."""
from __future__ import annotations

import runpy
import sys
import tempfile
import types
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
if "streamlit" not in sys.modules:
    sys.modules["streamlit"] = types.ModuleType("streamlit")

import channel_performance
import db


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
    with tempfile.TemporaryDirectory(prefix="nirvasell_channel_top_skus_") as temp:
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            db.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def test_top_skus_use_canonical_order_lines_and_platform_semantics() -> None:
    with isolated_database():
        today = date.today().isoformat()
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO orders "
                "(order_id,sku,platform,qty,total_price,order_date,status) "
                "VALUES (?,?,?,?,?,?,?)",
                [
                    ("direct-1", "SKU-A", None, 2, 180.0, today, "paid"),
                    ("direct-2", "SKU-A", None, 1, 90.0, today, "paid"),
                    ("direct-3", "SKU-B", None, 1, 50.0, today, "paid"),
                    ("cancelled", "SKU-X", None, 99, 9999.0, today, "Cancelled"),
                    ("returned", "SKU-Y", None, 88, 8888.0, today, "RETURNED"),
                    ("shopee", "SKU-Z", "shopee", 77, 7777.0, today, "paid"),
                ],
            )

        rows = channel_performance.top_skus_by_channel("direct", days=30)

        assert rows == [
            {"sku": "SKU-A", "total_qty": 3, "revenue": 270.0},
            {"sku": "SKU-B", "total_qty": 1, "revenue": 50.0},
        ]


def test_top_skus_fail_closed_on_missing_sku_qty_or_total_evidence() -> None:
    fixtures = [
        ("missing-sku", None, 1, 100.0),
        ("blank-sku", "  ", 1, 100.0),
        ("missing-qty", "SKU-A", None, 100.0),
        ("missing-total", "SKU-A", 1, None),
    ]
    for order_id, sku, qty, total_price in fixtures:
        with isolated_database():
            with db.conn() as connection:
                connection.executemany(
                    "INSERT INTO orders "
                    "(order_id,sku,platform,qty,total_price,order_date,status) "
                    "VALUES (?,?,?,?,?,?,?)",
                    [
                        (
                            "complete-row",
                            "SKU-COMPLETE",
                            "shopee",
                            2,
                            200.0,
                            date.today().isoformat(),
                            "paid",
                        ),
                        (
                            order_id,
                            sku,
                            "shopee",
                            qty,
                            total_price,
                            date.today().isoformat(),
                            "paid",
                        ),
                    ],
                )

            assert channel_performance.top_skus_by_channel("shopee", 30) is None


def test_top_skus_distinguish_complete_empty_evidence() -> None:
    with isolated_database():
        assert channel_performance.top_skus_by_channel("direct", 30) == []


def test_channels_page_warns_when_top_sku_evidence_is_incomplete() -> None:
    rendered = []
    fake_streamlit = _module("streamlit")
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.select_slider = lambda *_args, **_kwargs: 30
    fake_streamlit.columns = lambda count: [_Context() for _ in range(count)]
    fake_streamlit.divider = lambda: None
    fake_streamlit.info = lambda value: rendered.append(value)
    fake_streamlit.stop = lambda: None
    fake_streamlit.markdown = lambda value, **_kwargs: rendered.append(value)
    fake_streamlit.expander = lambda *_args, **_kwargs: _Context()
    fake_streamlit.metric = lambda *_args, **_kwargs: None
    fake_streamlit.warning = lambda value: rendered.append(value)

    channel = {
        "platform": "direct",
        "label": "Direct",
        "icon": "📞",
        "color": "#9a7569",
        "orders": 1,
        "revenue": 100.0,
        "avg_order": 100.0,
        "platform_fees": 0.0,
        "net_revenue": 100.0,
        "share_pct": 100.0,
    }
    replacements = {
        "streamlit": fake_streamlit,
        "db": _module("db", init=lambda: None),
        "channel_performance": _module(
            "channel_performance",
            summary=lambda _days: {
                "total_channels": 1,
                "top_channel": "Direct",
                "top_revenue": 100.0,
                "total_revenue": 100.0,
            },
            channel_stats=lambda _days: [channel],
            top_skus_by_channel=lambda *_args: None,
        ),
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *_args, **_kwargs: None,
        ),
        "i18n": _module("i18n", t=lambda key, **_kwargs: key),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    page = Path(__file__).parent / "pages" / "C5_📊_Channels.py"
    try:
        runpy.run_path(str(page), run_name="__channel_top_sku_page_test__")
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original

    assert any("unavailable" in value.lower() for value in rendered)


def test_focused_workflow_runs_top_sku_regression() -> None:
    workflow = (
        Path(__file__).parent / ".github" / "workflows" / "python-focused.yml"
    ).read_text(encoding="utf-8")
    assert '"channel_performance.py"' in workflow
    assert '"pages/C5_📊_Channels.py"' in workflow
    assert '"test_channel_performance_top_skus.py"' in workflow
    assert "python test_channel_performance_top_skus.py" in workflow
    assert "            channel_performance.py " + "\\" in workflow
    assert '            "pages/C5_📊_Channels.py" ' + "\\" in workflow
    assert "            test_channel_performance_top_skus.py " + "\\" in workflow


if __name__ == "__main__":
    test_top_skus_use_canonical_order_lines_and_platform_semantics()
    test_top_skus_fail_closed_on_missing_sku_qty_or_total_evidence()
    test_top_skus_distinguish_complete_empty_evidence()
    test_channels_page_warns_when_top_sku_evidence_is_incomplete()
    test_focused_workflow_runs_top_sku_regression()
    print("Channel performance top SKUs: 5 passed")
