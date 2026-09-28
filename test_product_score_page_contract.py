"""Canonical Product Score page and truthful-copy regressions."""

from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


PAGE = Path(__file__).parent / "pages" / "B7_🏅_ProductScore.py"


class StopExecution(Exception):
    pass


class AuthStop(Exception):
    pass


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


EVENTS: list[tuple[str, object]] = []


def fake_streamlit():
    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.select_slider = lambda *_args, **_kwargs: 7
    st.selectbox = lambda _label, options, **_kwargs: options[0]
    st.columns = lambda count: [Context() for _ in range(count)]
    st.divider = lambda: None
    st.caption = lambda value: EVENTS.append(("caption", value))
    st.markdown = lambda value, **_kwargs: EVENTS.append(("markdown", value))
    st.info = lambda value: EVENTS.append(("info", value))
    st.warning = lambda value: EVENTS.append(("warning", value))
    st.stop = lambda: (_ for _ in ()).throw(StopExecution())
    return st


def replacements(*, product_score, require_auth):
    return {
        "streamlit": fake_streamlit(),
        "db": module("db", init=lambda: EVENTS.append(("call", "db.init"))),
        "product_score": product_score,
        "_theme": module("_theme", apply=lambda: None),
        "_sidebar": module("_sidebar", render=lambda: None),
        "_auth_gate": module("_auth_gate", require_auth=require_auth),
        "_components": module(
            "_components",
            page_header=lambda **kwargs: EVENTS.append(("header", kwargs)),
            metric_with_hint=lambda *args, **_kwargs: EVENTS.append(("metric", args)),
        ),
        "i18n": module("i18n", t=lambda key, **_kwargs: key),
    }


def test_terminating_auth_prevents_database_and_score_calls() -> None:
    EVENTS.clear()
    product_score = module(
        "product_score",
        summary=lambda *_args: EVENTS.append(("call", "summary")),
        calculate=lambda *_args: EVENTS.append(("call", "calculate")),
    )
    with replaced_modules(replacements(
        product_score=product_score,
        require_auth=lambda: (_ for _ in ()).throw(AuthStop()),
    )):
        try:
            runpy.run_path(str(PAGE), run_name="__product_score_auth_test__")
        except AuthStop:
            pass
        else:
            raise AssertionError("authentication stop must terminate the page")
    assert not any(kind == "call" for kind, _value in EVENTS)


def test_selected_window_drives_summary_and_incomplete_evidence_stops_kpis() -> None:
    EVENTS.clear()
    calls: list[int] = []

    def summary(days):
        calls.append(days)
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": 2,
            "missing_product_evidence_rows": 1,
            "items": [],
            "total_skus": None,
            "avg_score": None,
            "quadrants": None,
        }

    stopped = False
    with replaced_modules(replacements(
        product_score=module("product_score", summary=summary),
        require_auth=lambda: {},
    )):
        try:
            runpy.run_path(str(PAGE), run_name="__product_score_incomplete_test__")
        except StopExecution:
            stopped = True
    assert stopped is True
    assert calls == [7]
    assert ("warning", "pscore.incomplete") in EVENTS
    assert not any(kind == "metric" for kind, _value in EVENTS)


def test_complete_page_reuses_the_selected_window_summary_items() -> None:
    EVENTS.clear()
    calls: list[int] = []
    item = {
        "rank": 1,
        "quadrant": "star",
        "quadrant_icon": "⭐",
        "sku": "SKU-7",
        "name": "Product",
        "revenue": 700.0,
        "margin_pct": 60.0,
        "velocity": 1.0,
        "score": 100.0,
    }

    def summary(days):
        calls.append(days)
        return {
            "evidence_complete": True,
            "missing_order_evidence_rows": 0,
            "missing_product_evidence_rows": 0,
            "items": [item],
            "total_skus": 1,
            "avg_score": 100.0,
            "quadrants": {"star": 1, "cash_cow": 0, "question": 0, "dog": 0},
        }

    with replaced_modules(replacements(
        product_score=module("product_score", summary=summary),
        require_auth=lambda: {},
    )):
        runpy.run_path(str(PAGE), run_name="__product_score_complete_test__")
    assert calls == [7]
    assert sum(1 for kind, _value in EVENTS if kind == "metric") == 4
    assert any("SKU-7" in str(value) for kind, value in EVENTS if kind == "markdown")


def test_active_caption_names_only_the_four_weighted_dimensions() -> None:
    fake_streamlit = module("streamlit", session_state={"lang": "en"})
    with replaced_modules({"streamlit": fake_streamlit}):
        namespace = runpy.run_path(
            str(Path(__file__).parent / "i18n.py"),
            run_name="__product_score_i18n_test__",
        )
        caption = namespace["t"]("pscore.caption")
    assert caption == "Composite score from revenue, margin, sales velocity, and stock"
    assert "review" not in caption.lower()


if __name__ == "__main__":
    test_terminating_auth_prevents_database_and_score_calls()
    test_selected_window_drives_summary_and_incomplete_evidence_stops_kpis()
    test_complete_page_reuses_the_selected_window_summary_items()
    test_active_caption_names_only_the_four_weighted_dimensions()
    print("product score page contract: 4 passed")
