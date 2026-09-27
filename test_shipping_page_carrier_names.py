"""Regression coverage for rendering carrier names on the Shipping page."""
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


class _DataFrame:
    def __init__(self, data, index):
        self.data = data
        self.index = index


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page(rendered_tables: list[_DataFrame]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.session_state = {"lang": "en"}
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.columns = lambda spec: [
        _Container() for _ in range(spec if isinstance(spec, int) else len(spec))
    ]
    fake_streamlit.number_input = (
        lambda _label, **kwargs: kwargs.get("value", kwargs.get("min_value", 0))
    )
    fake_streamlit.checkbox = lambda _label, **kwargs: kwargs.get("value", False)
    fake_streamlit.markdown = lambda *_args, **_kwargs: None
    fake_streamlit.divider = lambda: None
    fake_streamlit.caption = lambda *_args, **_kwargs: None
    fake_streamlit.expander = lambda *_args, **_kwargs: _Container()
    fake_streamlit.dataframe = (
        lambda frame, **_kwargs: rendered_tables.append(frame)
    )

    fake_pandas = _module("pandas", DataFrame=_DataFrame)
    replacements = {
        "streamlit": fake_streamlit,
        "pandas": fake_pandas,
        "db": _module("db", init=lambda: None),
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components", page_header=lambda **_kwargs: None
        ),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    cached_real_modules = {
        name: sys.modules.pop(name, None)
        for name in ("i18n", "i18n_inline", "shipping_calc")
    }
    sys.modules.update(replacements)
    try:
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
        for name in ("i18n", "i18n_inline", "shipping_calc"):
            sys.modules.pop(name, None)
        for name, original in cached_real_modules.items():
            if original is not None:
                sys.modules[name] = original


def test_shipping_page_renders_canonical_carrier_names() -> None:
    rendered_tables: list[_DataFrame] = []
    page = Path(__file__).parent / "pages" / "a_🚚_Shipping.py"

    with isolated_page(rendered_tables):
        runpy.run_path(str(page), run_name="__shipping_page_test__")

    assert len(rendered_tables) == 1
    assert list(rendered_tables[0].data) == [
        "Kerry",
        "Flash Express",
        "J&T Express",
        "Thailand Post EMS",
        "Thailand Post Registered",
        "Best Express",
        "Ninja Van",
    ]


if __name__ == "__main__":
    test_shipping_page_renders_canonical_carrier_names()
    print("shipping page carrier names: 1 passed")
