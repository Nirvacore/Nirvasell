"""Regression coverage for Goal page period options."""
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
def isolated_page_modules(selected_options: list[list[str]]):
    original_goal_tracker = sys.modules.pop("goal_tracker", None)
    fake_streamlit = _module("streamlit")
    fake_streamlit.session_state = {}
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.columns = lambda count: [_Container() for _ in range(count)]
    fake_streamlit.divider = lambda: None
    fake_streamlit.expander = lambda *_args, **_kwargs: _Container()
    fake_streamlit.form = lambda *_args, **_kwargs: _Container()

    def selectbox(_label, options, **_kwargs):
        values = list(options)
        selected_options.append(values)
        return values[0]

    fake_streamlit.selectbox = selectbox
    fake_streamlit.number_input = lambda *_args, **kwargs: kwargs.get("value", 0)
    fake_streamlit.text_input = lambda *_args, **_kwargs: ""
    fake_streamlit.form_submit_button = lambda *_args, **_kwargs: False
    fake_streamlit.markdown = lambda *_args, **_kwargs: None
    fake_streamlit.info = lambda *_args, **_kwargs: None
    fake_streamlit.stop = lambda: None
    fake_streamlit.rerun = lambda: None

    replacements = {
        "streamlit": fake_streamlit,
        "db": _module("db", init=lambda: None),
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *_args, **_kwargs: None,
            toast=lambda *_args, **_kwargs: None,
        ),
        "i18n": _module("i18n", t=lambda key, **_kwargs: key),
        "i18n_inline": _module(
            "i18n_inline",
            goal_type_label=lambda key: key,
            goal_type_unit=lambda _key: "THB",
            goal_period_label=lambda key: key,
        ),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        import goal_tracker

        goal_tracker.init = lambda: None
        goal_tracker.stats = lambda: {
            "total_active": 0,
            "on_track": 0,
            "off_track": 0,
        }
        goal_tracker.current_goals = lambda: []
        sys.modules["goal_tracker"] = goal_tracker
        yield goal_tracker
    finally:
        sys.modules.pop("goal_tracker", None)
        if original_goal_tracker is not None:
            sys.modules["goal_tracker"] = original_goal_tracker
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


def test_goals_page_uses_period_list_as_selectbox_options():
    selected_options: list[list[str]] = []
    page = Path(__file__).parent / "pages" / "C9_🎯_Goals.py"

    with isolated_page_modules(selected_options) as goal_tracker:
        runpy.run_path(str(page), run_name="__goals_page_test__")

        assert goal_tracker.PERIODS in selected_options


def test_page_module_isolation_restores_existing_goal_tracker():
    sentinel = _module("goal_tracker")
    original = sys.modules.get("goal_tracker")
    sys.modules["goal_tracker"] = sentinel
    try:
        with isolated_page_modules([]) as goal_tracker:
            assert goal_tracker is not sentinel
        assert sys.modules.get("goal_tracker") is sentinel
    finally:
        if original is None:
            sys.modules.pop("goal_tracker", None)
        else:
            sys.modules["goal_tracker"] = original


if __name__ == "__main__":
    test_goals_page_uses_period_list_as_selectbox_options()
    test_page_module_isolation_restores_existing_goal_tracker()
    print("goals page period options tests: 2 passed")
