"""Regression coverage for profit-calendar page evidence and field contracts."""
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

    def subheader(self, *_args, **_kwargs):
        return None

    def metric(self, *args, **_kwargs):
        CLAIMS.append(str(args))


CLAIMS: list[str] = []


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


def fake_streamlit(warnings: list[str]):
    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.title = lambda *_args, **_kwargs: None
    st.caption = lambda *_args, **_kwargs: None
    st.tabs = lambda labels: [Context() for _ in labels]
    st.segmented_control = lambda *_args, **_kwargs: 30
    st.columns = lambda count: [Context() for _ in range(count)]
    st.warning = lambda value: warnings.append(str(value))
    st.info = lambda *_args, **_kwargs: None
    st.subheader = lambda *_args, **_kwargs: None
    st.divider = lambda: None
    st.html = lambda value: CLAIMS.append(str(value))
    st.markdown = lambda value, **_kwargs: CLAIMS.append(str(value))
    st.stop = lambda: (_ for _ in ()).throw(StopExecution())
    return st


def base_replacements(st, pc):
    return {
        "streamlit": st,
        "profit_calendar": pc,
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
        "i18n": module("i18n", t=lambda key, **_kwargs: key),
    }


def test_pages_stop_before_profit_claims_when_evidence_is_incomplete():
    incomplete = {
        "evidence_complete": False,
        "missing_order_evidence_rows": 1,
        "missing_product_evidence_rows": 1,
        "days": [],
    }
    pc = module(
        "profit_calendar",
        daily_summary=lambda days: incomplete,
        daily_profits=lambda days: [],
        weekly_summary=lambda days: [],
        monthly_summary=lambda months: [],
        best_worst_days=lambda days, top: {"best": [], "worst": []},
    )

    for page_name in ["H2_🗓_ProfitCalendar.py", "r_📆_ProfitCal.py"]:
        CLAIMS.clear()
        warnings: list[str] = []
        stopped = False
        with replaced_modules(base_replacements(fake_streamlit(warnings), pc)):
            try:
                runpy.run_path(
                    str(Path(__file__).parent / "pages" / page_name),
                    run_name="__profit_calendar_incomplete_page_test__",
                )
            except StopExecution:
                stopped = True

        assert stopped, page_name
        assert warnings, page_name
        assert not CLAIMS, page_name


def test_h2_page_renders_the_canonical_profit_field():
    CLAIMS.clear()
    warnings: list[str] = []
    day = {
        "date": "2026-09-28",
        "weekday": "Mon",
        "weekday_num": 0,
        "revenue": 50.0,
        "cogs": 20.0,
        "profit": 30.0,
        "orders": 1,
        "has_data": True,
    }
    complete = {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "days": [day],
    }
    pc = module(
        "profit_calendar",
        daily_summary=lambda days: complete,
        daily_profits=lambda days: [day],
        weekly_summary=lambda days: [{
            "start": day["date"], "end": day["date"], "week": day["date"],
            "revenue": 50.0, "cogs": 20.0, "profit": 30.0,
            "orders": 1, "days_with_sales": 1,
        }],
        monthly_summary=lambda months: [{
            "month": "2026-09", "revenue": 50.0, "cogs": 20.0,
            "profit": 30.0, "days_with_sales": 1,
        }],
        best_worst_days=lambda days, top: {"best": [day], "worst": [day]},
    )

    with replaced_modules(base_replacements(fake_streamlit(warnings), pc)):
        runpy.run_path(
            str(Path(__file__).parent / "pages" / "H2_🗓_ProfitCalendar.py"),
            run_name="__profit_calendar_complete_page_test__",
        )

    assert not warnings
    rendered = "\n".join(CLAIMS)
    assert "฿30" in rendered
    assert "฿0" not in rendered
    assert "2026-09-28 – 2026-09-28" in rendered


if __name__ == "__main__":
    test_pages_stop_before_profit_claims_when_evidence_is_incomplete()
    test_h2_page_renders_the_canonical_profit_field()
    print("profit calendar page contract: 2 passed")
