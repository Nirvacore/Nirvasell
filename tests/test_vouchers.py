"""Tests for vouchers.py — pure-logic functions (no DB).

We test: random_suffix, suggest_code, format_discount, status_for,
and the CSV export functions (export_shopee, export_lazada, export_tiktok).
"""
from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from unittest.mock import patch

import pytest

import vouchers


# ---------------------------------------------------------------------------
# random_suffix()
# ---------------------------------------------------------------------------

class TestRandomSuffix:
    """Tests for random_suffix()."""

    def test_default_length(self):
        s = vouchers.random_suffix()
        assert len(s) == 4

    def test_custom_length(self):
        s = vouchers.random_suffix(8)
        assert len(s) == 8

    def test_uppercase_and_digits_only(self):
        for _ in range(20):
            s = vouchers.random_suffix(10)
            assert s.isalnum()
            assert s == s.upper()

    def test_randomness(self):
        """Two calls should (almost certainly) produce different results."""
        samples = {vouchers.random_suffix() for _ in range(50)}
        # With 36^4 = 1.6M possibilities, 50 samples should be nearly all unique
        assert len(samples) >= 40


# ---------------------------------------------------------------------------
# suggest_code()
# ---------------------------------------------------------------------------

class TestSuggestCode:
    """Tests for suggest_code()."""

    def test_known_template(self):
        code = vouchers.suggest_code("songkran")
        assert code.startswith("SONGKRAN")
        # prefix(8) + suffix(3) = 11 chars
        assert len(code) == 11

    def test_double_11_template(self):
        code = vouchers.suggest_code("double_11")
        assert code.startswith("ELEVEN11")

    def test_unknown_template(self):
        code = vouchers.suggest_code("nonexistent")
        assert code.startswith("PROMO")
        assert len(code) == 9  # "PROMO" + 4 random chars

    def test_welcome_template(self):
        code = vouchers.suggest_code("welcome")
        assert code.startswith("WELCOME")

    @pytest.mark.parametrize("key", vouchers.TEMPLATES.keys())
    def test_all_templates_produce_code(self, key):
        code = vouchers.suggest_code(key)
        assert len(code) >= 5
        assert code == code.upper() or code.isalnum()


# ---------------------------------------------------------------------------
# format_discount()
# ---------------------------------------------------------------------------

class TestFormatDiscount:
    """Tests for format_discount()."""

    def test_percent(self):
        v = {"discount_type": "percent", "discount_value": 20}
        assert vouchers.format_discount(v) == "-20%"

    def test_fixed(self):
        v = {"discount_type": "fixed", "discount_value": 50}
        result = vouchers.format_discount(v)
        assert "-" in result
        assert "50" in result

    def test_shipping(self):
        v = {"discount_type": "shipping", "discount_value": 0}
        result = vouchers.format_discount(v)
        assert result == "ส่งฟรี"

    def test_large_fixed_discount(self):
        v = {"discount_type": "fixed", "discount_value": 1000}
        result = vouchers.format_discount(v)
        assert "1,000" in result

    def test_percent_integer_display(self):
        """Percent values should display as integers."""
        v = {"discount_type": "percent", "discount_value": 15.0}
        assert vouchers.format_discount(v) == "-15%"


# ---------------------------------------------------------------------------
# status_for()
# ---------------------------------------------------------------------------

