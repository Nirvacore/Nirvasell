"""Canonical order lookup, COD evidence, CSV, and isolation regressions."""
from __future__ import annotations

import math
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

if "streamlit" not in sys.modules:
    fake_streamlit = types.ModuleType("streamlit")
    fake_streamlit.session_state = {}
    sys.modules["streamlit"] = fake_streamlit

import cod_tracker
import db
import label_generator


@contextmanager
def isolated_database():
    original_resolver = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_labels_") as temp:
        db._resolve_path = lambda: Path(temp) / "user.db"
        try:
            db.init()
            cod_tracker.init()
            yield
        finally:
            db._resolve_path = original_resolver


def add_order(
    connection,
    *,
    order_id: str,
    sku: str,
    platform: str = "shopee",
    qty=1,
    unit_price=100.0,
    total_price=100.0,
    order_date="2026-09-28T00:30:00+07:00",
    buyer_name="Buyer",
    buyer_phone="0812345678",
    buyer_address="Bangkok",
    tracking_number="TRACK-1",
    carrier="kerry",
):
    return connection.execute(
        """INSERT INTO orders
           (order_id,sku,platform,qty,unit_price,total_price,order_date,status,
            buyer_name,buyer_phone,buyer_address,tracking_number,carrier)
           VALUES (?,?,?,?,?,?,?,'paid',?,?,?,?,?)""",
        (
            order_id, sku, platform, qty, unit_price, total_price, order_date,
            buyer_name, buyer_phone, buyer_address, tracking_number, carrier,
        ),
    ).lastrowid


def add_cod(connection, *, order_id: str, platform: str = "shopee",
            payment_type: str = "cod", amount=100.0):
    connection.execute(
        """INSERT INTO cod_orders (order_id,platform,payment_type,amount)
           VALUES (?,?,?,?)""",
        (order_id, platform, payment_type, amount),
    )


def test_lookup_uses_only_exact_platform_and_external_order_id() -> None:
    with isolated_database():
        with db.conn() as connection:
            internal_id = add_order(
                connection, order_id="EXTERNAL-A", sku="SKU-A", platform="shopee"
            )
            add_order(
                connection, order_id="REUSED", sku="SKU-S", platform="shopee",
                total_price=125,
            )
            add_order(
                connection, order_id="REUSED", sku="SKU-L", platform="lazada",
                total_price=900,
            )

        shopee = label_generator.from_order("shopee", "REUSED")
        assert shopee["ok"] is True
        assert shopee["order"]["platform"] == "shopee"
        assert shopee["order"]["order_id"] == "REUSED"
        assert shopee["order"]["total_price"] == 125.0
        assert "SKU-S" in shopee["label"]
        assert "SKU-L" not in shopee["label"]

        collision = label_generator.from_order("shopee", str(internal_id))
        assert collision["ok"] is False
        assert collision["code"] == "not_found"


def test_multi_sku_rows_aggregate_without_exposing_internal_ids() -> None:
    with isolated_database():
        with db.conn() as connection:
            first_id = add_order(
                connection, order_id="MULTI-1", sku="SKU-1", qty=2,
                unit_price=50, total_price=100,
            )
            second_id = add_order(
                connection, order_id="MULTI-1", sku="SKU-2", qty=1,
                unit_price=75, total_price=75,
            )

        result = label_generator.from_order("shopee", "MULTI-1")
        assert result["ok"] is True
        assert result["order"]["total_price"] == 175.0
        assert result["order"]["items"] == [
            {"sku": "SKU-1", "qty": 2, "price": 50.0},
            {"sku": "SKU-2", "qty": 1, "price": 75.0},
        ]
        assert "MULTI-1" in result["label"]
        assert f"Order: {first_id}" not in result["label"]
        assert f"Order: {second_id}" not in result["label"]


def test_conflicting_and_incomplete_evidence_fail_closed() -> None:
    with isolated_database():
        with db.conn() as connection:
            add_order(connection, order_id="CONFLICT", sku="SKU-1")
            add_order(
                connection, order_id="CONFLICT", sku="SKU-2",
                buyer_phone="0899999999",
            )
            add_order(
                connection, order_id="INCOMPLETE", sku="SKU-3", carrier="   ",
            )

        conflict = label_generator.from_order("shopee", "CONFLICT")
        assert conflict["ok"] is False
        assert conflict["code"] == "conflicting_evidence"
        incomplete = label_generator.from_order("shopee", "INCOMPLETE")
        assert incomplete["ok"] is False
        assert incomplete["code"] == "incomplete_evidence"


def test_each_required_shipping_field_must_be_nonblank() -> None:
    fields = (
        "buyer_name", "buyer_phone", "buyer_address",
        "tracking_number", "carrier",
    )
    with isolated_database():
        with db.conn() as connection:
            for field in fields:
                add_order(
                    connection,
                    order_id=f"BLANK-{field}",
                    sku=f"SKU-{field}",
                    **{field: "   "},
                )

        for field in fields:
            result = label_generator.from_order("shopee", f"BLANK-{field}")
            assert result["ok"] is False, field
            assert result["code"] == "incomplete_evidence", field


