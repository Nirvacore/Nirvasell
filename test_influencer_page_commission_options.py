"""Regression coverage for Influencer page commission type options."""
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

    def selectbox(_label, options, **_kwargs):
        values = list(options)
        selected_options.append(values)
        return values[0]

    fake_streamlit.selectbox = selectbox
    fake_streamlit.form_submit_button = lambda *_args, **_kwargs: False
    for name in ("title", "caption", "divider", "subheader", "info", "success", "rerun"):
        setattr(fake_streamlit, name, lambda *_args, **_kwargs: None)

    tracker = _module(
        "influencer_tracker",
        COMMISSION_TYPES=["percentage", "flat_per_sale", "flat_monthly"],
        PLATFORMS=["tiktok", "facebook"],
        STATUSES={"pending": {}, "active": {}, "ended": {}},
        init=lambda: None,
        stats=lambda: {"total": 0, "active": 0, "total_sales": 0, "unpaid_commission": 0},
        all_influencers=lambda **_kwargs: [],
    )
    replacements = {
        "streamlit": fake_streamlit,
        "influencer_tracker": tracker,
        "theme": _module("theme", apply_theme=lambda: None),
        "auth": _module("auth", require_auth=lambda: None),
        "sidebar": _module("sidebar", render_sidebar=lambda: None),
        "i18n": _module("i18n", t=lambda key, **_kwargs: key),
        "i18n_inline": _module(
            "i18n_inline",
            inf_status_label=lambda key: key,
            inf_commission_label=lambda key: key,
        ),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        yield tracker
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def test_influencer_page_uses_commission_type_list_as_options() -> None:
    selected_options: list[list[str]] = []
    page = Path(__file__).parent / "pages" / "D9_🌟_Influencers.py"

    with isolated_page_modules(selected_options) as tracker:
        runpy.run_path(str(page), run_name="__influencer_page_test__")
        assert tracker.COMMISSION_TYPES in selected_options


if __name__ == "__main__":
    test_influencer_page_uses_commission_type_list_as_options()
    print("influencer page commission options: 1 passed")
