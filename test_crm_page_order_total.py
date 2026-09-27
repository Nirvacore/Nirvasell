"""Regression coverage for the CRM page's canonical order total."""
from __future__ import annotations

import runpy
import shutil
import sys
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

import db


class _Container:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _SelectionReached(Exception):
    pass


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@contextmanager
def isolated_page(selected_options: list[tuple[list[str], object]]):
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_crm_total_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path

    fake_streamlit = _module("streamlit")
    fake_streamlit.set_page_config = lambda **_kwargs: None
    fake_streamlit.columns = lambda spec: [
        _Container() for _ in range(spec if isinstance(spec, int) else len(spec))
    ]
    fake_streamlit.divider = lambda: None
    fake_streamlit.markdown = lambda *_args, **_kwargs: None
    fake_streamlit.stop = lambda: (_ for _ in ()).throw(AssertionError("unexpected stop"))

    def selectbox(_label, options, format_func=None, **_kwargs):
        selected_options.append((list(options), format_func))
        raise _SelectionReached

    fake_streamlit.selectbox = selectbox

    replacements = {
        "streamlit": fake_streamlit,
        "_theme": _module("_theme", apply=lambda: None),
        "_sidebar": _module("_sidebar", render=lambda: None),
        "_auth_gate": _module("_auth_gate", require_auth=lambda: None),
        "_components": _module(
            "_components",
            page_header=lambda **_kwargs: None,
            metric_with_hint=lambda *_args, **_kwargs: None,
            toast=lambda *_args, **_kwargs: None,
        ),
        "i18n": _module(
            "i18n",
            t=lambda key, **kwargs: (
                f"{kwargs['name']}|{kwargs['orders']}|{kwargs['total']}"
                if key == "crm.cust_option"
                else key
            ),
        ),
        "i18n_inline": _module(
            "i18n_inline",
            crm_note_type_label=lambda value: value,
            crm_tag_label=lambda value: value,
        ),
    }
    originals = {name: sys.modules.get(name) for name in replacements}
    sys.modules.update(replacements)
    try:
        db.init()
        with db.conn() as connection:
            connection.execute(
                """
                INSERT INTO orders (
                    order_id, sku, platform, qty, unit_price, total_price,
                    order_date, buyer_name, buyer_phone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "ORDER-1", "SKU-1", "shopee", 1, 125.5, 125.5,
                    "2026-09-28", "Buyer One", "0800000001",
                ),
            )
        yield
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_crm_page_lists_customers_using_total_price() -> None:
    selected_options: list[tuple[list[str], object]] = []
    page = Path(__file__).parent / "pages" / "z_📇_CRM.py"

    with isolated_page(selected_options):
        try:
            runpy.run_path(str(page), run_name="__crm_page_test__")
        except _SelectionReached:
            pass
        else:
            raise AssertionError("CRM page did not reach customer selection")

    options, format_func = selected_options[0]
    assert options == ["0800000001"]
    assert format_func("0800000001") == "Buyer One|1|126"


if __name__ == "__main__":
    test_crm_page_lists_customers_using_total_price()
    print("crm page order total: 1 passed")