def test_duplicate_sku_rows_in_a_legacy_database_are_ambiguous() -> None:
    original_resolver = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_label_legacy_") as temp:
        db._resolve_path = lambda: Path(temp) / "legacy.db"
        try:
            with db.conn() as connection:
                connection.executescript(
                    """CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT);
                       CREATE TABLE orders (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           order_id TEXT, sku TEXT, platform TEXT, qty REAL,
                           unit_price REAL, total_price REAL, order_date TEXT,
                           status TEXT, buyer_name TEXT, buyer_phone TEXT,
                           buyer_address TEXT, tracking_number TEXT, carrier TEXT
                       );"""
                )
                add_order(connection, order_id="DUP-SKU", sku="SKU-1")
                add_order(connection, order_id="DUP-SKU", sku="SKU-1")

            result = label_generator.from_order("shopee", "DUP-SKU")
            assert result["ok"] is False
            assert result["code"] == "ambiguous_order"
        finally:
            db._resolve_path = original_resolver


def test_explicit_cod_prepaid_absent_and_duplicate_evidence_are_truthful() -> None:
    with isolated_database():
        with db.conn() as connection:
            for order_id in ("COD", "PREPAID", "ABSENT", "DUPLICATE"):
                add_order(connection, order_id=order_id, sku=f"SKU-{order_id}")
            add_cod(connection, order_id="COD", payment_type="cod", amount=110)
            add_cod(connection, order_id="PREPAID", payment_type="prepaid", amount=0)
            add_cod(connection, order_id="DUPLICATE", payment_type="cod", amount=100)
            add_cod(connection, order_id="DUPLICATE", payment_type="cod", amount=100)

        original_t = label_generator.t
        label_generator.t = lambda key, **fmt: key + str(fmt)
        try:
            cod = label_generator.from_order("shopee", "COD", style="cod")
            assert cod["order"]["cod_state"] == "cod"
            assert cod["order"]["cod_amount"] == 110.0
            assert "lbl.body_cod_collect" in cod["label"]

            prepaid = label_generator.from_order("shopee", "PREPAID", style="cod")
            assert prepaid["order"]["cod_state"] == "prepaid"
            assert prepaid["order"]["cod_amount"] == 0.0
            assert "lbl.body_cod_collect" not in prepaid["label"]

            for order_id in ("ABSENT", "DUPLICATE"):
                result = label_generator.from_order("shopee", order_id, style="cod")
                assert result["ok"] is True
                assert result["order"]["cod_state"] == "unknown"
                assert result["order"]["cod_amount"] is None
                assert "lbl.body_cod_collect" not in result["label"]
        finally:
            label_generator.t = original_t


def test_invalid_numeric_and_date_evidence_fail_closed() -> None:
    with isolated_database():
        cases = [
            ("NULL-QTY", {"qty": None}),
            ("NEGATIVE-QTY", {"qty": -1}),
            ("INF-UNIT", {"unit_price": math.inf}),
            ("NAN-TOTAL", {"total_price": math.nan}),
            ("NEGATIVE-TOTAL", {"total_price": -1}),
            ("BAD-DATE", {"order_date": "09/28/2026"}),
            ("FUTURE-DATE", {"order_date": "9999-01-01"}),
        ]
        with db.conn() as connection:
            for order_id, overrides in cases:
                add_order(
                    connection,
                    order_id=order_id,
                    sku=f"SKU-{order_id}",
                    **overrides,
                )

        for order_id, _overrides in cases:
            result = label_generator.from_order("shopee", order_id)
            assert result["ok"] is False, order_id
            assert result["code"] == "incomplete_evidence", order_id


def test_bulk_csv_preserves_quoted_commas_first_row_and_each_error() -> None:
    result = label_generator.generate_bulk_labels(
        'FIRST-1,Alice,0812345678,"123 Main, Bangkok",100,0\n'
        'BAD-TOTAL,Bob,0899999999,Chiang Mai,not-a-number,0\n'
        'TOO-SHORT,Only two fields\n',
        style="full",
    )
    assert len(result["labels"]) == 1
    assert "FIRST-1" in result["labels"][0]
    assert "123 Main, Bangkok" in result["labels"][0]
    assert [error["row"] for error in result["errors"]] == [2, 3]
    assert [error["code"] for error in result["errors"]] == [
        "invalid_numeric", "invalid_columns",
    ]


def test_lookup_preserves_active_per_user_database_isolation() -> None:
    original_resolver = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_label_users_") as temp:
        active = {"path": Path(temp) / "user-a.db"}
        db._resolve_path = lambda: active["path"]
        try:
            db.init()
            cod_tracker.init()
            with db.conn() as connection:
                add_order(connection, order_id="SHARED", sku="USER-A")

            active["path"] = Path(temp) / "user-b.db"
            db.init()
            cod_tracker.init()
            with db.conn() as connection:
                add_order(connection, order_id="SHARED", sku="USER-B")

            result_b = label_generator.from_order("shopee", "SHARED")
            assert result_b["order"]["items"][0]["sku"] == "USER-B"
            active["path"] = Path(temp) / "user-a.db"
            result_a = label_generator.from_order("shopee", "SHARED")
            assert result_a["order"]["items"][0]["sku"] == "USER-A"
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_lookup_uses_only_exact_platform_and_external_order_id()
    test_multi_sku_rows_aggregate_without_exposing_internal_ids()
    test_conflicting_and_incomplete_evidence_fail_closed()
    test_each_required_shipping_field_must_be_nonblank()
    test_duplicate_sku_rows_in_a_legacy_database_are_ambiguous()
    test_explicit_cod_prepaid_absent_and_duplicate_evidence_are_truthful()
    test_invalid_numeric_and_date_evidence_fail_closed()
    test_bulk_csv_preserves_quoted_commas_first_row_and_each_error()
    test_lookup_preserves_active_per_user_database_isolation()
    print("label generator canonical lookup: 9 passed")
