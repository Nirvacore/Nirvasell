"""Regression coverage for opening the Policies page."""
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


class _ColumnConfig:
    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: object()


class _Frame:
    def __init__(self, _value=None):
        pass


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page_modules(rendered_headers: list[dict]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.session_state = {}
    fake_streamlit.column_config = _ColumnConfig()
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.columns = lambda widths: [_Container() for _ in range(len(widths) if isinstance(widths, list) else widths)]
    fake_streamlit.expander = lambda *_args, **_kwargs: _Container()
    fake_streamlit.data_editor = lambda frame, **_kwargs: frame
    fake_streamlit.button = lambda *_args, **_kwargs: False
    for name in ("markdown", "caption", "success", "divider"):
        setattr(fake_streamlit, name, lambda *_args, **_kwargs: None)

    replacements = {
        "pandas": _module("pandas", DataFrame=_Frame),
        "streamlit": fake_streamlit,
        "db": _module("db", init=lambda: None),
        "fees": _module("fees"),
        "policy_watcher": _module(
            "policy_watcher",
            load_sources=lambda: [],
            history=lambda: [],
        ),
        "knowledge_hub": _module("knowledge_hub", init=lambda: None),
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components",
            friendly_error=lambda _error: None,
            page_header=lambda **kwargs: rendered_headers.append(kwargs),
        ),
        "i18n": _module("i18n", t=lambda key, **_kwargs: key),
        "i18n_inline": _module("i18n_inline", policy_source_label=lambda key: key),
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


def test_policies_page_imports_and_renders_page_header() -> None:
    rendered_headers: list[dict] = []
    page = Path(__file__).parent / "pages" / "E_📋_Policies.py"

    with isolated_page_modules(rendered_headers):
        runpy.run_path(str(page), run_name="__policies_page_test__")

    assert rendered_headers == [
        {"icon": "📋", "title": "policy.title", "subtitle": "policy.caption"},
    ]


if __name__ == "__main__":
    test_policies_page_imports_and_renders_page_header()
    print("policies page header: 1 passed")
