"""Regression coverage for the Stock Turnover page output contract."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


class StopExecution(Exception):
    pass


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def metric(self, *args, **_kwargs):
        METRICS.append(args)


METRICS: list[tuple] = []


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


def fake_streamlit(rendered, warnings, successes):
    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.title = lambda *_args, **_kwargs: None
    st.caption = lambda *_args, **_kwargs: None
    st.columns = lambda count: [Context() for _ in range(count)]
    st.divider = lambda: None
    st.tabs = lambda labels: [Context() for _ in labels]
    st.info = lambda *_args, **_kwargs: None
    st.write = lambda *_args, **_kwargs: None
    st.html = lambda value, **_kwargs: rendered.append(str(value))
    st.markdown = lambda value, **_kwargs: rendered.append(str(value))
    st.warning = lambda value, **_kwargs: warnings.append(str(value))
    st.success = lambda value, **_kwargs: successes.append(str(value))
    st.stop = lambda: (_ for _ in ()).throw(StopExecution())
    return st


def base_replacements(st, stock_turnover):
    return {
        "streamlit": st,
        "db": module("db", init=lambda: None),
        "stock_turnover": stock_turnover,
        "theme": module("theme", apply_theme=lambda: None),
        "auth": module("auth", require_auth=lambda: None),
        "sidebar": module("sidebar", render_sidebar=lambda: None),
        "_theme": module("_theme", apply=lambda: None),
        "_auth_gate": module("_auth_gate", require_auth=lambda: None),
        "_sidebar": module("_sidebar", render=lambda: None),
        "_components": module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *args, **_kwargs: METRICS.append(args),
        ),
        "i18n": module(
            "i18n",
            t=lambda key, **kwargs: key + (
                ":" + ",".join(f"{name}={value}" for name, value in kwargs.items())
                if kwargs else ""
            ),
        ),
    }


def test_page_stops_before_false_zero_or_all_clear_when_evidence_is_incomplete() -> None:
    incomplete = {
        "evidence_complete": False,
        "missing_order_evidence_rows": 2,
        "missing_product_evidence_rows": 1,
        "items": [],
        "avg_turnover": None,
        "health": None,
    }
    stock_turnover = module(
        "stock_turnover",
        summary=lambda: incomplete,
        calculate=lambda: [],
        reorder_list=lambda: [],
    )

    for page_name in ["H5_🔄_StockTurnover.py", "q_🔄_Turnover.py"]:
        METRICS.clear()
        rendered: list[str] = []
        warnings: list[str] = []
        successes: list[str] = []
        stopped = False
        with replaced_modules(base_replacements(
            fake_streamlit(rendered, warnings, successes), stock_turnover
        )):
            try:
                runpy.run_path(
                    str(Path(__file__).parent / "pages" / page_name),
                    run_name="__stock_turnover_incomplete_page_test__",
                )
            except StopExecution:
                stopped = True

        assert stopped, page_name
        assert warnings, page_name
        assert "2" in warnings[0] and "1" in warnings[0], page_name
        assert METRICS == [], page_name
        assert successes == [], page_name
        assert rendered == [], page_name


def test_page_uses_current_summary_and_item_field_names() -> None:
    METRICS.clear()
    rendered: list[str] = []
    warnings: list[str] = []
    successes: list[str] = []
    complete = {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "avg_turnover": 2.5,
        "health": {"fast": 1, "good": 0, "slow": 1, "stuck": 0},
    }
    item = {
        "sku": "SKU-1",
        "name": "Product",
        "stock": 7,
        "turnover_rate": 2.5,
        "doi": 12,
        "reorder_point": 4,
        "needs_reorder": True,
    }
    stock_turnover = module(
        "stock_turnover",
        summary=lambda: complete,
        calculate=lambda: [item],
        reorder_list=lambda: [item],
    )

    with replaced_modules(base_replacements(
        fake_streamlit(rendered, warnings, successes), stock_turnover
    )):
        runpy.run_path(
            str(Path(__file__).parent / "pages" / "H5_🔄_StockTurnover.py"),
            run_name="__stock_turnover_complete_page_test__",
        )

    assert [metric[1] for metric in METRICS] == ["2.5x", 1, 1]
    combined = "\n".join(rendered)
    assert "2.5x" in combined
    assert "SKU-1" in combined
    assert "7" in combined
    assert "12" in combined
    assert "4" in combined
    assert warnings == []


if __name__ == "__main__":
    test_page_stops_before_false_zero_or_all_clear_when_evidence_is_incomplete()
    test_page_uses_current_summary_and_item_field_names()
    print("stock turnover page contract: 2 passed")
