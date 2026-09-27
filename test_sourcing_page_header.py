"""Regression coverage for opening the Sourcing page."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


class _StopPage(Exception):
    pass


class _Container:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: False


class _Query:
    def fetchone(self):
        return (0,)


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, *_args, **_kwargs):
        return _Query()


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page_modules(rendered_headers: list[dict]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.columns = lambda widths: [_Container() for _ in range(len(widths) if isinstance(widths, list) else widths)]
    fake_streamlit.markdown = lambda *_args, **_kwargs: None
    fake_streamlit.success = lambda *_args, **_kwargs: None
    fake_streamlit.button = lambda *_args, **_kwargs: False
    fake_streamlit.stop = lambda: (_ for _ in ()).throw(_StopPage())

    replacements = {
        "pandas": _module("pandas"),
        "streamlit": fake_streamlit,
        "db": _module("db", init=lambda: None, conn=lambda: _Connection()),
        "sourcing": _module("sourcing", auto_group_all=lambda: {}),
        "fees": _module("fees"),
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components",
            empty_state=lambda **_kwargs: None,
            page_header=lambda **kwargs: rendered_headers.append(kwargs),
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


def test_sourcing_page_imports_and_renders_page_header() -> None:
    rendered_headers: list[dict] = []
    page = Path(__file__).parent / "pages" / "D_🔀_Sourcing.py"

    with isolated_page_modules(rendered_headers):
        try:
            runpy.run_path(str(page), run_name="__sourcing_page_test__")
        except _StopPage:
            pass

    assert rendered_headers == [
        {"icon": "🔀", "title": "sourcing.title", "subtitle": "sourcing.caption"},
    ]


if __name__ == "__main__":
    test_sourcing_page_imports_and_renders_page_header()
    print("sourcing page header: 1 passed")
