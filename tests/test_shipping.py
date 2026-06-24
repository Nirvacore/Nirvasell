"""Tests for shipping_calc.py — Thai carrier shipping costs, COD, and comparisons."""
from __future__ import annotations

import pytest

import shipping_calc


# ---------------------------------------------------------------------------
# CARRIERS data integrity
# ---------------------------------------------------------------------------

class TestCarriersData:
    """Verify the CARRIERS constant is well-formed."""

    def test_seven_carriers_defined(self):
        assert len(shipping_calc.CARRIERS) == 7

    EXPECTED_CARRIERS = ["kerry", "flash", "jt", "thaipost_ems", "thaipost_reg", "best", "ninja"]

    @pytest.mark.parametrize("key", EXPECTED_CARRIERS)
    def test_carrier_exists(self, key):
        assert key in shipping_calc.CARRIERS

    @pytest.mark.parametrize("key", EXPECTED_CARRIERS)
    def test_carrier_has_required_fields(self, key):
        info = shipping_calc.CARRIERS[key]
        assert "name" in info
        assert "rates" in info
        assert "cod_fee" in info
        assert "cod_pct" in info
        assert "est_days" in info

    @pytest.mark.parametrize("key", EXPECTED_CARRIERS)
    def test_rates_are_sorted_by_weight(self, key):
        rates = shipping_calc.CARRIERS[key]["rates"]
        weights = [r[0] for r in rates]
        assert weights == sorted(weights), f"{key} rates not sorted by weight"

    @pytest.mark.parametrize("key", EXPECTED_CARRIERS)
    def test_rates_prices_increase_with_weight(self, key):
        rates = shipping_calc.CARRIERS[key]["rates"]
        prices = [r[1] for r in rates]
        for i in range(1, len(prices)):
            assert prices[i] >= prices[i - 1], (
                f"{key}: price at tier {i} ({prices[i]}) < tier {i-1} ({prices[i-1]})"
            )


# ---------------------------------------------------------------------------
# shipping_cost()
# ---------------------------------------------------------------------------

class TestShippingCost:
    """Tests for shipping_cost()."""

    def test_lightest_parcel_kerry(self):
        # 0.3 kg <= 0.5 kg tier -> 40 THB
        assert shipping_calc.shipping_cost("kerry", 0.3) == 40

    def test_exact_tier_boundary(self):
        # Exactly 1 kg -> should hit the 1 kg tier
        assert shipping_calc.shipping_cost("kerry", 1.0) == 50

    def test_between_tiers(self):
        # 1.5 kg: above 1 kg tier, hits 2 kg tier
        assert shipping_calc.shipping_cost("kerry", 1.5) == 60

    def test_max_weight_tier(self):
        # 20 kg is the last tier
        assert shipping_calc.shipping_cost("kerry", 20.0) == 210

    def test_over_max_weight_returns_last_tier(self):
        # 25 kg exceeds all tiers, should return last tier price
        assert shipping_calc.shipping_cost("kerry", 25.0) == 210

    def test_flash_cheapest_at_half_kg(self):
        # Flash 0.5 kg = 30 THB
        assert shipping_calc.shipping_cost("flash", 0.5) == 30

    def test_jt_cheapest_at_half_kg(self):
        assert shipping_calc.shipping_cost("jt", 0.5) == 29

    def test_thaipost_reg_cheapest_overall(self):
        # Thailand Post registered at 0.5 kg = 25 THB (cheapest carrier)
        assert shipping_calc.shipping_cost("thaipost_reg", 0.5) == 25

    def test_unknown_carrier_returns_zero(self):
        assert shipping_calc.shipping_cost("nonexistent", 1.0) == 0

    def test_zero_weight(self):
        # 0 kg should hit the first tier
        cost = shipping_calc.shipping_cost("kerry", 0)
        assert cost == 40  # first tier

    @pytest.mark.parametrize("carrier", shipping_calc.CARRIERS.keys())
    def test_all_carriers_return_positive_cost(self, carrier):
        cost = shipping_calc.shipping_cost(carrier, 1.0)
        assert cost > 0


# ---------------------------------------------------------------------------
# cod_fee()
# ---------------------------------------------------------------------------

class TestCodFee:
    """Tests for cod_fee()."""

    def test_kerry_cod_flat_fee_wins_for_small_order(self):
        # Kerry: flat=15, pct=3%. For 300 THB order: pct = 9, flat=15. max(15,9)=15
        assert shipping_calc.cod_fee("kerry", 300) == 15

    def test_kerry_cod_pct_wins_for_large_order(self):
        # Kerry: flat=15, pct=3%. For 1000 THB: pct = 30. max(15,30)=30
        assert shipping_calc.cod_fee("kerry", 1000) == 30

    def test_flash_cod(self):
        # Flash: flat=10, pct=2.5%. For 500: pct=12.5. max(10,12.5)=12.5
        assert shipping_calc.cod_fee("flash", 500) == pytest.approx(12.5)

    def test_thaipost_no_cod(self):
        # Thailand Post EMS: cod_fee=0, cod_pct=0
        assert shipping_calc.cod_fee("thaipost_ems", 1000) == 0

    def test_thaipost_reg_no_cod(self):
        assert shipping_calc.cod_fee("thaipost_reg", 1000) == 0

    def test_unknown_carrier_returns_zero(self):
        assert shipping_calc.cod_fee("nonexistent", 500) == 0

    def test_zero_order_amount(self):
        # flat = 15, pct = 0. max(15, 0) = 15
        assert shipping_calc.cod_fee("kerry", 0) == 15

    @pytest.mark.parametrize("carrier", shipping_calc.CARRIERS.keys())
    def test_cod_fee_never_negative(self, carrier):
        assert shipping_calc.cod_fee(carrier, 500) >= 0


