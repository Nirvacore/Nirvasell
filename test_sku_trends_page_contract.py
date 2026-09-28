"""Regression coverage for SKU-trend page evidence and field contracts."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


class StopExecution(Exception):
    pass


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def metric(self, *args, **_kwargs):
        METRICS.append(args)


METRICS: list[tuple] = []
CLAIMS: list[str] = []


def module(name: str, **attrs):
    result = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(result, key, value)
    return result


@contextmanager
def replaced_modules(replacements: dict[str, types.ModuleType]):
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


def fake_streamlit(warnings: list[str]):
    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.title = lambda *_args, **_kwargs: None
    st.caption = lambda *_args, **_kwargs: None
    st.columns = lambda count: [Context() for _ in range(count)]
    st.tabs = lambda labels: [Context() for _ in labels]
    st.slider = lambda *_args, **_kwargs: 4
    st.warning = lambda value: warnings.append(str(value))
    st.info = lambda *_args, **_kwargs: None
    st.success = lambda *_args, **_kwargs: None
    st.error = lambda *_args, **_kwargs: None
    st.divider = lambda: None
    st.write = lambda value: CLAIMS.append(str(value))
    st.html = lambda value: CLAIMS.append(str(value))
    st.markdown = lambda value, **_kwargs: CLAIMS.append(str(value))
    st.stop = lambda: (_ for _ in ()).throw(StopExecution())
    return st


def base_replacements(st, trends):
    return {
        "streamlit": st,
        "sku_trends": trends,
        "db": module("db", init=lambda: None),
        "theme": module("theme", apply_theme=lambda: None),
        "auth": module("auth", require_auth=lambda: None),
        "sidebar": module("sidebar", render_sidebar=lambda: None),
        "_theme": module("_theme", apply=lambda: None),
        "_auth_gate": module("_auth_gate", require_auth=lambda: None),
        "_sidebar": module("_sidebar", render=lambda: None),
        "_components": module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *args, **_kwargs: METRICS.append(args),
        ),
        "i18n": module("i18n", t=lambda key, **kwargs: key + str(kwargs or "")),
    }


def test_both_pages_stop_before_claims_when_trend_evidence_is_incomplete():
    incomplete = {
        "evidence_complete": False,
        "missing_order_evidence_rows": 1,
        "missing_product_evidence_rows": 0,
        "items": [],
        "total_skus": None,
        "rising": None,
        "declining": None,
        "stable": None,
        "top_gainer": None,
        "top_gainer_pct": None,
    }
    trends = module(
        "sku_trends",
        summary=lambda: incomplete,
        new_products_summary=lambda days: {**incomplete, "missing_product_evidence_rows": 0},
        weekly_trend=lambda weeks=4: [],
        rising_stars=lambda min_change=20: [],
        declining=lambda min_change=-20: [],
        new_products=lambda days=14: [],
    )

    for page_name in ["H6_📈_SKUTrends.py", "t_📊_Trends.py"]:
        METRICS.clear()
        CLAIMS.clear()
        warnings: list[str] = []
        stopped = False
        with replaced_modules(base_replacements(fake_streamlit(warnings), trends)):
            try:
                runpy.run_path(
                    str(Path(__file__).parent / "pages" / page_name),
                    run_name="__sku_trends_incomplete_page_test__",
                )
            except StopExecution:
                stopped = True

        assert stopped, page_name
        assert warnings, page_name
        assert not METRICS, page_name
        assert not CLAIMS, page_name


def test_h6_page_uses_canonical_summary_item_and_week_series_fields():
    METRICS.clear()
    CLAIMS.clear()
    warnings: list[str] = []
    item = {
        "sku": "SKU-1",
        "name": "Product",
        "qty_this_week": 3,
        "qty_last_week": 2,
        "qty_change_pct": 50.0,
        "rev_this_week": 60.0,
        "rev_last_week": 20.0,
        "rev_change_pct": 200.0,
        "trend": "rising",
        "weeks": {
            "This Week": {"qty": 3, "revenue": 60.0},
            "W-1": {"qty": 2, "revenue": 20.0},
        },
    }
    stable_item = {
        **item,
        "sku": "SKU-STABLE",
        "name": "Stable",
        "qty_this_week": 23,
        "qty_last_week": 20,
        "qty_change_pct": 15.0,
        "rev_change_pct": 15.0,
        "trend": "stable",
    }
    trend_summary = {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "items": [item, stable_item],
        "total_skus": 2,
        "rising": 1,
        "declining": 0,
        "stable": 0,
        "top_gainer": "SKU-1",
        "top_gainer_pct": 200.0,
    }
    new_item = {
        "sku": "SKU-NEW", "name": "New", "total_sold": 2,
        "total_revenue": 45.0,
    }
    new_summary = {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "items": [new_item],
    }
    trends = module(
        "sku_trends",
        summary=lambda: trend_summary,
        trend_summary=lambda weeks=4: {
            "evidence_complete": True,
            "missing_order_evidence_rows": 0,
            "missing_product_evidence_rows": 0,
            "items": [item],
        },
        new_products_summary=lambda days: new_summary,
        weekly_trend=lambda weeks=4: [item],
        rising_stars=lambda min_change=20: [item],
        declining=lambda min_change=-20: [],
        new_products=lambda days=14: [new_item],
    )

    with replaced_modules(base_replacements(fake_streamlit(warnings), trends)):
        runpy.run_path(
            str(Path(__file__).parent / "pages" / "H6_📈_SKUTrends.py"),
            run_name="__sku_trends_complete_page_test__",
        )

    assert not warnings
    assert [metric[1] for metric in METRICS[:4]] == [1, 0, 1, 2]
    rendered = "\n".join(CLAIMS)
    assert "+50.0%" in rendered
    assert "+15.0%" not in rendered
    assert "prev 2 → 3" in rendered
    assert "SKU-NEW" in rendered
    assert "This Week" in rendered
    assert "W-1" in rendered


if __name__ == "__main__":
    test_both_pages_stop_before_claims_when_trend_evidence_is_incomplete()
    test_h6_page_uses_canonical_summary_item_and_week_series_fields()
    print("sku trends page contract: 2 passed")
