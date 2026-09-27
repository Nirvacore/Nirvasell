"""Regression coverage for the order total rendered by Global Search."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


class _Column:
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
def isolated_page_modules(markdown_calls: list[str]):
    fake_streamlit = _module(
        "streamlit",
        set_page_config=lambda **_kwargs: None,
        columns=lambda count: [_Column() for _ in range(count)],
        divider=lambda: None,
        text_input=lambda *_args, **_kwargs: "order-1",
        caption=lambda *_args, **_kwargs: None,
        markdown=lambda body, **_kwargs: markdown_calls.append(body),
        info=lambda *_args, **_kwargs: None,
        stop=lambda: None,
        page_link=lambda *_args, **_kwargs: None,
    )
    replacements = {
        "streamlit": fake_streamlit,
        "db": _module("db", init=lambda: None),
        "global_search": _module(
            "global_search",
            quick_stats=lambda: {"products": 0, "orders": 1, "customers": 0},
            search=lambda _query: {
                "products": [],
                "orders": [{
                    "order_id": "order-1",
                    "sku": "SKU-1",
                    "platform": "fixture",
                    "total_price": 240.0,
                    "status": "paid",
                    "buyer_name": "Nirva buyer",
                    "order_date": "2026-09-07",
                }],
                "customers": [],
                "knowledge": [],
            },
        ),
        "knowledge_hub": _module(
            "knowledge_hub", init=lambda: None, stats=lambda: {"nodes": 0}
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
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def test_search_page_renders_canonical_order_total_price():
    markdown_calls: list[str] = []
    page = Path(__file__).parent / "pages" / "A2_🔎_Search.py"

    with isolated_page_modules(markdown_calls):
        runpy.run_path(str(page), run_name="__search_page_test__")

    rendered = "\n".join(markdown_calls)
    assert "฿240" in rendered
    assert "฿0" not in rendered


if __name__ == "__main__":
    test_search_page_renders_canonical_order_total_price()
    print("search page order total tests: 1 passed")
