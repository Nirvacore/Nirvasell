"""Tests for fees.py — platform fee calculations and currency conversion."""
from __future__ import annotations

import pytest
from unittest.mock import patch

import fees


# ---------------------------------------------------------------------------
# Currency conversion
# ---------------------------------------------------------------------------

class TestConvertFromThb:
    """Tests for convert_from_thb()."""

    def test_thb_to_thb_is_identity(self):
        assert fees.convert_from_thb(1000, "THB") == 1000.0

    def test_thb_to_usd_uses_static_rate(self):
        result = fees.convert_from_thb(1000, "USD", prefer_live=False)
        expected = 1000 * 0.0286
        assert result == pytest.approx(expected)

    def test_thb_to_jpy_uses_static_rate(self):
        result = fees.convert_from_thb(100, "JPY", prefer_live=False)
        expected = 100 * 4.25
        assert result == pytest.approx(expected)

    def test_thb_to_eur(self):
        result = fees.convert_from_thb(500, "EUR", prefer_live=False)
        assert result == pytest.approx(500 * 0.0263)

    def test_unknown_currency_returns_thb(self):
        """Unknown currencies fall back to rate=1.0, so output equals input."""
        result = fees.convert_from_thb(200, "XYZ", prefer_live=False)
        assert result == pytest.approx(200.0)

    def test_zero_amount(self):
        assert fees.convert_from_thb(0, "USD", prefer_live=False) == 0.0

    def test_negative_amount(self):
        result = fees.convert_from_thb(-1000, "USD", prefer_live=False)
        assert result == pytest.approx(-1000 * 0.0286)

    def test_live_rate_preferred_when_available(self):
        with patch.object(fees, '_live_rates', return_value={"USD": 0.030}):
            result = fees.convert_from_thb(1000, "USD", prefer_live=True)
        assert result == pytest.approx(30.0)

    def test_live_rate_fallback_when_missing(self):
        """If live rates don't contain the target, fall back to static."""
        with patch.object(fees, '_live_rates', return_value={"EUR": 0.025}):
            result = fees.convert_from_thb(1000, "USD", prefer_live=True)
        # Should use the static rate since USD not in live dict
        assert result == pytest.approx(1000 * 0.0286)

    def test_all_static_rates_are_positive(self):
        for currency, rate in fees.FX_RATES_VS_THB.items():
            assert rate > 0, f"Rate for {currency} should be positive"


# ---------------------------------------------------------------------------
# format_money
# ---------------------------------------------------------------------------

class TestFormatMoney:
    """Tests for format_money()."""

    def test_thb_format(self):
        result = fees.format_money(1500, "THB")
        assert result == "฿1,500"

    def test_usd_format(self):
        result = fees.format_money(3500, "USD")
        # 3500 * 0.0286 = 100.10 (using static rates)
        assert "$" in result

    def test_jpy_format_no_decimals(self):
        result = fees.format_money(100, "JPY")
        # JPY should have no decimal places
        assert "." not in result
        assert "¥" in result

    def test_idr_format_no_decimals(self):
        result = fees.format_money(100, "IDR")
        assert "." not in result

    def test_zero_amount(self):
        result = fees.format_money(0, "THB")
        assert "฿" in result
        assert "0" in result


# ---------------------------------------------------------------------------
# Platform fee calculation
# ---------------------------------------------------------------------------

class TestPlatformFee:
    """Tests for platform_fee()."""

    def test_shopee_fee(self):
        """Shopee: 6.42% commission + 3.21% payment + 7% VAT on fees."""
        sell = 1000.0
        fee = fees.platform_fee(sell, "shopee")
        base_pct = (6.42 + 3.21 + 0.0) / 100
        base = sell * base_pct
        vat = base * 0.07
        expected = base + vat
        assert fee == pytest.approx(expected, rel=1e-6)

    def test_lazada_fee(self):
        sell = 1000.0
        fee = fees.platform_fee(sell, "lazada")
        base_pct = (5.0 + 2.0 + 0.0) / 100
        base = sell * base_pct
        vat = base * 0.07
        expected = base + vat
        assert fee == pytest.approx(expected, rel=1e-6)

    def test_tiktok_fee(self):
        sell = 1000.0
        fee = fees.platform_fee(sell, "tiktok")
        base_pct = (5.0 + 2.0 + 0.0) / 100
        base = sell * base_pct
        vat = base * 0.07
        expected = base + vat
        assert fee == pytest.approx(expected, rel=1e-6)

    def test_shopify_no_vat(self):
        """Shopify has no VAT on fees."""
        sell = 1000.0
        fee = fees.platform_fee(sell, "shopify")
        base_pct = (0.0 + 2.9 + 0.3) / 100
        base = sell * base_pct
        # VAT = 0%
        expected = base
        assert fee == pytest.approx(expected, rel=1e-6)

    def test_amazon_us_fee(self):
        sell = 500.0
        fee = fees.platform_fee(sell, "amazon_us")
        expected = 500 * 0.15  # 15% commission, no other fees, no VAT
        assert fee == pytest.approx(expected, rel=1e-6)

    def test_unknown_platform_zero_fee(self):
        """Unknown platform returns zero fee."""
        fee = fees.platform_fee(1000, "nonexistent_platform")
        assert fee == 0.0

    def test_zero_sell_price(self):
        fee = fees.platform_fee(0, "shopee")
        assert fee == 0.0

    def test_custom_fees_dict(self):
        custom = {
            "custom_shop": {
                "commission_pct": 10.0,
                "payment_pct": 2.0,
                "transaction_pct": 0.0,
                "vat_on_fees": 0.0,
            }
        }
        fee = fees.platform_fee(1000, "custom_shop", custom)
        assert fee == pytest.approx(120.0)  # 12% of 1000

    def test_fee_increases_linearly_with_price(self):
        fee_100 = fees.platform_fee(100, "shopee")
        fee_200 = fees.platform_fee(200, "shopee")
        assert fee_200 == pytest.approx(fee_100 * 2, rel=1e-6)

    def test_all_default_platforms_have_positive_or_zero_fees(self):
        loaded = fees.load()
        for platform in loaded:
            fee = fees.platform_fee(1000, platform, loaded)
            assert fee >= 0, f"Fee for {platform} should not be negative"


