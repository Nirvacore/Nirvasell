"""Regression coverage for the Forecast page/backend contract."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


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
def isolated_page(metrics: list[tuple[str, object]], html: list[str]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.segmented_control = lambda *_args, **_kwargs: 30
    fake_streamlit.spinner = lambda *_args, **_kwargs: _Context()
    fake_streamlit.columns = lambda count: [
        _MetricColumn(metrics) for _ in range(count)
    ]
    fake_streamlit.title = lambda *_args, **_kwargs: None
    fake_streamlit.caption = lambda *_args, **_kwargs: None
    fake_streamlit.divider = lambda: None
    fake_streamlit.error = lambda *_args, **_kwargs: None
    fake_streamlit.tabs = lambda labels: [_Context() for _ in labels]
    fake_streamlit.info = lambda *_args, **_kwargs: None
    fake_streamlit.success = lambda *_args, **_kwargs: None
    fake_streamlit.subheader = lambda *_args, **_kwargs: None
    fake_streamlit.html = lambda body: html.append(body)

    forecast = {
        "sku": "SKU-1",
        "trend": "rising",
        "forecast_qty": 12,
        "forecast_revenue": 1_200.0,
        "avg_weekly_recent": 4.5,
        "confidence": "high",
    }
    fake_forecast = _module(
        "demand_forecast",
        summary=lambda: {
            "skus_forecasted": 7,
            "rising_skus": 3,
            "declining_skus": 2,
        },
        stockout_risk=lambda horizon_days: [{
            "sku": "SKU-RISK",
            "current_stock": 1,
            "forecast_need": 4,
            "deficit": 3,
            "coverage_days": 5,
            "risk_level": "high",
        }],
        forecast_all=lambda horizon_days, limit=50: [forecast],
    )

    replacements = {
        "streamlit": fake_streamlit,
        "demand_forecast": fake_forecast,
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


def test_forecast_page_uses_canonical_summary_and_row_fields() -> None:
    metrics: list[tuple[str, object]] = []
    html: list[str] = []
    page = Path(__file__).parent / "pages" / "F2_🔮_Forecast.py"

    with isolated_page(metrics, html):
        runpy.run_path(str(page), run_name="__forecast_page_test__")

    assert metrics == [
        ("fcast.kpi_skus", 7),
        ("fcast.kpi_rising", 3),
        ("fcast.kpi_declining", 2),
        ("fcast.kpi_stockout", 1),
    ]
    assert any("4.5fcast.per_week" in fragment for fragment in html)


if __name__ == "__main__":
    test_forecast_page_uses_canonical_summary_and_row_fields()
    print("forecast page contract: 1 passed")
