"""Regression coverage for dead-stock page output and evidence gating."""
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
def replaced_modules(replacements: dict[str, types.ModuleType]):
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


def fake_streamlit(warnings: list[str], successes: list[str]):
    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.title = lambda *_args, **_kwargs: None
    st.caption = lambda *_args, **_kwargs: None
    st.segmented_control = lambda *_args, **_kwargs: 60
    st.selectbox = lambda *_args, **_kwargs: 60
    st.columns = lambda count: [Context() for _ in range(count)]
    st.warning = lambda value: warnings.append(value)
    st.success = lambda value: successes.append(value)
    st.divider = lambda: None
    st.markdown = lambda *_args, **_kwargs: None
    st.html = lambda *_args, **_kwargs: None
    st.expander = lambda *_args, **_kwargs: Context()
    st.stop = lambda: (_ for _ in ()).throw(StopExecution())
    return st


def test_h4_page_uses_current_summary_and_item_field_names() -> None:
    METRICS.clear()
    warnings: list[str] = []
    successes: list[str] = []
    complete_summary = {
        "evidence_complete": True,
        "dead": 2,
        "slow": 1,
        "dead_trapped": 120.0,
        "items": [],
    }
    replacements = {
        "streamlit": fake_streamlit(warnings, successes),
        "dead_stock": module(
            "dead_stock",
            summary=lambda days: complete_summary,
            detect=lambda days: [],
            suggest_actions=lambda items: [],
        ),
        "theme": module("theme", apply_theme=lambda: None),
        "auth": module("auth", require_auth=lambda: None),
        "sidebar": module("sidebar", render_sidebar=lambda: None),
        "i18n": module("i18n", t=lambda key, **_kwargs: key),
    }

    with replaced_modules(replacements):
        runpy.run_path(
            str(Path(__file__).parent / "pages" / "H4_☠_DeadStock.py"),
            run_name="__dead_stock_h4_contract_test__",
        )

    assert [metric[1] for metric in METRICS] == [2, 1, "฿120"]


def test_dead_stock_pages_stop_before_false_zero_or_all_clear_when_incomplete() -> None:
    incomplete_summary = {
        "evidence_complete": False,
        "missing_order_evidence_rows": 2,
        "missing_product_evidence_rows": 1,
        "items": [],
        "total_items": None,
        "dead": None,
        "stale": None,
        "slow": None,
        "trapped_cash": None,
        "dead_trapped": None,
        "stale_trapped": None,
        "slow_trapped": None,
    }

    for page_name in ["H4_☠_DeadStock.py", "m_💀_DeadStock.py"]:
        METRICS.clear()
        warnings: list[str] = []
        successes: list[str] = []
        replacements = {
            "streamlit": fake_streamlit(warnings, successes),
            "dead_stock": module(
                "dead_stock",
                summary=lambda days: incomplete_summary,
                detect=lambda days: [],
                suggest_actions=lambda _items=None: [],
            ),
            "db": module("db", init=lambda: None),
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
            "i18n": module("i18n", t=lambda key, **_kwargs: key),
        }

        stopped = False
        with replaced_modules(replacements):
            try:
                runpy.run_path(
                    str(Path(__file__).parent / "pages" / page_name),
                    run_name="__dead_stock_incomplete_page_test__",
                )
            except StopExecution:
                stopped = True

        assert stopped, page_name
        assert warnings, page_name
        assert not METRICS, page_name
        assert not successes, page_name


if __name__ == "__main__":
    test_h4_page_uses_current_summary_and_item_field_names()
    test_dead_stock_pages_stop_before_false_zero_or_all_clear_when_incomplete()
    print("dead stock page contract: 2 passed")