class TestStatusFor:
    """Tests for status_for()."""

    def test_active_no_dates(self):
        v = {"status": "active", "starts_at": "", "expires_at": ""}
        assert vouchers.status_for(v) == "active"

    def test_paused(self):
        v = {"status": "paused", "starts_at": "", "expires_at": ""}
        assert vouchers.status_for(v) == "paused"

    def test_expired(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        v = {"status": "active", "starts_at": "", "expires_at": yesterday}
        assert vouchers.status_for(v) == "expired"

    def test_scheduled_future(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        v = {"status": "active", "starts_at": tomorrow, "expires_at": ""}
        assert vouchers.status_for(v) == "scheduled"

    def test_active_within_dates(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        next_week = (date.today() + timedelta(days=7)).isoformat()
        v = {"status": "active", "starts_at": yesterday, "expires_at": next_week}
        assert vouchers.status_for(v) == "active"

    def test_paused_overrides_expiry(self):
        """Paused status takes priority even if dates say expired."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        v = {"status": "paused", "starts_at": "", "expires_at": yesterday}
        assert vouchers.status_for(v) == "paused"

    def test_no_status_key_defaults_active(self):
        v = {"starts_at": "", "expires_at": ""}
        # status_for checks v.get("status"), which returns None; not == "paused"
        assert vouchers.status_for(v) == "active"


# ---------------------------------------------------------------------------
# TEMPLATES data integrity
# ---------------------------------------------------------------------------

class TestTemplates:
    """Verify TEMPLATES constant structure."""

    def test_at_least_5_templates(self):
        assert len(vouchers.TEMPLATES) >= 5

    @pytest.mark.parametrize("key", vouchers.TEMPLATES.keys())
    def test_template_has_required_keys(self, key):
        t = vouchers.TEMPLATES[key]
        assert "label" in t
        assert "code_prefix" in t
        assert "suggested" in t
        assert "discount_type" in t["suggested"]
        assert "discount_value" in t["suggested"]

    @pytest.mark.parametrize("key", vouchers.TEMPLATES.keys())
    def test_discount_type_is_valid(self, key):
        dt = vouchers.TEMPLATES[key]["suggested"]["discount_type"]
        assert dt in ("percent", "fixed", "shipping")


# ---------------------------------------------------------------------------
# CSV exporters
# ---------------------------------------------------------------------------

class TestExportShopee:
    """Tests for export_shopee()."""

    def _parse(self, data: bytes) -> list[list[str]]:
        text = data.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        return list(reader)

    def test_header_row(self):
        rows = self._parse(vouchers.export_shopee([]))
        assert rows[0][0] == "Voucher Code"
        assert len(rows) == 1  # header only

    def test_single_voucher(self):
        v = {
            "code": "TEST10",
            "label": "Test",
            "discount_type": "percent",
            "discount_value": 10,
            "min_spend": 100,
            "max_uses": 50,
            "starts_at": "2025-01-01",
            "expires_at": "2025-12-31",
        }
        rows = self._parse(vouchers.export_shopee([v]))
        assert len(rows) == 2
        assert rows[1][0] == "TEST10"
        assert rows[1][2] == "%"

    def test_fixed_discount_type(self):
        v = {
            "code": "FIX50",
            "label": "Fixed 50",
            "discount_type": "fixed",
            "discount_value": 50,
        }
        rows = self._parse(vouchers.export_shopee([v]))
        assert rows[1][2] == "THB"

    def test_shipping_discount_type(self):
        v = {
            "code": "SHIP",
            "label": "Free Ship",
            "discount_type": "shipping",
            "discount_value": 0,
        }
        rows = self._parse(vouchers.export_shopee([v]))
        assert rows[1][2] == "FREE_SHIPPING"

    def test_multiple_vouchers(self):
        vs = [
            {"code": f"V{i}", "label": f"V{i}", "discount_type": "percent",
             "discount_value": i * 5, "min_spend": 0, "max_uses": 0,
             "starts_at": "", "expires_at": ""}
            for i in range(5)
        ]
        rows = self._parse(vouchers.export_shopee(vs))
        assert len(rows) == 6  # 1 header + 5 data


class TestExportLazada:
    """Tests for export_lazada()."""

    def _parse(self, data: bytes) -> list[list[str]]:
        text = data.decode("utf-8-sig")
        return list(csv.reader(io.StringIO(text)))

    def test_header(self):
        rows = self._parse(vouchers.export_lazada([]))
        assert rows[0][0] == "VoucherCode"

    def test_discount_type_mapping(self):
        for dt, expected in [("percent", "PERCENTAGE"), ("fixed", "AMOUNT"), ("shipping", "SHIPPING")]:
            v = {"code": "X", "label": "X", "discount_type": dt, "discount_value": 10}
            rows = self._parse(vouchers.export_lazada([v]))
            assert rows[1][2] == expected

    def test_unlimited_uses_becomes_999999(self):
        v = {"code": "X", "label": "X", "discount_type": "percent",
             "discount_value": 10, "max_uses": 0}
        rows = self._parse(vouchers.export_lazada([v]))
        assert rows[1][5] == "999999"


class TestExportTiktok:
    """Tests for export_tiktok()."""

    def _parse(self, data: bytes) -> list[list[str]]:
        text = data.decode("utf-8-sig")
        return list(csv.reader(io.StringIO(text)))

    def test_header(self):
        rows = self._parse(vouchers.export_tiktok([]))
        assert rows[0][0] == "Code"

    def test_discount_type_mapping(self):
        for dt, expected in [("percent", "percent"), ("fixed", "amount"), ("shipping", "free_shipping")]:
            v = {"code": "X", "label": "X", "discount_type": dt, "discount_value": 10}
            rows = self._parse(vouchers.export_tiktok([v]))
            assert rows[1][2] == expected

    def test_returns_bytes(self):
        result = vouchers.export_tiktok([])
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# PLATFORM_EXPORTERS registry
# ---------------------------------------------------------------------------

class TestPlatformExporters:
    """Verify the PLATFORM_EXPORTERS registry."""

    def test_three_platforms_registered(self):
        assert len(vouchers.PLATFORM_EXPORTERS) == 3

    @pytest.mark.parametrize("platform", ["shopee", "lazada", "tiktok"])
    def test_exporter_is_callable(self, platform):
        fn, prefix = vouchers.PLATFORM_EXPORTERS[platform]
        assert callable(fn)
        assert isinstance(prefix, str)
