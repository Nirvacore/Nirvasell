"""Regression coverage for H0 cash-flow field and evidence contracts."""

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
        CLAIMS.append(str(args))


CLAIMS: list[str] = []


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


def fake_streamlit(warnings):
    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.title = lambda *_args, **_kwargs: None
    st.caption = lambda *_args, **_kwargs: None
    st.columns = lambda count: [Context() for _ in range(count)]
    st.divider = lambda: None
    st.tabs = lambda labels: [Context() for _ in labels]
    st.segmented_control = lambda *_args, **_kwargs: 7
    st.slider = lambda *_args, **_kwargs: 2
    st.info = lambda *_args, **_kwargs: None
    st.warning = lambda value: warnings.append(str(value))
    st.html = lambda value: CLAIMS.append(str(value))
    st.stop = lambda: (_ for _ in ()).throw(StopExecution())
    return st


def replacements(st, cash_flow):
    return {
        "streamlit": st,
        "cash_flow": cash_flow,
        "pandas": module("pandas", DataFrame=type("DataFrame", (), {})),
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
            metric_with_hint=lambda *args, **_kwargs: CLAIMS.append(str(args)),
        ),
        "i18n": module("i18n", t=lambda key: key),
    }


def test_h0_stops_before_cash_claims_when_current_evidence_is_incomplete():
    CLAIMS.clear()
    warnings: list[str] = []
    incomplete = {
        "evidence_complete": False,
        "missing_order_evidence_rows": 1,
        "missing_expense_evidence_rows": 0,
        "months": [],
    }
    cf = module(
        "cash_flow",
        monthly_summary=lambda months: incomplete,
        daily_summary=lambda days: {**incomplete, "days": []},
        current_month_forecast=lambda: (_ for _ in ()).throw(
            AssertionError("forecast must not run from incomplete evidence")
        ),
    )

    stopped = False
    with replaced_modules(replacements(fake_streamlit(warnings), cf)):
        try:
            runpy.run_path(
                str(Path(__file__).parent / "pages" / "H0_💵_CashFlow.py"),
                run_name="__cash_flow_incomplete_page_test__",
            )
        except StopExecution:
            stopped = True

    assert stopped
    assert warnings
    assert not CLAIMS


def test_h0_stops_before_cash_claims_when_forecast_evidence_is_incomplete():
    CLAIMS.clear()
    warnings: list[str] = []
    complete = {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_expense_evidence_rows": 0,
        "months": [],
    }
    cf = module(
        "cash_flow",
        monthly_summary=lambda months: complete,
        daily_summary=lambda days: {**complete, "days": []},
        current_month_forecast=lambda: {
            "evidence_complete": False,
            "projected_net": None,
        },
    )

    stopped = False
    with replaced_modules(replacements(fake_streamlit(warnings), cf)):
        try:
            runpy.run_path(
                str(Path(__file__).parent / "pages" / "H0_💵_CashFlow.py"),
                run_name="__cash_flow_incomplete_forecast_page_test__",
            )
        except StopExecution:
            stopped = True

    assert stopped
    assert warnings
    assert not CLAIMS


def test_c8_stops_before_cash_claims_when_forecast_evidence_is_incomplete():
    CLAIMS.clear()
    warnings: list[str] = []
    cf = module(
        "cash_flow",
        current_month_forecast=lambda: {
            "evidence_complete": False,
            "projected_net": None,
        },
    )

    stopped = False
    with replaced_modules(replacements(fake_streamlit(warnings), cf)):
        try:
            runpy.run_path(
                str(Path(__file__).parent / "pages" / "C8_💵_CashFlow.py"),
                run_name="__cash_flow_c8_incomplete_page_test__",
            )
        except StopExecution:
            stopped = True

    assert stopped
    assert warnings
    assert not CLAIMS


def test_h0_renders_canonical_income_expenses_net_and_day_fields():
    CLAIMS.clear()
    warnings: list[str] = []
    month = {
        "month": "2026-09", "income": 125.0, "expenses": 25.0,
        "net": 100.0, "margin_pct": 80.0,
    }
    day = {
        "day": "2026-09-28", "income": 125.0, "expenses": 25.0,
        "net": 100.0, "cumulative": 100.0,
    }
    complete_months = {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_expense_evidence_rows": 0,
        "months": [month],
    }
    complete_days = {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_expense_evidence_rows": 0,
        "days": [day],
    }
    cf = module(
        "cash_flow",
        monthly_summary=lambda months: complete_months,
        daily_summary=lambda days: complete_days,
        current_month_forecast=lambda: {
            "evidence_complete": True, "projected_net": 110.0,
        },
    )

    with replaced_modules(replacements(fake_streamlit(warnings), cf)):
        runpy.run_path(
            str(Path(__file__).parent / "pages" / "H0_💵_CashFlow.py"),
            run_name="__cash_flow_complete_page_test__",
        )

    assert not warnings
    rendered = "\n".join(CLAIMS)
    assert "125" in rendered
    assert "25" in rendered
    assert "100" in rendered
    assert "2026-09-28" in rendered


if __name__ == "__main__":
    test_h0_stops_before_cash_claims_when_current_evidence_is_incomplete()
    test_h0_stops_before_cash_claims_when_forecast_evidence_is_incomplete()
    test_c8_stops_before_cash_claims_when_forecast_evidence_is_incomplete()
    test_h0_renders_canonical_income_expenses_net_and_day_fields()
    print("cash flow page contract: 4 passed")
