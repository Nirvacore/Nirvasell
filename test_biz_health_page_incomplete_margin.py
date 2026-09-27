"""Regression coverage for unavailable business-health cost evidence."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page_modules(rendered: list[str], warnings: list[str]):
    fake_streamlit = _module("streamlit")
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.markdown = lambda value, **_kwargs: rendered.append(value)
    fake_streamlit.warning = lambda value, **_kwargs: warnings.append(value)
    fake_streamlit.divider = lambda: None
    fake_streamlit.caption = lambda *_args, **_kwargs: None

    incomplete_result = {
        "overall": 85,
        "grade": "A",
        "status": "incomplete",
        "dimensions": {"margin": None},
        "weights": {"margin": 0.2},
        "evidence": {
            "margin": {"complete": False, "missing_evidence_rows": 2},
        },
    }
    fake_health = _module(
        "biz_health",
        calculate=lambda: incomplete_result,
        dimension_details=lambda: [
            {"key": "margin", "icon": "💰", "score": None, "weight": 20,
             "status": "unavailable"},
            {"key": "revenue", "icon": "📈", "score": 75, "weight": 20,
             "status": "good"},
        ],
    )
    replacements = {
        "streamlit": fake_streamlit,
        "db": _module("db", init=lambda: None),
        "biz_health": fake_health,
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module("_components", page_header=lambda **_kwargs: None),
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


def test_incomplete_margin_suppresses_exact_overall_health_score() -> None:
    rendered: list[str] = []
    warnings: list[str] = []
    page = Path(__file__).parent / "pages" / "v_🏥_BizHealth.py"

    with isolated_page_modules(rendered, warnings):
        runpy.run_path(str(page), run_name="__biz_health_page_test__")

    combined = "\n".join(rendered)
    assert ">85</div>" not in combined
    assert ">—</div>" in combined
    assert "—/100" in combined
    assert "Incomplete evidence" in combined
    assert warnings


if __name__ == "__main__":
    test_incomplete_margin_suppresses_exact_overall_health_score()
    print("business health incomplete margin page: 1 passed")
