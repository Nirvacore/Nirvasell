"""Behavior tests for the active Label Generator page."""
from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


PAGE = Path(__file__).parent / "pages" / "D4_🏷_Labels.py"
EVENTS: list[tuple[str, object]] = []


class AuthStop(Exception):
    pass


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def text_input(self, *_args, **_kwargs):
        return ""

    def selectbox(self, _label, options, **_kwargs):
        return options[0]

    def number_input(self, *_args, **_kwargs):
        return 0.0


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


def fake_streamlit(*, pressed: str | None = None, bulk_text: str = ""):
    st = module("streamlit", session_state={})
    st.title = lambda *_args, **_kwargs: None
    st.caption = lambda *_args, **_kwargs: None
    st.subheader = lambda *_args, **_kwargs: None
    st.tabs = lambda labels: [Context() for _ in labels]
    st.form = lambda *_args, **_kwargs: Context()
    st.columns = lambda count: [Context() for _ in range(count)]
    st.selectbox = lambda _label, options, **_kwargs: options[0]
    st.form_submit_button = lambda *_args, **_kwargs: False
    st.number_input = lambda *_args, **_kwargs: 0.0
    st.text_input = lambda label, **_kwargs: {
        "cod.f_platform": "shopee",
        "lbl.order_id_input": "ORDER-1",
    }.get(label, "")
    st.text_area = lambda label, **_kwargs: (
        bulk_text if label == "lbl.bulk_orders" else ""
    )
    st.button = lambda label, **_kwargs: label == pressed
    st.code = lambda value, **_kwargs: EVENTS.append(("code", value))
    st.error = lambda value: EVENTS.append(("error", value))
    st.success = lambda value: EVENTS.append(("success", value))
    return st


def replacements(*, st, label_generator, require_auth):
    return {
        "streamlit": st,
        "label_generator": label_generator,
        "shop_settings": module(
            "shop_settings", init=lambda: EVENTS.append(("call", "ss.init"))
        ),
        "theme": module("theme", apply_theme=lambda: None),
        "auth": module("auth", require_auth=require_auth),
        "sidebar": module("sidebar", render_sidebar=lambda: None),
        "i18n": module("i18n", t=lambda key, **fmt: key.format(**fmt)),
        "i18n_inline": module(
            "i18n_inline",
            carrier_name=lambda value: value,
            label_style_label=lambda value: value,
        ),
    }


def test_terminating_auth_prevents_database_and_label_calls() -> None:
    EVENTS.clear()
    lg = module(
        "label_generator",
        LABEL_STYLES=("full",),
        from_order=lambda *_args, **_kwargs: EVENTS.append(("call", "from_order")),
    )
    with replaced_modules(replacements(
        st=fake_streamlit(),
        label_generator=lg,
        require_auth=lambda: (_ for _ in ()).throw(AuthStop()),
    )):
        try:
            runpy.run_path(str(PAGE), run_name="__label_auth_test__")
        except AuthStop:
            pass
        else:
            raise AssertionError("authentication stop must terminate the page")
    assert EVENTS == []


def test_saved_order_requires_platform_and_renders_structured_failure() -> None:
    EVENTS.clear()
    calls: list[tuple[str, str, str]] = []

    def from_order(platform, order_id, *, style):
        calls.append((platform, order_id, style))
        return {"ok": False, "code": "conflicting_evidence", "message": "conflict"}

    lg = module(
        "label_generator",
        LABEL_STYLES=("full",),
        from_order=from_order,
        generate_label=lambda **_kwargs: "manual",
        generate_bulk_labels=lambda *_args, **_kwargs: {"labels": [], "errors": []},
    )
    with replaced_modules(replacements(
        st=fake_streamlit(pressed="lbl.fetch_btn"),
        label_generator=lg,
        require_auth=lambda: {},
    )):
        runpy.run_path(str(PAGE), run_name="__label_lookup_failure_test__")
    assert calls == [("shopee", "ORDER-1", "full")]
    assert ("error", "conflict") in EVENTS
    assert not any(kind == "code" for kind, _value in EVENTS)


def test_bulk_page_renders_every_row_error_without_hiding_valid_labels() -> None:
    EVENTS.clear()
    csv_text = 'FIRST,Alice,081,"Road, Bangkok",100,0\nBAD,Bob'
    calls: list[tuple[str, str]] = []

    def generate_bulk_labels(raw, *, style):
        calls.append((raw, style))
        return {
            "labels": ["FIRST LABEL"],
            "errors": [
                {"row": 2, "code": "invalid_columns", "message": "row 2"},
                {"row": 3, "code": "invalid_numeric", "message": "row 3"},
            ],
        }

    lg = module(
        "label_generator",
        LABEL_STYLES=("full",),
        from_order=lambda *_args, **_kwargs: {},
        generate_label=lambda **_kwargs: "manual",
        generate_bulk_labels=generate_bulk_labels,
    )
    with replaced_modules(replacements(
        st=fake_streamlit(pressed="lbl.bulk_btn", bulk_text=csv_text),
        label_generator=lg,
        require_auth=lambda: {},
    )):
        runpy.run_path(str(PAGE), run_name="__label_bulk_error_test__")
    assert calls == [(csv_text, "full")]
    assert ("code", "FIRST LABEL") in EVENTS
    assert [value for kind, value in EVENTS if kind == "error"] == ["row 2", "row 3"]
    assert any(kind == "success" for kind, _value in EVENTS)


if __name__ == "__main__":
    test_terminating_auth_prevents_database_and_label_calls()
    test_saved_order_requires_platform_and_renders_structured_failure()
    test_bulk_page_renders_every_row_error_without_hiding_valid_labels()
    print("label generator page contract: 3 passed")
