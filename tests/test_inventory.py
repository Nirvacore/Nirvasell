"""Tests for inventory.py — stock parsing, audit, filtering, and normalization."""
from __future__ import annotations

import pytest
import pandas as pd

import inventory


# ---------------------------------------------------------------------------
# parse_stock
# ---------------------------------------------------------------------------

class TestParseStock:
    """Tests for parse_stock() — free-text stock extraction."""

    def test_integer_string(self):
        assert inventory.parse_stock("5") == 5

    def test_zero_string(self):
        assert inventory.parse_stock("0") == 0

    def test_integer_with_thai_suffix(self):
        assert inventory.parse_stock("5 ชิ้น") == 5

    def test_integer_with_plus_suffix(self):
        assert inventory.parse_stock("100+") == 100

    def test_large_number(self):
        assert inventory.parse_stock("9999") == 9999

    def test_none_returns_fallback(self):
        assert inventory.parse_stock(None) == inventory._FALLBACK_STOCK

    def test_empty_string_returns_fallback(self):
        assert inventory.parse_stock("") == inventory._FALLBACK_STOCK

    def test_whitespace_only_returns_fallback(self):
        assert inventory.parse_stock("   ") == inventory._FALLBACK_STOCK

    def test_non_numeric_no_oos_returns_fallback(self):
        """Non-numeric text that is NOT an OOS phrase should assume in-stock."""
        assert inventory.parse_stock("In stock") == inventory._FALLBACK_STOCK

    def test_oos_english_out_of_stock(self):
        assert inventory.parse_stock("out of stock") == 0

    def test_oos_english_sold_out(self):
        assert inventory.parse_stock("sold out") == 0

    def test_oos_english_no_stock(self):
        assert inventory.parse_stock("no stock") == 0

    def test_oos_english_unavailable(self):
        assert inventory.parse_stock("unavailable") == 0

    def test_oos_thai(self):
        assert inventory.parse_stock("หมด") == 0

    def test_oos_thai_full(self):
        assert inventory.parse_stock("สินค้าหมด") == 0

    def test_oos_chinese(self):
        assert inventory.parse_stock("缺货") == 0

    def test_oos_japanese(self):
        assert inventory.parse_stock("売り切れ") == 0

    def test_oos_korean(self):
        assert inventory.parse_stock("품절") == 0

    def test_oos_vietnamese(self):
        assert inventory.parse_stock("hết hàng") == 0

    def test_oos_indonesian(self):
        assert inventory.parse_stock("habis") == 0

    def test_oos_case_insensitive(self):
        assert inventory.parse_stock("OUT OF STOCK") == 0
        assert inventory.parse_stock("Sold Out") == 0

    def test_negative_sign_ignored_by_regex(self):
        """regex \\d+ finds '5' in '-5' (no minus), so result is 5."""
        assert inventory.parse_stock("-5") == 5

    def test_number_inside_text(self):
        assert inventory.parse_stock("about 12 units") == 12

    def test_numeric_value_passed_as_int(self):
        assert inventory.parse_stock(42) == 42

    def test_numeric_value_passed_as_float(self):
        assert inventory.parse_stock(7.9) == 7


# ---------------------------------------------------------------------------
# is_in_stock
# ---------------------------------------------------------------------------

class TestIsInStock:
    """Tests for is_in_stock()."""

    def test_positive_stock_is_in_stock(self):
        assert inventory.is_in_stock("10") is True

    def test_zero_stock_is_not_in_stock(self):
        assert inventory.is_in_stock("0") is False

    def test_oos_phrase_is_not_in_stock(self):
        assert inventory.is_in_stock("sold out") is False

    def test_none_assumed_in_stock(self):
        """None falls back to _FALLBACK_STOCK (99), which is > 0."""
        assert inventory.is_in_stock(None) is True

    def test_custom_low_threshold(self):
        """Stock must be strictly above the threshold."""
        assert inventory.is_in_stock("5", low_threshold=5) is False
        assert inventory.is_in_stock("6", low_threshold=5) is True

    def test_threshold_zero_default(self):
        assert inventory.is_in_stock("1", low_threshold=0) is True
        assert inventory.is_in_stock("0", low_threshold=0) is False


