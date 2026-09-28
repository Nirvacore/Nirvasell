"""Regression coverage for atomic, inventory-neutral shipment transitions."""

from __future__ import annotations

import tempfile
import sys
import types
from concurrent.futures import ThreadPoolExecutor
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
import fulfillment


@contextmanager
def isolated_database():
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_fulfillment_") as temp:
        db._resolve_path = lambda: Path(temp) / "user.db"
        try:
            db.init()
            fulfillment.init()
            yield
        finally:
            db._resolve_path = original_resolve_path


def insert_order(*, status: str, tracking_number=None, shipped_at=None,
                 product_id=None, order_id="ORDER-1") -> int:
    with db.conn() as connection:
        cursor = connection.execute(
            """INSERT INTO orders
               (order_id, sku, product_id, platform, qty, unit_price,
                total_price, order_date, status, tracking_number, shipped_at)
               VALUES (?, ?, ?, 'shopee', 2, 50, 100, '2026-09-28', ?, ?, ?)""",
            (order_id, f"SKU-{order_id}", product_id, status,
             tracking_number, shipped_at),
        )
        return cursor.lastrowid


def order_state(order_id: int):
    with db.conn() as connection:
        return dict(connection.execute(
            """SELECT status, tracking_number, carrier, shipped_at
               FROM orders WHERE id = ?""",
            (order_id,),
        ).fetchone())


def test_first_eligible_transition_succeeds_once_without_decrementing_stock() -> None:
    with isolated_database():
        with db.conn() as connection:
            product_id = connection.execute(
                "INSERT INTO products (sku, name, stock) VALUES ('STOCK-1', 'One', 10)"
            ).lastrowid
        order_id = insert_order(status="paid", product_id=product_id)

        assert fulfillment.mark_shipped(
            order_id, tracking_number="TH-12345", carrier="kerry"
        ) is True
        first = order_state(order_id)
        assert first["status"] == "shipped"
        assert first["tracking_number"] == "TH-12345"
        assert first["carrier"] == "kerry"
        assert first["shipped_at"].endswith("+00:00")

        assert fulfillment.mark_shipped(
            order_id, tracking_number="REPLACEMENT", carrier="flash"
        ) is False
        assert order_state(order_id) == first
        with db.conn() as connection:
            assert connection.execute(
                "SELECT stock FROM products WHERE id = ?", (product_id,)
            ).fetchone()[0] == 10


def test_confirmed_transition_is_atomic_under_concurrent_retries() -> None:
    with isolated_database():
        order_id = insert_order(status=" confirmed ")

        def transition(args):
            tracking, carrier = args
            return fulfillment.mark_shipped(
                order_id, tracking_number=tracking, carrier=carrier
            )

        attempts = [("TH-A", "kerry"), ("TH-B", "flash")]
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(transition, attempts))

        assert sorted(outcomes) == [False, True]
        state = order_state(order_id)
        assert (state["tracking_number"], state["carrier"]) in attempts
        shipped_at = state["shipped_at"]
        assert fulfillment.mark_shipped(
            order_id, tracking_number="TH-C", carrier="dhl"
        ) is False
        assert order_state(order_id)["shipped_at"] == shipped_at


def test_ineligible_missing_and_prepopulated_shipments_fail_without_mutation() -> None:
    with isolated_database():
        cases = [
            ("cancelled", None, None),
            ("refunded", None, None),
            ("unknown", None, None),
            ("paid", "EXISTING", "2026-09-01T00:00:00+00:00"),
            ("paid", None, "2026-09-01T00:00:00+00:00"),
        ]
        for index, (status, tracking, shipped_at) in enumerate(cases):
            order_id = insert_order(
                status=status,
                tracking_number=tracking,
                shipped_at=shipped_at,
                order_id=f"CASE-{index}",
            )
            before = order_state(order_id)
            assert fulfillment.mark_shipped(
                order_id, tracking_number="NEW", carrier="kerry"
            ) is False
            assert order_state(order_id) == before

        assert fulfillment.mark_shipped(
            999999, tracking_number="NEW", carrier="kerry"
        ) is False


