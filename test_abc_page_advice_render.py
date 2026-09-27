"""Regression coverage for ABC investment-advice rendering."""
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
def isolated_page_modules(rendered_markdown: list[str]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.columns = lambda count: [_Container() for _ in range(count)]
    fake_streamlit.tabs = lambda labels: [_Container() for _ in labels]
    fake_streamlit.markdown = lambda value, **_kwargs: rendered_markdown.append(value)
    fake_streamlit.divider = lambda: None
    fake_streamlit.info = lambda *_args, **_kwargs: None
    fake_streamlit.stop = lambda: None

    summary = {
        "total_skus": 1,
        "A": {"count": 1, "revenue": 100.0, "stock_value": 60.0},
        "B": {"count": 0, "revenue": 0.0, "stock_value": 0.0},
        "C": {"count": 0, "revenue": 0.0, "stock_value": 0.0},
    }
    abc_analysis = _module(
        "abc_analysis",
        summary=lambda: summary,
        class_items=lambda _classification: [],
        investment_advice=lambda: [
            {
                "priority": "high",
                "action": "restock",
                "sku": "SKU-1",
                "name": "สินค้า",
                "stock": 7,
            },
        ],
    )

    def translate(key, **kwargs):
        if key == "abc.advice_stock":
            return "stock " + kwargs["n"]
        return key

    replacements = {
        "streamlit": fake_streamlit,
        "db": _module("db", init=lambda: None),
        "abc_analysis": abc_analysis,
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *_args, **_kwargs: None,
        ),
        "i18n": _module("i18n", t=translate),
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


def test_abc_page_renders_investment_advice_stock_text() -> None:
    rendered_markdown: list[str] = []
    page = Path(__file__).parent / "pages" / "l_🔤_ABC.py"

    with isolated_page_modules(rendered_markdown):
        runpy.run_path(str(page), run_name="__abc_page_test__")

    assert any("SKU-1" in html and "stock 7" in html for html in rendered_markdown)


if __name__ == "__main__":
    test_abc_page_renders_investment_advice_stock_text()
    print("abc page advice render: 1 passed")