# ---------------------------------------------------------------------------
# Net profit
# ---------------------------------------------------------------------------

class TestNetProfit:
    """Tests for net_profit()."""

    def test_basic_profit(self):
        result = fees.net_profit(cost=300, sell=1000, platform="shopee")
        assert result["sell"] == 1000
        assert result["cost"] == 300
        assert result["platform_fee"] > 0
        net = 1000 - 300 - result["platform_fee"]
        assert result["net"] == pytest.approx(net)

    def test_margin_percentage(self):
        result = fees.net_profit(cost=0, sell=1000, platform="shopee")
        # net = sell - 0 - fee; margin = net / sell * 100
        expected_margin = result["net"] / 1000 * 100
        assert result["margin_pct"] == pytest.approx(expected_margin)

    def test_zero_sell_margin(self):
        result = fees.net_profit(cost=100, sell=0, platform="shopee")
        assert result["margin_pct"] == 0

    def test_negative_profit_possible(self):
        """If cost exceeds sell, net should be negative."""
        result = fees.net_profit(cost=900, sell=100, platform="amazon_us")
        assert result["net"] < 0

    def test_extra_cost_reduces_net(self):
        result_no_extra = fees.net_profit(cost=200, sell=1000, platform="shopee")
        result_with_extra = fees.net_profit(cost=200, sell=1000, platform="shopee", extra_cost=50)
        assert result_with_extra["net"] == pytest.approx(result_no_extra["net"] - 50)
        assert result_with_extra["extra_cost"] == 50

    def test_result_keys(self):
        result = fees.net_profit(cost=100, sell=500, platform="lazada")
        assert set(result.keys()) == {"sell", "cost", "platform_fee", "extra_cost", "net", "margin_pct"}


# ---------------------------------------------------------------------------
# Best platform
# ---------------------------------------------------------------------------

class TestBestPlatform:
    """Tests for best_platform()."""

    def test_returns_valid_platform(self):
        best = fees.best_platform(cost=200, sell=1000)
        loaded = fees.load()
        assert best in loaded

    def test_lowest_fee_platform_wins(self):
        """Facebook-like platform with zero fees should win when available."""
        custom = {
            "zero_fee": {
                "commission_pct": 0.0,
                "payment_pct": 0.0,
                "transaction_pct": 0.0,
                "vat_on_fees": 0.0,
            },
            "high_fee": {
                "commission_pct": 50.0,
                "payment_pct": 10.0,
                "transaction_pct": 0.0,
                "vat_on_fees": 0.0,
            },
        }
        best = fees.best_platform(cost=200, sell=1000, fees=custom)
        assert best == "zero_fee"

    def test_best_platform_consistent_with_net_profit(self):
        """The best platform should have the highest net profit."""
        loaded = fees.load()
        best = fees.best_platform(cost=300, sell=1000, fees=loaded)
        best_net = fees.net_profit(300, 1000, best, loaded)["net"]
        for platform in loaded:
            this_net = fees.net_profit(300, 1000, platform, loaded)["net"]
            assert best_net >= this_net - 1e-6, (
                f"Expected {best} (net={best_net}) >= {platform} (net={this_net})"
            )


# ---------------------------------------------------------------------------
# load / DEFAULT_FEES
# ---------------------------------------------------------------------------

class TestLoadFees:
    """Tests for load() and the DEFAULT_FEES structure."""

    def test_load_returns_dict(self):
        loaded = fees.load()
        assert isinstance(loaded, dict)

    def test_load_contains_all_default_platforms(self):
        loaded = fees.load()
        for key in fees.DEFAULT_FEES:
            assert key in loaded

    def test_default_fees_have_required_keys(self):
        for platform, f in fees.DEFAULT_FEES.items():
            assert "commission_pct" in f, f"{platform} missing commission_pct"
            assert "payment_pct" in f, f"{platform} missing payment_pct"
            assert "vat_on_fees" in f, f"{platform} missing vat_on_fees"

    def test_load_returns_copies(self):
        """Mutating loaded dict should not affect DEFAULT_FEES."""
        loaded = fees.load()
        loaded["shopee"]["commission_pct"] = 999
        assert fees.DEFAULT_FEES["shopee"]["commission_pct"] != 999

    def test_ten_platforms_minimum(self):
        """We expect at least 10 default platforms."""
        assert len(fees.DEFAULT_FEES) >= 10
