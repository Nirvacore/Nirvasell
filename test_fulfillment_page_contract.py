"""Contract tests for the canonical Fulfillment page."""

from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path

PAGE = Path(__file__).parent / "pages" / "K_📦_Fulfillment.py"


class AuthStop(Exception):
    pass


class Rerun(Exception):
    pass


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: None


class FakeRow(dict):
    def __getattr__(self, name):
        return self[name]


class FakeFrame:
    def __init__(self, rows):
        self.rows = [FakeRow(row) for row in rows]

    def assign(self, **values):
        for row in self.rows:
            row.update(values)
        return self

    def iterrows(self):
        return enumerate(self.rows)


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


def fake_streamlit(*, submit=False):
    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.columns = lambda spec: [Context() for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.tabs = lambda labels: [Context() for _ in labels]
    st.form = lambda *_args, **_kwargs: Context()
    st.expander = lambda *_args, **_kwargs: Context()
    st.selectbox = lambda _label, options, **_kwargs: options[0]
    st.caption = lambda *_args, **_kwargs: None
    st.markdown = lambda *_args, **_kwargs: None
    st.divider = lambda: None
    st.metric = lambda *_args, **_kwargs: None
    st.warning = lambda value: EVENTS.append(("warning", str(value)))
    st.error = lambda value: EVENTS.append(("error", str(value)))
    st.success = lambda value: EVENTS.append(("success", str(value)))
    st.form_submit_button = lambda *_args, **_kwargs: submit
    st.data_editor = lambda frame, **_kwargs: frame.assign(
        **{"✓": True, "tracking_number": "TH-123"}
    )
    st.rerun = lambda: (_ for _ in ()).throw(Rerun())
    st.column_config = types.SimpleNamespace(
        CheckboxColumn=lambda *_args, **_kwargs: None,
        TextColumn=lambda *_args, **_kwargs: None,
        NumberColumn=lambda *_args, **_kwargs: None,
    )
    st.dataframe = lambda *_args, **_kwargs: None
    st.download_button = lambda *_args, **_kwargs: None
    st.slider = lambda _label, _min, _max, value, **_kwargs: value
    st.text_input = lambda *_args, value="", **_kwargs: value
    st.text_area = lambda *_args, value="", **_kwargs: value
    st.components = types.SimpleNamespace(v1=types.SimpleNamespace(html=lambda *_args, **_kwargs: None))
    return st


EVENTS: list[tuple[str, str]] = []


def common_replacements(*, st, ff, require_auth):
    return {
        "streamlit": st,
        "pandas": module(
            "pandas",
            DataFrame=FakeFrame,
            Timestamp=types.SimpleNamespace(now=lambda: types.SimpleNamespace(strftime=lambda _fmt: "20260928")),
        ),
        "db": module("db", init=lambda: EVENTS.append(("call", "db.init"))),
        "fulfillment": ff,
        "user_settings": module(
            "user_settings",
            init=lambda: EVENTS.append(("call", "us.init")),
            get=lambda _key, default="": default,
            set=lambda *_args, **_kwargs: None,
        ),
        "_theme": module("_theme", apply=lambda: None),
        "_sidebar": module("_sidebar", render=lambda: None),
        "_auth_gate": module("_auth_gate", require_auth=require_auth),
        "_components": module(
            "_components",
            page_header=lambda **_kwargs: None,
            empty_state=lambda **_kwargs: None,
            toast=lambda *_args, **_kwargs: None,
        ),
        "i18n": module("i18n", t=lambda key, **fmt: key + (f":{fmt['n']}" if "n" in fmt else "")),
        "i18n_inline": module("i18n_inline", platform_name=lambda value: value),
    }


def test_terminating_auth_prevents_database_and_feature_initialization() -> None:
    EVENTS.clear()
    ff = module("fulfillment", init=lambda: EVENTS.append(("call", "ff.init")))
    replacements = common_replacements(
        st=fake_streamlit(),
        ff=ff,
        require_auth=lambda: (_ for _ in ()).throw(AuthStop()),
    )
    with replaced_modules(replacements):
        try:
            runpy.run_path(str(PAGE), run_name="__fulfillment_auth_test__")
        except AuthStop:
            pass
        else:
            raise AssertionError("authentication stop must terminate the page")
    assert EVENTS == []


def test_zero_actual_bulk_transitions_render_failure_without_success_or_rerun() -> None:
    EVENTS.clear()
    pending = [{
        "id": 7, "platform": "shopee", "order_id": "ORDER-7",
        "sku": "SKU-7", "qty": 1, "product_name": "Product",
    }]
    ff = module(
        "fulfillment",
        init=lambda: None,
        stats=lambda: {"pending": 1, "shipped": 0, "pending_by_platform": {"shopee": 1}},
        pending_orders=lambda: pending,
        platforms_with_pending=lambda: ["shopee"],
        carrier_options=lambda: [("kerry", "Kerry")],
        mark_shipped_bulk=lambda _items: 0,
        shipped_orders=lambda limit=200: [],
    )
    replacements = common_replacements(
        st=fake_streamlit(submit=True), ff=ff, require_auth=lambda: {},
    )
    reran = False
    with replaced_modules(replacements):
        try:
            runpy.run_path(str(PAGE), run_name="__fulfillment_failure_test__")
        except Rerun:
            reran = True
    assert reran is False
    assert ("error", "fulfill.shipped_n:0") in EVENTS
    assert not any(kind == "success" for kind, _value in EVENTS)


if __name__ == "__main__":
    test_terminating_auth_prevents_database_and_feature_initialization()
    test_zero_actual_bulk_transitions_render_failure_without_success_or_rerun()
    print("fulfillment page contract: 2 passed")
