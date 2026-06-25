"""Tests for invoices.py — invoice creation, VAT, text rendering, and stats."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from unittest.mock import patch

import pytest

# In-memory SQLite wired through db.conn()
_mem_db: sqlite3.Connection | None = None


class _ConnWrapper:
    """Thin proxy that forwards lastrowid from the most recent cursor."""

    def __init__(self, real_conn: sqlite3.Connection):
        self._conn = real_conn
        self.lastrowid: int | None = None

    def execute(self, sql, params=()):
        cur = self._conn.execute(sql, params)
        self.lastrowid = cur.lastrowid
        return cur

    def executescript(self, sql):
        return self._conn.executescript(sql)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    @property
    def row_factory(self):
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, value):
        self._conn.row_factory = value


@contextmanager
def _mem_conn():
    global _mem_db
    if _mem_db is None:
        _mem_db = sqlite3.connect(":memory:")
        _mem_db.row_factory = sqlite3.Row
        _mem_db.execute("PRAGMA foreign_keys = ON")
    wrapper = _ConnWrapper(_mem_db)
    try:
        yield wrapper
        _mem_db.commit()
    except Exception:
        _mem_db.rollback()
        raise


@pytest.fixture(autouse=True)
def _fresh_db():
    """Provide a clean in-memory database for every test."""
    global _mem_db
    _mem_db = None
    with patch("db.conn", _mem_conn):
        import invoices
        invoices.init()
        yield


# ---------------------------------------------------------------------------
# create — basic
# ---------------------------------------------------------------------------

class TestCreate:
    def test_create_empty_invoice(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create()
        assert isinstance(inv_id, int)
        assert inv_id >= 1

    def test_create_with_items(self):
        import invoices
        items = [
            {"sku": "A001", "description": "Widget", "qty": 2, "unit_price": 100},
            {"sku": "B002", "description": "Gadget", "qty": 1, "unit_price": 500},
        ]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items)
            inv = invoices.get(inv_id)
        assert inv is not None
        assert len(inv["items"]) == 2

    def test_create_calculates_subtotal(self):
        import invoices
        items = [
            {"description": "A", "qty": 3, "unit_price": 100},
            {"description": "B", "qty": 2, "unit_price": 50},
        ]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items)
            inv = invoices.get(inv_id)
        assert inv["subtotal"] == 400.0  # 300 + 100

    def test_create_no_vat_by_default(self):
        import invoices
        items = [{"description": "X", "qty": 1, "unit_price": 1000}]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items)
            inv = invoices.get(inv_id)
        assert inv["vat_amount"] == 0
        assert inv["total"] == 1000.0
        assert inv["include_vat"] == 0

    def test_create_with_vat(self):
        import invoices
        items = [{"description": "X", "qty": 1, "unit_price": 1000}]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items, include_vat=True)
            inv = invoices.get(inv_id)
        assert inv["vat_amount"] == 70.0  # 1000 * 0.07
        assert inv["total"] == 1070.0
        assert inv["include_vat"] == 1

    def test_create_stores_customer_info(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(
                customer_name="Test Customer",
                customer_address="123 Bangkok",
                customer_tax_id="1234567890123",
            )
            inv = invoices.get(inv_id)
        assert inv["customer_name"] == "Test Customer"
        assert inv["customer_address"] == "123 Bangkok"
        assert inv["customer_tax_id"] == "1234567890123"

    def test_create_stores_order_id(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(order_id="ORD-12345")
            inv = invoices.get(inv_id)
        assert inv["order_id"] == "ORD-12345"

    def test_create_stores_notes(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(notes="ชำระภายใน 30 วัน")
            inv = invoices.get(inv_id)
        assert inv["notes"] == "ชำระภายใน 30 วัน"

    def test_create_item_line_totals(self):
        import invoices
        items = [
            {"description": "Widget", "qty": 5, "unit_price": 80.50},
        ]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items)
            inv = invoices.get(inv_id)
        assert inv["items"][0]["line_total"] == 402.50

    def test_create_item_defaults(self):
        """Items with missing qty/unit_price default to 1 and 0."""
        import invoices
        items = [{"description": "Freebie"}]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items)
            inv = invoices.get(inv_id)
        assert inv["items"][0]["qty"] == 1
        assert inv["items"][0]["unit_price"] == 0
        assert inv["items"][0]["line_total"] == 0


# ---------------------------------------------------------------------------
# _next_number
# ---------------------------------------------------------------------------

class TestNextNumber:
    def test_first_invoice_number_format(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create()
            inv = invoices.get(inv_id)
        num = inv["invoice_number"]
        assert num.startswith("INV-")
        assert num.endswith("-0001")

    def test_sequential_numbering(self):
        import invoices
        with patch("db.conn", _mem_conn):
            id1 = invoices.create()
            id2 = invoices.create()
            inv1 = invoices.get(id1)
            inv2 = invoices.get(id2)
        assert inv1["invoice_number"].endswith("-0001")
        assert inv2["invoice_number"].endswith("-0002")

    def test_number_includes_year_month(self):
        import invoices
        from datetime import datetime
        ym = datetime.now().strftime("%Y%m")
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create()
            inv = invoices.get(inv_id)
        assert ym in inv["invoice_number"]


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

class TestGet:
    def test_get_existing_invoice(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(customer_name="Test")
            inv = invoices.get(inv_id)
        assert inv is not None
        assert inv["customer_name"] == "Test"
        assert "items" in inv

    def test_get_nonexistent_returns_none(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv = invoices.get(99999)
        assert inv is None

    def test_get_includes_items(self):
        import invoices
        items = [
            {"description": "A", "qty": 1, "unit_price": 100},
            {"description": "B", "qty": 2, "unit_price": 200},
        ]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items)
            inv = invoices.get(inv_id)
        assert len(inv["items"]) == 2
        descriptions = {item["description"] for item in inv["items"]}
        assert descriptions == {"A", "B"}


# ---------------------------------------------------------------------------
# all_invoices
# ---------------------------------------------------------------------------

class TestAllInvoices:
    def test_empty_initially(self):
        import invoices
        with patch("db.conn", _mem_conn):
            result = invoices.all_invoices()
        assert result == []

    def test_returns_list_of_dicts(self):
        import invoices
        with patch("db.conn", _mem_conn):
            invoices.create(customer_name="A")
            invoices.create(customer_name="B")
            result = invoices.all_invoices()
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], dict)

    def test_limit_parameter(self):
        import invoices
        with patch("db.conn", _mem_conn):
            for _ in range(10):
                invoices.create()
            result = invoices.all_invoices(limit=3)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# render_text
# ---------------------------------------------------------------------------

class TestRenderText:
    def test_render_empty_invoice(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create()
            text = invoices.render_text(inv_id)
        assert "ใบกำกับภาษี" in text
        assert "TAX INVOICE" in text

    def test_render_nonexistent_returns_empty(self):
        import invoices
        with patch("db.conn", _mem_conn):
            text = invoices.render_text(99999)
        assert text == ""

    def test_render_includes_invoice_number(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create()
            inv = invoices.get(inv_id)
            text = invoices.render_text(inv_id)
        assert inv["invoice_number"] in text

    def test_render_includes_customer_info(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(
                customer_name="ร้าน ABC",
                customer_address="กรุงเทพ",
                customer_tax_id="1234567890123",
            )
            text = invoices.render_text(inv_id)
        assert "ร้าน ABC" in text
        assert "กรุงเทพ" in text
        assert "1234567890123" in text

    def test_render_includes_order_id(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(order_id="ORD-999")
            text = invoices.render_text(inv_id)
        assert "ORD-999" in text

    def test_render_includes_items(self):
        import invoices
        items = [{"description": "สินค้าทดสอบ", "qty": 3, "unit_price": 250}]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items)
            text = invoices.render_text(inv_id)
        # The item description should appear (possibly truncated to 24 chars)
        assert "สินค้าทดสอบ" in text

    def test_render_shows_vat_when_included(self):
        import invoices
        items = [{"description": "A", "qty": 1, "unit_price": 1000}]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items, include_vat=True)
            text = invoices.render_text(inv_id)
        assert "VAT 7%" in text

    def test_render_hides_vat_when_not_included(self):
        import invoices
        items = [{"description": "A", "qty": 1, "unit_price": 1000}]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items, include_vat=False)
            text = invoices.render_text(inv_id)
        assert "VAT 7%" not in text

    def test_render_includes_notes(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(notes="กรุณาชำระภายใน 7 วัน")
            text = invoices.render_text(inv_id)
        assert "กรุณาชำระภายใน 7 วัน" in text

    def test_render_includes_total_line(self):
        import invoices
        items = [{"description": "Widget", "qty": 2, "unit_price": 500}]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items)
            text = invoices.render_text(inv_id)
        assert "รวมทั้งสิ้น" in text
        assert "1000.00" in text


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_empty_stats(self):
        import invoices
        with patch("db.conn", _mem_conn):
            s = invoices.stats()
        assert s["total"] == 0
        assert s["total_revenue"] == 0

    def test_stats_counts_invoices(self):
        import invoices
        items = [{"description": "X", "qty": 1, "unit_price": 500}]
        with patch("db.conn", _mem_conn):
            invoices.create(items=items)
            invoices.create(items=items)
            s = invoices.stats()
        assert s["total"] == 2
        assert s["total_revenue"] == 1000.0


# ---------------------------------------------------------------------------
# VAT calculation edge cases
# ---------------------------------------------------------------------------

class TestVatCalculation:
    def test_vat_rate_is_seven_percent(self):
        import invoices
        assert invoices.VAT_RATE == 0.07

    def test_vat_on_multiple_items(self):
        import invoices
        items = [
            {"description": "A", "qty": 2, "unit_price": 100},
            {"description": "B", "qty": 1, "unit_price": 300},
        ]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items, include_vat=True)
            inv = invoices.get(inv_id)
        # subtotal = 200 + 300 = 500
        assert inv["subtotal"] == 500.0
        assert inv["vat_amount"] == 35.0  # 500 * 0.07
        assert inv["total"] == 535.0

    def test_vat_rounding(self):
        import invoices
        items = [{"description": "A", "qty": 1, "unit_price": 33.33}]
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=items, include_vat=True)
            inv = invoices.get(inv_id)
        expected_vat = round(33.33 * 0.07, 2)
        assert inv["vat_amount"] == expected_vat

    def test_zero_total_with_vat(self):
        import invoices
        with patch("db.conn", _mem_conn):
            inv_id = invoices.create(items=[], include_vat=True)
            inv = invoices.get(inv_id)
        assert inv["subtotal"] == 0
        assert inv["vat_amount"] == 0
        assert inv["total"] == 0


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_invoice_prefix(self):
        import invoices
        assert invoices.INVOICE_PREFIX == "INV"

    def test_vat_rate_between_zero_and_one(self):
        import invoices
        assert 0 < invoices.VAT_RATE < 1
