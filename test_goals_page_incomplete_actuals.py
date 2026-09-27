"""Regression coverage for fail-closed output on the legacy Goals page."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def module(name: str, **attrs):
    result = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(result, key, value)
    return result


@contextmanager
def replaced_modules(replacements):
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


def test_page_does_not_publish_exact_progress_when_actual_evidence_is_incomplete() -> None:
    rendered: list[str] = []
    warnings: list[str] = []
    metrics: list[tuple] = []

    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.expander = lambda *_args, **_kwargs: Context()
    st.form = lambda *_args, **_kwargs: Context()
    st.columns = lambda count: [Context() for _ in range(count)]
    st.caption = lambda *_args, **_kwargs: None
    st.number_input = lambda *_args, **kwargs: kwargs.get("value", 0)
    st.form_submit_button = lambda *_args, **_kwargs: False
    st.rerun = lambda: None
    st.info = lambda *_args, **_kwargs: None
    st.stop = lambda: None
    st.divider = lambda: None
    st.warning = lambda value, **_kwargs: warnings.append(str(value))
    st.markdown = lambda value, **_kwargs: rendered.append(str(value))

    incomplete_goal = {
        "metric": "profit",
        "target": 100.0,
        "actual": None,
        "pct": None,
        "pace_pct": 50.0,
        "status": "unavailable",
        "evidence_complete": False,
        "missing_evidence_rows": 2,
        "days_elapsed": 15,
        "days_remaining": 15,
        "label": "Profit",
        "icon": "💵",
        "unit": "฿",
    }
    fake_goals = module(
        "goals",
        METRICS={"profit": {"icon": "💵"}},
        init=lambda: None,
        set_goal=lambda *_args: None,
        goals_for_period=lambda _period: [incomplete_goal],
        summary=lambda _period: {
            "achieved": 0,
            "on_track": 0,
            "behind": 0,
            "at_risk": 0,
            "unavailable": 1,
        },
    )
    replacements = {
        "streamlit": st,
        "db": module("db", init=lambda: None),
        "goals": fake_goals,
        "_theme": module("_theme", apply=lambda: None),
        "_sidebar": module("_sidebar", render=lambda: None),
        "_auth_gate": module("_auth_gate", require_auth=lambda: None),
        "_components": module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *args, **_kwargs: metrics.append(args),
            toast=lambda *_args, **_kwargs: None,
        ),
        "i18n": module("i18n", t=lambda key, **_kwargs: key),
        "i18n_inline": module("i18n_inline", goal_type_label=lambda key: key),
    }

    with replaced_modules(replacements):
        runpy.run_path(
            str(Path(__file__).parent / "pages" / "x_🎯_Goals.py"),
            run_name="__goals_incomplete_page_test__",
        )

    combined = "\n".join(rendered)
    assert warnings
    assert "2" in warnings[0]
    assert "unavailable" in combined.lower()
    assert "฿— / ฿100" in combined
    assert "None%" not in combined
    assert "actual" not in combined or "฿0 / ฿100" not in combined
    assert [metric[1] for metric in metrics] == ["0", "0", "0", "0"]


if __name__ == "__main__":
    test_page_does_not_publish_exact_progress_when_actual_evidence_is_incomplete()
    print("goals incomplete actual page: 1 passed")
