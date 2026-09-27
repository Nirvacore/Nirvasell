"""Regression coverage for RFM overview average-spend rendering."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


class _Container:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page_modules(rendered_html: list[str]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.tabs = lambda labels: [_Container() for _ in labels]
    fake_streamlit.spinner = lambda *_args, **_kwargs: _Container()
    fake_streamlit.selectbox = lambda _label, options, **_kwargs: list(options)[0]
    fake_streamlit.html = lambda value: rendered_html.append(value)
    for name in ("title", "caption", "subheader", "info", "write", "divider"):
        setattr(fake_streamlit, name, lambda *_args, **_kwargs: None)

    rfm = _module(
        "rfm",
        SEGMENTS={
            "champions": {
                "icon": "👑",
                "color": "#4d6c5c",
                "action": "reward",
            },
        },
        segment_summary=lambda: [
            {"segment": "champions", "count": 2, "revenue": 300.0},
        ],
        customers_in_segment=lambda _segment: [],
        calculate_rfm=lambda: [],
    )
    replacements = {
        "streamlit": fake_streamlit,
        "rfm": rfm,
        "theme": _module("theme", apply_theme=lambda: None),
        "auth": _module("auth", require_auth=lambda: None),
        "sidebar": _module("sidebar", render_sidebar=lambda: None),
        "i18n": _module("i18n", t=lambda key, **_kwargs: key),
        "i18n_inline": _module(
            "i18n_inline",
            rfm_segment_label=lambda key: key,
            rfm_action_label=lambda key: key,
        ),
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


def test_rfm_page_derives_average_spent_from_summary_revenue_and_count() -> None:
    rendered_html: list[str] = []
    page = Path(__file__).parent / "pages" / "E8_🎯_RFM.py"

    with isolated_page_modules(rendered_html):
        runpy.run_path(str(page), run_name="__rfm_page_test__")

    assert any("฿150 avg" in html for html in rendered_html)


if __name__ == "__main__":
    test_rfm_page_derives_average_spent_from_summary_revenue_and_count()
    print("rfm page average spent: 1 passed")
