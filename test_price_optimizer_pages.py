"""Page-contract tests for target-price advice consumers."""

from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).parent
TRANSLATIONS: list[str] = []
METRICS: list[tuple[str, str]] = []
CALLS: list[tuple[str, dict]] = []
WARNINGS: list[str] = []
EVENTS: list[str] = []


class PageStopped(Exception):
    pass


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class Column(Context):
    def number_input(self, _label, **kwargs):
        return kwargs.get("value", 1.0)

    def selectbox(self, _label, options, **_kwargs):
        return list(options)[0]

    def checkbox(self, _label, **kwargs):
        return kwargs.get("value", False)

    def metric(self, label, value, **_kwargs):
        METRICS.append((str(label), str(value)))


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


def t(key, **_kwargs):
    TRANSLATIONS.append(key)
    return key


def quote(platform="shopee"):
    return {
        "error": None,
        "kind": "target_price_advice",
        "evidence": "configured_fee_assumption",
        "platform": platform,
        "platform_label": platform,
        "fee_rate_pct": 10.0,
        "raw": {
            "price": 200.0,
            "platform_fee": 20.0,
            "net": 80.0,
            "actual_margin_pct": 40.0,
        },
        "selected": {
            "price": 209,
            "platform_fee": 20.9,
            "net": 88.1,
            "actual_margin_pct": 42.2,
        },
    }


def fake_optimizer(*, target_error=None, compare_errors=None):
    def target_price(**kwargs):
        CALLS.append(("target_price", kwargs))
        if target_error:
            return {"error": target_error, "platform": kwargs["platform"]}
        return quote(kwargs["platform"])

    def compare_platforms(*args, **kwargs):
        CALLS.append(("compare_platforms", {"args": args, **kwargs}))
        if compare_errors:
            return [
                {
                    "error": error,
                    "platform": platform,
                    "platform_label": platform,
                    "max_margin": 10.0,
                }
                for platform, error in compare_errors
            ]
        return [quote("shopee"), quote("lazada")]

    def margin_at_price(*args, **kwargs):
        CALLS.append(("margin_at_price", {"args": args, **kwargs}))
        return {
            "error": None,
            "price": args[1],
            "platform_fee": 20.0,
            "net": 80.0,
            "actual_margin_pct": 40.0,
        }

    return module(
        "price_optimizer",
        CANONICAL_PLATFORMS=("shopee", "lazada"),
        target_price=target_price,
        compare_platforms=compare_platforms,
        margin_at_price=margin_at_price,
    )