def test_identifiers_tracking_and_carrier_are_bounded_and_validated() -> None:
    with isolated_database():
        order_id = insert_order(status="paid")
        invalid = [
            (True, "TRACK", "kerry"),
            (0, "TRACK", "kerry"),
            (-1, "TRACK", "kerry"),
            (2**63, "TRACK", "kerry"),
            (order_id, "", "kerry"),
            (order_id, "   ", "kerry"),
            (order_id, "A" * 101, "kerry"),
            (order_id, "BAD TRACK", "kerry"),
            (order_id, "TRACK", "unknown"),
            (order_id, "TRACK", ""),
        ]
        for invalid_id, tracking, carrier in invalid:
            assert fulfillment.mark_shipped(
                invalid_id, tracking_number=tracking, carrier=carrier
            ) is False
        assert order_state(order_id)["status"] == "paid"


def test_bulk_count_reflects_only_real_conditional_transitions() -> None:
    with isolated_database():
        paid = insert_order(status="paid", order_id="BULK-PAID")
        confirmed = insert_order(status="confirmed", order_id="BULK-CONFIRMED")
        cancelled = insert_order(status="cancelled", order_id="BULK-CANCELLED")
        count = fulfillment.mark_shipped_bulk([
            {"id": paid, "tracking_number": "P-1", "carrier": "kerry"},
            {"id": confirmed, "tracking_number": "C-1", "carrier": "flash"},
            {"id": cancelled, "tracking_number": "X-1", "carrier": "dhl"},
            {"id": 999999, "tracking_number": "N-1", "carrier": "dhl"},
            {"id": paid, "tracking_number": "P-2", "carrier": "dhl"},
            {"id": "bad", "tracking_number": "B-1", "carrier": "dhl"},
        ])
        assert count == 2
        assert order_state(cancelled)["status"] == "cancelled"


def test_pending_views_only_include_eligible_untracked_orders() -> None:
    with isolated_database():
        insert_order(status="paid", order_id="PENDING-PAID")
        insert_order(status="confirmed", order_id="PENDING-CONFIRMED")
        insert_order(status="cancelled", order_id="NOT-PENDING")
        insert_order(status="paid", tracking_number="DONE", order_id="TRACKED")

        assert {row["order_id"] for row in fulfillment.pending_orders()} == {
            "PENDING-PAID", "PENDING-CONFIRMED"
        }
        assert fulfillment.platforms_with_pending() == ["shopee"]
        summary = fulfillment.stats()
        assert summary["pending"] == 2
        assert summary["shipped"] == 1


def test_active_per_user_database_isolation_is_preserved() -> None:
    original_resolve_path = db._resolve_path
    with tempfile.TemporaryDirectory(prefix="nirvasell_fulfillment_users_") as temp:
        active = {"path": Path(temp) / "user-a.db"}
        db._resolve_path = lambda: active["path"]
        try:
            db.init()
            fulfillment.init()
            user_a_id = insert_order(status="paid", order_id="USER-A")

            active["path"] = Path(temp) / "user-b.db"
            db.init()
            fulfillment.init()
            user_b_id = insert_order(status="paid", order_id="USER-B")
            assert user_b_id == user_a_id

            active["path"] = Path(temp) / "user-a.db"
            assert fulfillment.mark_shipped(
                user_a_id, tracking_number="A-1", carrier="kerry"
            ) is True

            active["path"] = Path(temp) / "user-b.db"
            assert order_state(user_b_id)["status"] == "paid"
        finally:
            db._resolve_path = original_resolve_path


if __name__ == "__main__":
    test_first_eligible_transition_succeeds_once_without_decrementing_stock()
    test_confirmed_transition_is_atomic_under_concurrent_retries()
    test_ineligible_missing_and_prepopulated_shipments_fail_without_mutation()
    test_identifiers_tracking_and_carrier_are_bounded_and_validated()
    test_bulk_count_reflects_only_real_conditional_transitions()
    test_pending_views_only_include_eligible_untracked_orders()
    test_active_per_user_database_isolation_is_preserved()
    print("fulfillment transition: 7 passed")