# ---------------------------------------------------------------------------
# is_assumed
# ---------------------------------------------------------------------------

class TestIsAssumed:
    """Tests for is_assumed() — detecting fallback/assumed stock values."""

    def test_none_is_assumed(self):
        assert inventory.is_assumed(None) is True

    def test_empty_string_is_assumed(self):
        assert inventory.is_assumed("") is True

    def test_whitespace_is_assumed(self):
        assert inventory.is_assumed("   ") is True

    def test_non_numeric_non_oos_is_assumed(self):
        assert inventory.is_assumed("In stock") is True

    def test_numeric_is_not_assumed(self):
        assert inventory.is_assumed("5") is False

    def test_oos_phrase_is_not_assumed(self):
        """OOS phrases are explicit — the seller said 'out of stock'."""
        assert inventory.is_assumed("sold out") is False

    def test_number_with_suffix_is_not_assumed(self):
        assert inventory.is_assumed("10 ชิ้น") is False


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------

class TestAudit:
    """Tests for audit() — pre-flight stock summary."""

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = inventory.audit(df)
        assert result["total"] == 0
        assert result["ok"] == 0
        assert result["low"] == 0
        assert result["out"] == 0
        assert result["assumed"] == 0

    def test_no_stock_column(self):
        df = pd.DataFrame({"sku": ["A", "B"]})
        result = inventory.audit(df)
        assert result["total"] == 2
        assert result["ok"] == 2
        assert result["out"] == 0
        assert result["low"] == 0

    def test_all_in_stock(self):
        df = pd.DataFrame({"sku": ["A", "B", "C"], "stock": ["100", "50", "20"]})
        result = inventory.audit(df)
        assert result["total"] == 3
        assert result["ok"] == 3
        assert result["out"] == 0
        assert result["low"] == 0

    def test_out_of_stock_detected(self):
        df = pd.DataFrame({"sku": ["A", "B"], "stock": ["0", "sold out"]})
        result = inventory.audit(df)
        assert result["out"] == 2
        assert result["out_skus"] == ["A", "B"]

    def test_low_stock_detected(self):
        df = pd.DataFrame({"sku": ["A", "B"], "stock": ["3", "5"]})
        result = inventory.audit(df, low_threshold=5)
        assert result["low"] == 2
        assert result["low_skus"] == ["A", "B"]

    def test_mixed_stock_states(self):
        df = pd.DataFrame({
            "sku": ["OK", "LOW", "OUT", "ASSUMED"],
            "stock": ["100", "3", "0", ""],
        })
        result = inventory.audit(df, low_threshold=5)
        assert result["total"] == 4
        assert result["ok"] == 2  # "100" and "" (assumed = 99 > 5)
        assert result["low"] == 1  # "3"
        assert result["out"] == 1  # "0"
        assert result["assumed"] == 1  # ""

    def test_custom_low_threshold(self):
        df = pd.DataFrame({"sku": ["A"], "stock": ["10"]})
        result_default = inventory.audit(df, low_threshold=5)
        result_high = inventory.audit(df, low_threshold=15)
        assert result_default["ok"] == 1
        assert result_default["low"] == 0
        assert result_high["ok"] == 0
        assert result_high["low"] == 1

    def test_assumed_count(self):
        df = pd.DataFrame({"sku": ["A", "B"], "stock": [None, "available"]})
        result = inventory.audit(df)
        assert result["assumed"] == 2


# ---------------------------------------------------------------------------
# filter_in_stock
# ---------------------------------------------------------------------------