def fake_streamlit(*, competitor_text=""):
    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.title = lambda value: TRANSLATIONS.append(str(value))
    st.caption = lambda value: TRANSLATIONS.append(str(value))
    st.subheader = lambda value: TRANSLATIONS.append(str(value))
    st.tabs = lambda labels: [Context() for _ in labels]
    st.columns = lambda spec: [Column() for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.number_input = Column().number_input
    st.text_area = lambda *_args, **_kwargs: competitor_text
    st.checkbox = Column().checkbox
    st.selectbox = Column().selectbox
    st.metric = Column().metric
    st.html = lambda *_args, **_kwargs: None
    st.markdown = lambda *_args, **_kwargs: None
    st.divider = lambda: None
    st.warning = lambda value, **_kwargs: WARNINGS.append(str(value))
    st.info = lambda *_args, **_kwargs: None
    st.stop = lambda: (_ for _ in ()).throw(PageStopped())
    st.dataframe = lambda *_args, **_kwargs: None
    st.column_config = types.SimpleNamespace(NumberColumn=lambda **_kwargs: object())
    return st


def common_replacements(*, competitor_text="", target_error=None,
                        compare_errors=None, auth_stops=False):
    fees = {
        "shopee": {
            "commission_pct": 10.0,
            "payment_pct": 0.0,
            "transaction_pct": 0.0,
            "vat_on_fees": 0.0,
        }
    }
    def require_auth():
        EVENTS.append("auth")
        if auth_stops:
            raise PageStopped()

    def init_db():
        EVENTS.append("db")

    return {
        "streamlit": fake_streamlit(competitor_text=competitor_text),
        "price_optimizer": fake_optimizer(
            target_error=target_error,
            compare_errors=compare_errors,
        ),
        "theme": module("theme", apply_theme=lambda: None),
        "auth": module("auth", require_auth=require_auth),
        "sidebar": module("sidebar", render_sidebar=lambda: None),
        "_theme": module("_theme", apply=lambda: None),
        "_auth_gate": module("_auth_gate", require_auth=require_auth),
        "_sidebar": module("_sidebar", render=lambda: None),
        "_components": module("_components", page_header=lambda **_kwargs: None),
        "i18n": module("i18n", t=t),
        "i18n_inline": module(
            "i18n_inline", marketplace_fee_label=lambda value: value
        ),
        "db": module("db", init=init_db),
        "onboarding": module("onboarding", tip=lambda *_args: None),
        "fees": module(
            "fees",
            load=lambda: fees,
            net_profit=lambda cost, sell, platform, _fees: {
                "net": sell - cost,
                "margin_pct": (sell - cost) / sell * 100,
            },
        ),
        "pandas": module("pandas", DataFrame=lambda rows: rows),
    }


def reset() -> None:
    TRANSLATIONS.clear()
    METRICS.clear()
    CALLS.clear()
    WARNINGS.clear()
    EVENTS.clear()


def test_f8_uses_selected_target_quote_and_truthful_advisory_labels() -> None:
    reset()
    with replaced_modules(common_replacements()):
        runpy.run_path(str(ROOT / "pages" / "F8_💡_PriceOpt.py"), run_name="__f8_test__")

    assert "popt.advisory_title" in TRANSLATIONS
    assert "popt.advisory_caption" in TRANSLATIONS
    assert "popt.target_price" in TRANSLATIONS
    assert "popt.safe_psych_price" in TRANSLATIONS
    assert "popt.title" not in TRANSLATIONS
    assert any(name == "target_price" for name, _kwargs in CALLS)
    assert any(name == "compare_platforms" for name, _kwargs in CALLS)
    assert ("popt.target_price", "฿209") in METRICS
    assert ("popt.estimated_platform_fees", "฿21") in METRICS
    assert ("popt.net_after_listed_costs", "฿88") in METRICS


def test_canonical_pricing_page_uses_same_selected_contract_and_advisory_copy() -> None:
    reset()
    with replaced_modules(common_replacements(competitor_text="shop 200")):
        runpy.run_path(str(ROOT / "pages" / "7_💰_Pricing.py"), run_name="__pricing_test__")

    assert "pricing.target_adviser_title" in TRANSLATIONS
    assert "pricing.target_adviser_help" in TRANSLATIONS
    assert "pricing.optimizer_title" not in TRANSLATIONS
    compare_calls = [kwargs for name, kwargs in CALLS if name == "compare_platforms"]
    assert compare_calls and compare_calls[-1]["psychological"] is True
    assert any(name == "margin_at_price" for name, _kwargs in CALLS)


def test_empty_competitor_state_keeps_target_adviser_accessible() -> None:
    reset()
    with replaced_modules(common_replacements(competitor_text="")):
        runpy.run_path(str(ROOT / "pages" / "7_💰_Pricing.py"), run_name="__pricing_empty_test__")

    assert any(name == "compare_platforms" for name, _kwargs in CALLS)
    assert "pricing.target_adviser_title" in TRANSLATIONS


def test_auth_gate_stops_before_database_initialization() -> None:
    reset()
    with replaced_modules(common_replacements(auth_stops=True)):
        try:
            runpy.run_path(str(ROOT / "pages" / "7_💰_Pricing.py"), run_name="__pricing_auth_test__")
        except PageStopped:
            pass
        else:
            raise AssertionError("the real authentication stop must terminate the page")

    assert EVENTS == ["auth"]


def test_f8_calculator_error_does_not_hide_platform_comparison() -> None:
    reset()
    with replaced_modules(common_replacements(target_error="invalid_fee_config")):
        runpy.run_path(str(ROOT / "pages" / "F8_💡_PriceOpt.py"), run_name="__f8_error_test__")

    assert "popt.advisory_unavailable" in WARNINGS
    assert any(name == "compare_platforms" for name, _kwargs in CALLS)


def test_pricing_page_labels_margin_and_other_errors_truthfully() -> None:
    reset()
    errors = (
        ("shopee", "margin_too_high"),
        ("lazada", "invalid_fee_config"),
    )
    with replaced_modules(common_replacements(
        competitor_text="shop 200", compare_errors=errors,
    )):
        runpy.run_path(str(ROOT / "pages" / "7_💰_Pricing.py"), run_name="__pricing_errors_test__")

    assert "pricing.margin_too_high" in TRANSLATIONS
    assert "pricing.advisory_unavailable" in TRANSLATIONS


if __name__ == "__main__":
    test_f8_uses_selected_target_quote_and_truthful_advisory_labels()
    test_canonical_pricing_page_uses_same_selected_contract_and_advisory_copy()
    test_empty_competitor_state_keeps_target_adviser_accessible()
    test_auth_gate_stops_before_database_initialization()
    test_f8_calculator_error_does_not_hide_platform_comparison()
    test_pricing_page_labels_margin_and_other_errors_truthfully()
    print("price optimizer pages: 6 passed")
