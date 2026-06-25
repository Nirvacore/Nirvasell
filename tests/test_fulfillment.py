"""Tests for fulfillment.py — carrier codes, CSV exports, label HTML, and
mark-shipped logic. Database interactions are mocked via the `db` module."""
from __future__ import annotations

import csv
import io
import sqlite3
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

import pytest

import fulfillment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_csv_bytes(data: bytes) -> list[list[str]]:
    """Decode a UTF-8-BOM CSV export and return rows as lists of strings."""
    text = data.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    return list(reader)


# ---------------------------------------------------------------------------
# carrier_options
# ---------------------------------------------------------------------------

class TestCarrierOptions:
    """Tests for carrier_options()."""

    def test_returns_list_of_tuples(self):
        opts = fulfillment.carrier_options()
        assert isinstance(opts, list)
        for item in opts:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_keys_are_lowercase(self):
        for key, _ in fulfillment.carrier_options():
            assert key == key.lower()

    def test_contains_kerry(self):
        keys = [k for k, _ in fulfillment.carrier_options()]
        assert "kerry" in keys

    def test_contains_flash(self):
        keys = [k for k, _ in fulfillment.carrier_options()]
        assert "flash" in keys

    def test_label_is_human_readable(self):
        for _, label in fulfillment.carrier_options():
            assert len(label) > 0
            assert label[0].isupper()


# ---------------------------------------------------------------------------
# platform_code
# ---------------------------------------------------------------------------

class TestPlatformCode:
    """Tests for platform_code() — carrier key to platform-specific code."""

    def test_kerry_shopee(self):
        assert fulfillment.platform_code("kerry", "shopee") == "KERRY"

    def test_kerry_lazada(self):
        assert fulfillment.platform_code("kerry", "lazada") == "KE"

    def test_kerry_tiktok(self):
        assert fulfillment.platform_code("kerry", "tiktok") == "KEX"

    def test_flash_shopee(self):
        assert fulfillment.platform_code("flash", "shopee") == "FLASH"

    def test_flash_lazada(self):
        assert fulfillment.platform_code("flash", "lazada") == "FLE"

    def test_jt_shopee(self):
        assert fulfillment.platform_code("j&t", "shopee") == "JT"

    def test_case_insensitive_carrier(self):
        assert fulfillment.platform_code("KERRY", "shopee") == "KERRY"
        assert fulfillment.platform_code("Kerry", "lazada") == "KE"

    def test_case_insensitive_platform(self):
        assert fulfillment.platform_code("flash", "SHOPEE") == "FLASH"

    def test_unknown_carrier_returns_uppercased(self):
        assert fulfillment.platform_code("unknown_carrier", "shopee") == "UNKNOWN_CARRIER"

    def test_unknown_platform_returns_label(self):
        """If carrier exists but platform key is unknown, returns the label."""
        result = fulfillment.platform_code("kerry", "unknown_platform")
        assert result == "Kerry Express"

    def test_all_carriers_have_shopee_code(self):
        for key in fulfillment.CARRIERS:
            code = fulfillment.platform_code(key, "shopee")
            assert len(code) > 0

    def test_all_carriers_have_lazada_code(self):
        for key in fulfillment.CARRIERS:
            code = fulfillment.platform_code(key, "lazada")
            assert len(code) > 0

    def test_all_carriers_have_tiktok_code(self):
        for key in fulfillment.CARRIERS:
            code = fulfillment.platform_code(key, "tiktok")
            assert len(code) > 0


# ---------------------------------------------------------------------------
# Shipment CSV exports
# ---------------------------------------------------------------------------

