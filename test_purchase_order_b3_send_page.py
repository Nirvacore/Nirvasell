"""Regression coverage for the truthful B3 draft-to-sent action."""

from __future__ import annotations

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path


class Rerun(Exception):
    pass


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class EmptyConnection(Context):
    def execute(self, *_args, **_kwargs):
        return EmptyRows()


class EmptyRows:
    def fetchall(self):
        return []


BUTTONS: list[tuple[str, str]] = []
ERRORS: list[str] = []
TOASTS: list[str] = []


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


def fake_streamlit(click_send: bool):
    st = module("streamlit")
    st.set_page_config = lambda **_kwargs: None
    st.columns = lambda spec: [Context() for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.divider = lambda: None
    st.expander = lambda *_args, **_kwargs: Context()
    st.info = lambda *_args, **_kwargs: None
    st.markdown = lambda *_args, **_kwargs: None
    st.warning = lambda *_args, **_kwargs: None
    st.error = lambda value: ERRORS.append(str(value))
    st.stop = lambda: None

    def button(label, *, key=None, **_kwargs):
        BUTTONS.append((str(label), str(key)))
        return click_send and str(key).startswith("b3send_")

    st.button = button
    st.rerun = lambda: (_ for _ in ()).throw(Rerun())
    return st


def order(status: str) -> dict:
    return {
        "id": 7,
        "po_number": "PO-7",
        "supplier": "Supplier",
        "order_date": "2026-09-28",
        "expected_date": "",
        "item_count": 1,
        "total_amount": 100.0,
        "status": status,
        "status_info": {"icon": "📋", "color": "#999"},
    }


def run_page(*, status="draft", outcome=True, click_send=True):
    BUTTONS.clear()
    ERRORS.clear()
    TOASTS.clear()
    calls: list[int] = []

    def send(po_id):
        calls.append(po_id)
        return outcome

    po = module(
        "purchase_orders",
        init=lambda: None,
        summary=lambda: {
            "total": 1, "pending_count": 0, "pending_value": 100.0,
            "overdue": 0,
        },
        all_pos=lambda: [order(status)],
        get=lambda _po_id: {"items": []},
        send=send,
    )
    replacements = {
        "streamlit": fake_streamlit(click_send),
        "db": module("db", init=lambda: None, conn=lambda: EmptyConnection()),
        "purchase_orders": po,
        "_theme": module("_theme", apply=lambda: None),
        "_sidebar": module("_sidebar", render=lambda: None),
        "_auth_gate": module("_auth_gate", require_auth=lambda: None),
        "_components": module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *_args, **_kwargs: None,
            toast=lambda value, **_kwargs: TOASTS.append(str(value)),
        ),
        "i18n": module("i18n", t=lambda key, **_kwargs: key),
        "i18n_inline": module("i18n_inline", po_status=lambda value: value),
    }

    reran = False
    with replaced_modules(replacements):
        try:
            runpy.run_path(
                str(Path(__file__).parent / "pages" / "B3_🛒_PurchaseOrders.py"),
                run_name="__purchase_order_b3_test__",
            )
        except Rerun:
            reran = True
    return calls, reran


def test_draft_action_is_truthful_and_reruns_only_after_success() -> None:
    calls, reran = run_page(outcome=True)
    assert calls == [7]
    assert reran is True
    assert TOASTS == ["po.mark_sent_success"]
    assert ERRORS == []
    assert ("po.mark_sent_btn", "b3send_7") in BUTTONS
    assert all(label != "po.send_btn" for label, _key in BUTTONS)


def test_stale_or_missing_draft_shows_error_without_success_or_rerun() -> None:
    calls, reran = run_page(outcome=False)
    assert calls == [7]
    assert reran is False
    assert TOASTS == []
    assert ERRORS == ["po.mark_sent_stale"]


def test_non_draft_rows_have_no_mark_sent_action() -> None:
    for status in ("sent", "cancelled", "partial", "received"):
        calls, reran = run_page(status=status, click_send=True)
        assert calls == [], status
        assert reran is False, status
        assert not any(key.startswith("b3send_") for _label, key in BUTTONS), status


if __name__ == "__main__":
    test_draft_action_is_truthful_and_reruns_only_after_success()
    test_stale_or_missing_draft_shows_error_without_success_or_rerun()
    test_non_draft_rows_have_no_mark_sent_action()
    print("purchase order B3 send page: 3 passed")
