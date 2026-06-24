"""Tests for platform_fees.py — Shopee/Lazada/TikTok fee breakdown calculator."""
from __future__ import annotations

import pytest

import platform_fees


# ---------------------------------------------------------------------------
# PLATFORMS data integrity
# ---------------------------------------------------------------------------

class TestPlatformsData:
    """Verify the PLATFORMS constant is well-formed."""

    EXPECTED = ["shopee", "lazada", "tiktok_shop", "facebook", "line"]

    def test_five_platforms(self):
        assert len(platform_fees.PLATFORMS) == 5

    @pytest.mark.parametrize("key", EXPECTED)
    def test_platform_has_fees(self, key):
        p = platform_fees.PLATFORMS[key]
        fees = p["fees"]
        assert "commission" in fees
        assert "payment" in fees
        assert "transaction" in fees
        assert "vat_on_fees" in fees

    @pytest.mark.parametrize("key", EXPECTED)
    def test_platform_has_label(self, key):
        assert "label" in platform_fees.PLATFORMS[key]


# ---------------------------------------------------------------------------
# calculate()
# ---------------------------------------------------------------------------

class TestCalculate:
    """Tests for platform_fees.calculate()."""

    def test_shopee_basic(self):
        r = platform_fees.calculate("shopee", sale_price=1000, cost_price=400)
        assert r["platform"] == "shopee"
        assert r["revenue"] == 1000
        assert r["cogs"] == 400
        # commission = 1000 * 3% = 30
        assert r["commission"] == 30.0
        # payment = 1000 * 2% = 20
        assert r["payment_fee"] == 20.0
        # vat on commission = 30 * 7% = 2.10
        assert r["vat_on_fees"] == pytest.approx(2.10)
        # total_fees = 30 + 20 + 0 + 2.10 = 52.10
        assert r["total_fees"] == pytest.approx(52.10)

    def test_facebook_zero_fees(self):
        r = platform_fees.calculate("facebook", sale_price=500, cost_price=200)
        assert r["total_fees"] == 0
        assert r["gross_profit"] == 300.0
        assert r["margin_pct"] == 60.0

    def test_with_quantity(self):
        r = platform_fees.calculate("shopee", sale_price=500, cost_price=200, qty=3)
        assert r["revenue"] == 1500.0
        assert r["cogs"] == 600.0

    def test_zero_sale_price(self):
        r = platform_fees.calculate("shopee", sale_price=0, cost_price=100)
        assert r["revenue"] == 0
        assert r["total_fees"] == 0
        assert r["margin_pct"] == 0

    def test_unknown_platform_defaults_to_shopee(self):
        r = platform_fees.calculate("nonexistent", sale_price=1000)
        # Should use shopee as fallback
        shopee = platform_fees.calculate("shopee", sale_price=1000)
        assert r["total_fees"] == shopee["total_fees"]

    def test_gross_profit_formula(self):
        r = platform_fees.calculate("lazada", sale_price=800, cost_price=300)
        expected_gp = r["net_revenue"] - r["cogs"]
        assert r["gross_profit"] == pytest.approx(expected_gp)

    def test_fee_pct(self):
        r = platform_fees.calculate("shopee", sale_price=1000)
        expected_fee_pct = r["total_fees"] / 1000 * 100
        assert r["fee_pct"] == pytest.approx(expected_fee_pct, abs=0.1)

    def test_result_keys(self):
        r = platform_fees.calculate("shopee", sale_price=1000)
        expected = {
            "platform", "label", "revenue", "commission", "payment_fee",
            "transaction_fee", "vat_on_fees", "total_fees", "fee_pct",
            "net_revenue", "cogs", "gross_profit", "margin_pct", "notes",
        }
        assert set(r.keys()) == expected

    def test_line_payment_fee_only(self):
        """LINE OA charges only payment gateway fee."""
        r = platform_fees.calculate("line", sale_price=1000)
        assert r["commission"] == 0
        assert r["payment_fee"] == 15.0  # 1.5%
        assert r["total_fees"] == 15.0

    def test_tiktok_low_fees(self):
        """TikTok Shop has promotional low fees."""
        r = platform_fees.calculate("tiktok_shop", sale_price=1000)
        # commission 2% + payment 1% + vat on commission 7%
        commission = 20.0
        payment = 10.0
        vat = 20.0 * 0.07  # 1.40
        expected_total = commission + payment + vat
        assert r["total_fees"] == pytest.approx(expected_total)


# ---------------------------------------------------------------------------
# compare_all()
# ---------------------------------------------------------------------------

class TestCompareAll:
    """Tests for platform_fees.compare_all()."""

    def test_returns_all_platforms(self):
        results = platform_fees.compare_all(sale_price=1000)
        assert len(results) == len(platform_fees.PLATFORMS)

    def test_each_result_is_valid(self):
        results = platform_fees.compare_all(sale_price=500, cost_price=200)
        for r in results:
            assert "platform" in r
            assert r["revenue"] == 500

    def test_facebook_cheapest(self):
        """Facebook should have lowest fees (zero)."""
        results = platform_fees.compare_all(sale_price=1000, cost_price=400)
        lowest_fee = min(results, key=lambda r: r["total_fees"])
        assert lowest_fee["platform"] == "facebook"


# ---------------------------------------------------------------------------
# best_platform()
# ---------------------------------------------------------------------------

class TestBestPlatform:
    """Tests for platform_fees.best_platform()."""

    def test_facebook_best_due_to_zero_fees(self):
        """Facebook has zero fees, so it should yield highest gross profit."""
        result = platform_fees.best_platform(sale_price=1000, cost_price=400)
        assert result["platform"] == "facebook"

    def test_returns_dict(self):
        result = platform_fees.best_platform(sale_price=500)
        assert isinstance(result, dict)
        assert "gross_profit" in result

    def test_best_profit_is_highest(self):
        best = platform_fees.best_platform(sale_price=800, cost_price=300)
        all_results = platform_fees.compare_all(800, 300)
        max_profit = max(r["gross_profit"] for r in all_results)
        assert best["gross_profit"] == pytest.approx(max_profit)