class TestShipmentCsvShopee:
    """Tests for shipment_csv_shopee()."""

    def test_header_row(self):
        rows = _parse_csv_bytes(fulfillment.shipment_csv_shopee([]))
        assert rows[0] == ["Order ID", "Tracking Number", "Shipping Channel"]

    def test_single_row(self):
        data = [{"order_id": "ORD001", "tracking_number": "TRK123", "carrier": "kerry"}]
        rows = _parse_csv_bytes(fulfillment.shipment_csv_shopee(data))
        assert len(rows) == 2
        assert rows[1][0] == "ORD001"
        assert rows[1][1] == "TRK123"
        assert rows[1][2] == "KERRY"

    def test_multiple_rows(self):
        data = [
            {"order_id": "A", "tracking_number": "T1", "carrier": "flash"},
            {"order_id": "B", "tracking_number": "T2", "carrier": "j&t"},
        ]
        rows = _parse_csv_bytes(fulfillment.shipment_csv_shopee(data))
        assert len(rows) == 3
        assert rows[1][2] == "FLASH"
        assert rows[2][2] == "JT"

    def test_missing_tracking_defaults_empty(self):
        data = [{"order_id": "ORD001", "carrier": "kerry"}]
        rows = _parse_csv_bytes(fulfillment.shipment_csv_shopee(data))
        assert rows[1][1] == ""

    def test_output_is_bytes(self):
        result = fulfillment.shipment_csv_shopee([])
        assert isinstance(result, bytes)


class TestShipmentCsvLazada:
    """Tests for shipment_csv_lazada()."""

    def test_header_row(self):
        rows = _parse_csv_bytes(fulfillment.shipment_csv_lazada([]))
        assert rows[0] == ["OrderItemId", "TrackingNumber", "ShipmentProvider"]

    def test_carrier_translation(self):
        data = [{"order_id": "L1", "tracking_number": "T1", "carrier": "kerry"}]
        rows = _parse_csv_bytes(fulfillment.shipment_csv_lazada(data))
        assert rows[1][2] == "KE"


class TestShipmentCsvTiktok:
    """Tests for shipment_csv_tiktok()."""

    def test_header_row(self):
        rows = _parse_csv_bytes(fulfillment.shipment_csv_tiktok([]))
        assert rows[0] == ["Order ID", "Tracking ID", "Shipping Provider"]

    def test_carrier_translation(self):
        data = [{"order_id": "TT1", "tracking_number": "T1", "carrier": "flash"}]
        rows = _parse_csv_bytes(fulfillment.shipment_csv_tiktok(data))
        assert rows[1][2] == "FLE"


class TestShipmentCsvGeneric:
    """Tests for shipment_csv_generic()."""

    def test_header_row(self):
        rows = _parse_csv_bytes(fulfillment.shipment_csv_generic([]))
        assert rows[0] == ["order_id", "platform", "sku", "qty",
                           "tracking_number", "carrier", "shipped_at"]

    def test_full_row(self):
        data = [{
            "order_id": "G1", "platform": "shopee", "sku": "SKU1",
            "qty": 2, "tracking_number": "T1", "carrier": "kerry",
            "shipped_at": "2026-01-01",
        }]
        rows = _parse_csv_bytes(fulfillment.shipment_csv_generic(data))
        assert len(rows) == 2
        assert rows[1][0] == "G1"
        assert rows[1][4] == "T1"


class TestShipmentCsvFor:
    """Tests for shipment_csv_for() — platform dispatch."""

    def test_shopee_dispatches(self):
        data = [{"order_id": "S1", "tracking_number": "T", "carrier": "kerry"}]
        result = fulfillment.shipment_csv_for("shopee", data)
        rows = _parse_csv_bytes(result)
        assert rows[0][0] == "Order ID"

    def test_lazada_dispatches(self):
        data = [{"order_id": "L1", "tracking_number": "T", "carrier": "kerry"}]
        result = fulfillment.shipment_csv_for("lazada", data)
        rows = _parse_csv_bytes(result)
        assert rows[0][0] == "OrderItemId"

    def test_tiktok_dispatches(self):
        data = [{"order_id": "T1", "tracking_number": "T", "carrier": "flash"}]
        result = fulfillment.shipment_csv_for("tiktok", data)
        rows = _parse_csv_bytes(result)
        assert rows[0][0] == "Order ID"
        assert rows[0][1] == "Tracking ID"

    def test_unknown_platform_uses_generic(self):
        data = [{"order_id": "X1", "tracking_number": "T", "carrier": "dhl"}]
        result = fulfillment.shipment_csv_for("ebay", data)
        rows = _parse_csv_bytes(result)
        assert rows[0] == ["order_id", "platform", "sku", "qty",
                           "tracking_number", "carrier", "shipped_at"]

    def test_none_platform_uses_generic(self):
        result = fulfillment.shipment_csv_for(None, [])
        rows = _parse_csv_bytes(result)
        assert rows[0][0] == "order_id"

    def test_case_insensitive_platform(self):
        data = [{"order_id": "S1", "tracking_number": "T", "carrier": "kerry"}]
        result = fulfillment.shipment_csv_for("SHOPEE", data)
        rows = _parse_csv_bytes(result)
        assert rows[0][0] == "Order ID"


