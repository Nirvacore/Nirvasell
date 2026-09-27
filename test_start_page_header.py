"""Regression coverage for opening the onboarding Start page."""
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
def isolated_page_modules(rendered_headers: list[dict]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.session_state = {}
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.columns = lambda count: [_Container() for _ in range(count)]
    fake_streamlit.form = lambda *_args, **_kwargs: _Container()
    fake_streamlit.button = lambda *_args, **_kwargs: False
    for name in (
        "progress", "caption", "markdown", "divider", "success", "write",
        "warning", "page_link", "balloons", "rerun",
    ):
        setattr(fake_streamlit, name, lambda *_args, **_kwargs: None)

    completed = ["api_key", "first_product", "first_generate", "first_export", "done"]
    replacements = {
        "streamlit": fake_streamlit,
        "db": _module("db", init=lambda: None),
        "user_settings": _module("user_settings", init=lambda: None),
        "onboarding": _module(
            "onboarding",
            autodetect_progress=lambda: None,
            progress=lambda: (5, 5),
            completed_steps=lambda: completed,
        ),
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components",
            friendly_error=lambda _error: None,
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


def test_start_page_imports_and_renders_page_header() -> None:
    rendered_headers: list[dict] = []
    page = Path(__file__).parent / "pages" / "0_🚀_Start.py"

    with isolated_page_modules(rendered_headers):
        runpy.run_path(str(page), run_name="__start_page_test__")

    assert rendered_headers == [
        {"icon": "🚀", "title": "onboard.title", "subtitle": "onboard.caption"},
    ]


if __name__ == "__main__":
    test_start_page_imports_and_renders_page_header()
    print("start page header: 1 passed")