class TestFilterInStock:
    """Tests for filter_in_stock() — dropping OOS rows."""

    def test_empty_df_passthrough(self):
        df = pd.DataFrame()
        result = inventory.filter_in_stock(df)
        assert result.empty

    def test_no_stock_column_passthrough(self):
        df = pd.DataFrame({"sku": ["A"]})
        result = inventory.filter_in_stock(df)
        assert len(result) == 1

    def test_drops_zero_stock(self):
        df = pd.DataFrame({"sku": ["A", "B"], "stock": ["10", "0"]})
        result = inventory.filter_in_stock(df)
        assert len(result) == 1
        assert result.iloc[0]["sku"] == "A"

    def test_drops_oos_phrase(self):
        df = pd.DataFrame({"sku": ["A", "B"], "stock": ["5", "sold out"]})
        result = inventory.filter_in_stock(df)
        assert len(result) == 1
        assert result.iloc[0]["sku"] == "A"

    def test_keeps_assumed_stock(self):
        """Items with no stock info get fallback (99) and are kept."""
        df = pd.DataFrame({"sku": ["A"], "stock": [""]})
        result = inventory.filter_in_stock(df)
        assert len(result) == 1

    def test_returns_copy(self):
        """filter_in_stock should return a copy, not a view."""
        df = pd.DataFrame({"sku": ["A"], "stock": ["5"]})
        result = inventory.filter_in_stock(df)
        result["sku"] = "modified"
        assert df.iloc[0]["sku"] == "A"


# ---------------------------------------------------------------------------
# normalize_stock_column
# ---------------------------------------------------------------------------

class TestNormalizeStockColumn:
    """Tests for normalize_stock_column() — replacing free-text with ints."""

    def test_empty_df_passthrough(self):
        df = pd.DataFrame()
        result = inventory.normalize_stock_column(df)
        assert result.empty

    def test_no_stock_column_passthrough(self):
        df = pd.DataFrame({"sku": ["A"]})
        result = inventory.normalize_stock_column(df)
        assert "stock" not in result.columns or len(result) == 1

    def test_converts_to_integers(self):
        df = pd.DataFrame({"sku": ["A", "B"], "stock": ["5 ชิ้น", "sold out"]})
        result = inventory.normalize_stock_column(df)
        assert result.iloc[0]["stock"] == 5
        assert result.iloc[1]["stock"] == 0

    def test_returns_copy(self):
        df = pd.DataFrame({"sku": ["A"], "stock": ["10"]})
        result = inventory.normalize_stock_column(df)
        assert result.iloc[0]["stock"] == 10
        # Original should be unchanged
        assert df.iloc[0]["stock"] == "10"

    def test_none_becomes_fallback(self):
        df = pd.DataFrame({"sku": ["A"], "stock": [None]})
        result = inventory.normalize_stock_column(df)
        assert result.iloc[0]["stock"] == inventory._FALLBACK_STOCK


# ---------------------------------------------------------------------------
# decrement
# ---------------------------------------------------------------------------

class TestDecrement:
    """Tests for decrement() — manual stock reduction."""

    def test_simple_number(self):
        assert inventory.decrement("10", 1) == "9"

    def test_decrement_by_more(self):
        assert inventory.decrement("10", 3) == "7"

    def test_clamps_to_zero(self):
        assert inventory.decrement("2", 5) == "0"

    def test_preserves_suffix(self):
        result = inventory.decrement("10 ชิ้น", 1)
        assert result == "9 ชิ้น"

    def test_none_uses_fallback(self):
        result = inventory.decrement(None, 1)
        expected = str(max(0, inventory._FALLBACK_STOCK - 1))
        assert result == expected

    def test_no_number_returns_as_is(self):
        """If there's no digit in the string, return it unchanged."""
        assert inventory.decrement("available", 1) == "available"

    def test_decrement_zero_treated_as_one(self):
        """n=0 falls through to `int(n or 1) = 1`, so decrements by 1."""
        assert inventory.decrement("5", 0) == "4"

    def test_decrement_from_zero(self):
        assert inventory.decrement("0", 1) == "0"