# ---------------------------------------------------------------------------
# _html (HTML escaping)
# ---------------------------------------------------------------------------

class TestHtmlEscape:
    """Tests for _html() — internal HTML escape helper."""

    def test_none_returns_empty(self):
        assert fulfillment._html(None) == ""

    def test_plain_text_unchanged(self):
        assert fulfillment._html("hello") == "hello"

    def test_ampersand_escaped(self):
        assert "&amp;" in fulfillment._html("a & b")

    def test_angle_brackets_escaped(self):
        assert "&lt;" in fulfillment._html("<script>")
        assert "&gt;" in fulfillment._html("end>")

    def test_quotes_escaped(self):
        assert "&quot;" in fulfillment._html('say "hi"')

    def test_numeric_value(self):
        assert fulfillment._html(42) == "42"


# ---------------------------------------------------------------------------
# label_html
# ---------------------------------------------------------------------------

class TestLabelHtml:
    """Tests for label_html() — printable shipping label generation."""

    def test_empty_list_produces_valid_html(self):
        html = fulfillment.label_html([])
        assert "<!doctype html>" in html.lower()
        assert "</html>" in html

    def test_single_label_contains_order_info(self):
        orders = [{"order_id": "ORD-123", "sku": "SKU-A", "qty": 2,
                    "carrier": "kerry", "tracking_number": "TRK999",
                    "buyer_name": "Test Buyer", "buyer_address": "123 St",
                    "buyer_phone": "0812345678", "platform": "shopee"}]
        html = fulfillment.label_html(orders, seller_name="My Shop")
        assert "ORD-123" in html
        assert "SKU-A" in html
        assert "TRK999" in html
        assert "Test Buyer" in html
        assert "My Shop" in html

    def test_seller_defaults_to_seller(self):
        html = fulfillment.label_html([{"order_id": "X"}])
        assert "Seller" in html

    def test_html_escaping_in_labels(self):
        orders = [{"buyer_name": "<script>alert('xss')</script>"}]
        html = fulfillment.label_html(orders)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_multiple_orders_produce_multiple_labels(self):
        orders = [{"order_id": f"ORD-{i}"} for i in range(3)]
        html = fulfillment.label_html(orders)
        assert html.count("class='label'") == 3

    def test_missing_fields_use_dashes(self):
        html = fulfillment.label_html([{}])
        # buyer_name and buyer_address default to em dash when missing
        assert "—" in html or "&mdash;" in html.lower() or "—" in html


# ---------------------------------------------------------------------------
# mark_shipped (database mocked)
# ---------------------------------------------------------------------------

class TestMarkShipped:
    """Tests for mark_shipped() with mocked database."""

    def _make_mock_conn(self, order_row=None, stock_row=None):
        """Create a mock db.conn() context manager that returns a mock cursor."""
        mock_cursor = MagicMock()

        def execute_side_effect(sql, params=None):
            result = MagicMock()
            if params is None:
                return result
            sql_lower = sql.strip().lower()
            if "select product_id, qty from orders" in sql_lower:
                result.fetchone.return_value = order_row
            elif "select stock from products" in sql_lower:
                result.fetchone.return_value = stock_row
            else:
                result.fetchone.return_value = None
            return result

        mock_cursor.execute = MagicMock(side_effect=execute_side_effect)

        @contextmanager
        def mock_conn():
            yield mock_cursor

        return mock_conn, mock_cursor

    @patch("fulfillment.init")
    @patch("fulfillment.db")
    def test_empty_tracking_returns_false(self, mock_db, mock_init):
        result = fulfillment.mark_shipped(1, tracking_number="", carrier="kerry")
        assert result is False

    @patch("fulfillment.init")
    @patch("fulfillment.db")
    def test_whitespace_tracking_returns_false(self, mock_db, mock_init):
        result = fulfillment.mark_shipped(1, tracking_number="   ", carrier="kerry")
        assert result is False

    @patch("fulfillment.init")
    @patch("fulfillment.db")
    def test_valid_tracking_returns_true(self, mock_db, mock_init):
        order_row = {"product_id": 10, "qty": 1}
        stock_row = {"stock": "5"}
        mock_conn, mock_cursor = self._make_mock_conn(order_row, stock_row)
        mock_db.conn = mock_conn

        result = fulfillment.mark_shipped(
            1, tracking_number="TRK123", carrier="kerry"
        )
        assert result is True

    @patch("fulfillment.init")
    @patch("fulfillment.db")
    def test_no_decrement_when_flag_false(self, mock_db, mock_init):
        order_row = {"product_id": 10, "qty": 1}
        mock_conn, mock_cursor = self._make_mock_conn(order_row)
        mock_db.conn = mock_conn

        fulfillment.mark_shipped(
            1, tracking_number="TRK123", carrier="kerry", decrement_stock=False
        )
        # Should NOT query products table for stock
        calls = [str(c) for c in mock_cursor.execute.call_args_list]
        stock_queries = [c for c in calls if "select stock from products" in c.lower()]
        assert len(stock_queries) == 0


