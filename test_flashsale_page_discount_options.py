"""Regression coverage for Flash Sale page discount type options."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


class _Container:
    def __init__(self, selected_options=None):
        self.selected_options = selected_options

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __getattr__(self, _name):
        return lambda *_args, **kwargs: kwargs.get("value", 0)

    def selectbox(self, _label, options, **_kwargs):
        values = list(options)
        if self.selected_options is not None:
            self.selected_options.append(values)
        return values[0]


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page_modules(selected_options: list[list[str]]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.columns = lambda count: [_Container(selected_options) for _ in range(count)]
    fake_streamlit.tabs = lambda labels: [_Container() for _ in labels]
    fake_streamlit.form = lambda *_args, **_kwargs: _Container()
    fake_streamlit.expander = lambda *_args, **_kwargs: _Container()
    fake_streamlit.segmented_control = lambda *_args, **kwargs: kwargs.get("default")
    fake_streamlit.form_submit_button = lambda *_args, **_kwargs: False
    fake_streamlit.text_input = lambda *_args, **_kwargs: ""
    for name in (
        "title", "caption", "divider", "subheader", "info", "success",
        "error", "markdown", "rerun",
    ):
        setattr(fake_streamlit, name, lambda *_args, **_kwargs: None)

    flash_sale = _module(
        "flash_sale",
        DISCOUNT_TYPES=["percentage", "fixed", "free_shipping"],
        init=lambda: None,
        stats=lambda: {"total": 0, "active": 0, "upcoming": 0, "active_titles": []},
        active_now=lambda: [],
        all_sales=lambda **_kwargs: [],
    )
    replacements = {
        "streamlit": fake_streamlit,
        "flash_sale": flash_sale,
        "theme": _module("theme", apply_theme=lambda: None),
        "auth": _module("auth", require_auth=lambda: None),
        "sidebar": _module("sidebar", render_sidebar=lambda: None),
        "i18n": _module("i18n", t=lambda key, **_kwargs: key),
        "i18n_inline": _module(
            "i18n_inline",
            flash_status_label=lambda key: key,
            flash_discount_label=lambda key: key,
        ),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        yield flash_sale
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def test_flashsale_page_uses_discount_type_list_as_options() -> None:
    selected_options: list[list[str]] = []
    page = Path(__file__).parent / "pages" / "E0_⚡_FlashSale.py"

    with isolated_page_modules(selected_options) as flash_sale:
        runpy.run_path(str(page), run_name="__flashsale_page_test__")
        assert flash_sale.DISCOUNT_TYPES in selected_options


if __name__ == "__main__":
    test_flashsale_page_uses_discount_type_list_as_options()
    print("flash sale page discount options: 1 passed")