# ---------------------------------------------------------------------------
# compare_all()
# ---------------------------------------------------------------------------

class TestCompareAll:
    """Tests for compare_all()."""

    def test_returns_all_carriers(self):
        results = shipping_calc.compare_all(1.0)
        assert len(results) == len(shipping_calc.CARRIERS)

    def test_sorted_by_total_cost(self):
        results = shipping_calc.compare_all(2.0)
        totals = [r["total"] for r in results]
        assert totals == sorted(totals)

    def test_no_cod_means_zero_cod_fee(self):
        results = shipping_calc.compare_all(1.0, order_amount=500, is_cod=False)
        for r in results:
            assert r["cod_fee"] == 0

    def test_with_cod_adds_fee(self):
        results = shipping_calc.compare_all(1.0, order_amount=1000, is_cod=True)
        # At least one carrier should have a non-zero COD fee
        has_cod = any(r["cod_fee"] > 0 for r in results)
        assert has_cod

    def test_result_keys(self):
        results = shipping_calc.compare_all(1.0)
        expected_keys = {"carrier", "name", "icon", "shipping", "cod_fee", "total", "est_days"}
        for r in results:
            assert set(r.keys()) == expected_keys

    def test_total_equals_shipping_plus_cod(self):
        results = shipping_calc.compare_all(2.0, order_amount=500, is_cod=True)
        for r in results:
            assert r["total"] == pytest.approx(r["shipping"] + r["cod_fee"])

    def test_heavy_parcel_ordering(self):
        """For a 10 kg parcel, verify cheapest-first ordering holds."""
        results = shipping_calc.compare_all(10.0)
        for i in range(1, len(results)):
            assert results[i]["total"] >= results[i - 1]["total"]


# ---------------------------------------------------------------------------
# cheapest()
# ---------------------------------------------------------------------------

class TestCheapest:
    """Tests for cheapest()."""

    def test_returns_single_dict(self):
        result = shipping_calc.cheapest(1.0)
        assert isinstance(result, dict)
        assert "carrier" in result

    def test_cheapest_matches_first_of_compare_all(self):
        c = shipping_calc.cheapest(2.0, order_amount=500, is_cod=True)
        all_sorted = shipping_calc.compare_all(2.0, order_amount=500, is_cod=True)
        assert c["carrier"] == all_sorted[0]["carrier"]
        assert c["total"] == all_sorted[0]["total"]

    def test_cheapest_for_light_parcel(self):
        """Thailand Post Registered should be cheapest for very light parcels."""
        c = shipping_calc.cheapest(0.3)
        assert c["carrier"] == "thaipost_reg"
        assert c["total"] == 25


# ---------------------------------------------------------------------------
# margin_after_shipping()
# ---------------------------------------------------------------------------

class TestMarginAfterShipping:
    """Tests for margin_after_shipping()."""

    def test_basic_margin(self):
        result = shipping_calc.margin_after_shipping(
            sell_price=500, cost_price=200, weight_kg=1.0, carrier="kerry"
        )
        ship = shipping_calc.shipping_cost("kerry", 1.0)
        expected_profit = 500 - 200 - ship
        assert result["profit"] == pytest.approx(expected_profit, abs=0.01)

    def test_margin_percentage(self):
        result = shipping_calc.margin_after_shipping(
            sell_price=1000, cost_price=400, weight_kg=2.0, carrier="flash"
        )
        assert result["margin"] == pytest.approx(result["profit"] / 1000 * 100, abs=0.1)

    def test_with_cod(self):
        result_no_cod = shipping_calc.margin_after_shipping(
            sell_price=800, cost_price=300, weight_kg=1.0, carrier="kerry", is_cod=False
        )
        result_cod = shipping_calc.margin_after_shipping(
            sell_price=800, cost_price=300, weight_kg=1.0, carrier="kerry", is_cod=True
        )
        # COD should reduce profit
        assert result_cod["profit"] < result_no_cod["profit"]
        assert result_cod["cod_fee"] > 0
        assert result_no_cod["cod_fee"] == 0

    def test_zero_sell_price(self):
        result = shipping_calc.margin_after_shipping(
            sell_price=0, cost_price=100, weight_kg=1.0, carrier="flash"
        )
        assert result["margin"] == 0
        assert result["profit"] < 0

    def test_result_keys(self):
        result = shipping_calc.margin_after_shipping(
            sell_price=500, cost_price=200, weight_kg=1.0, carrier="kerry"
        )
        expected_keys = {"sell_price", "cost_price", "shipping", "cod_fee",
                         "total_cost", "profit", "margin"}
        assert set(result.keys()) == expected_keys

    def test_total_cost_breakdown(self):
        result = shipping_calc.margin_after_shipping(
            sell_price=500, cost_price=200, weight_kg=1.0, carrier="best", is_cod=True
        )
        expected_total = 200 + result["shipping"] + result["cod_fee"]
        assert result["total_cost"] == pytest.approx(expected_total, abs=0.01)