# ---------------------------------------------------------------------------
# mark_shipped_bulk
# ---------------------------------------------------------------------------

class TestMarkShippedBulk:
    """Tests for mark_shipped_bulk()."""

    @patch("fulfillment.mark_shipped")
    def test_counts_successful_updates(self, mock_mark):
        mock_mark.return_value = True
        items = [
            {"id": 1, "tracking_number": "T1", "carrier": "kerry"},
            {"id": 2, "tracking_number": "T2", "carrier": "flash"},
        ]
        assert fulfillment.mark_shipped_bulk(items) == 2

    @patch("fulfillment.mark_shipped")
    def test_counts_partial_success(self, mock_mark):
        mock_mark.side_effect = [True, False, True]
        items = [
            {"id": 1, "tracking_number": "T1", "carrier": "kerry"},
            {"id": 2, "tracking_number": "", "carrier": "flash"},
            {"id": 3, "tracking_number": "T3", "carrier": "j&t"},
        ]
        assert fulfillment.mark_shipped_bulk(items) == 2

    @patch("fulfillment.mark_shipped")
    def test_empty_list(self, mock_mark):
        assert fulfillment.mark_shipped_bulk([]) == 0
        mock_mark.assert_not_called()

    @patch("fulfillment.mark_shipped")
    def test_missing_tracking_defaults_empty(self, mock_mark):
        mock_mark.return_value = False
        items = [{"id": 1, "carrier": "kerry"}]
        fulfillment.mark_shipped_bulk(items)
        mock_mark.assert_called_once_with(
            1, tracking_number="", carrier="kerry"
        )


# ---------------------------------------------------------------------------
# CARRIERS constant
# ---------------------------------------------------------------------------

class TestCarriersConstant:
    """Validate the CARRIERS data structure."""

    def test_all_entries_have_required_keys(self):
        for key, entry in fulfillment.CARRIERS.items():
            assert "label" in entry, f"{key} missing label"
            assert "shopee" in entry, f"{key} missing shopee"
            assert "lazada" in entry, f"{key} missing lazada"
            assert "tiktok" in entry, f"{key} missing tiktok"

    def test_at_least_five_carriers(self):
        assert len(fulfillment.CARRIERS) >= 5

    def test_keys_are_lowercase(self):
        for key in fulfillment.CARRIERS:
            assert key == key.lower()

    def test_labels_are_non_empty(self):
        for key, entry in fulfillment.CARRIERS.items():
            assert len(entry["label"]) > 0


# ---------------------------------------------------------------------------
# PLATFORM_CSV dispatch map
# ---------------------------------------------------------------------------

class TestPlatformCsvMap:
    """Validate the PLATFORM_CSV dispatch dict."""

    def test_contains_shopee(self):
        assert "shopee" in fulfillment.PLATFORM_CSV

    def test_contains_lazada(self):
        assert "lazada" in fulfillment.PLATFORM_CSV

    def test_contains_tiktok(self):
        assert "tiktok" in fulfillment.PLATFORM_CSV

    def test_values_are_callable(self):
        for key, fn in fulfillment.PLATFORM_CSV.items():
            assert callable(fn), f"{key} value is not callable"
