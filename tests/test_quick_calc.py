"""Tests for quick_calc.py — margin, break-even, ROI, and discount impact calculators."""
from __future__ import annotations

import pytest

import quick_calc


# ---------------------------------------------------------------------------
# margin_calc()
# ---------------------------------------------------------------------------

class TestMarginCalc:
    """Tests for margin_calc()."""

    def test_basic_profitable_sale(self):
        r = quick_calc.margin_calc(cost=200, sell=500)
        assert r["profit"] == 300
        assert r["margin_pct"] == 60.0
        assert r["profitable"] is True

    def test_with_platform_fee(self):
        r = quick_calc.margin_calc(cost=200, sell=500, platform_fee_pct=10.0)
        # fee = 500 * 10% = 50
        assert r["platform_fee"] == 50.0
        # net_revenue = 500 - 50 = 450; profit = 450 - 200 = 250
        assert r["profit"] == 250.0
        assert r["net_revenue"] == 450.0

    def test_with_shipping_and_packaging(self):
        r = quick_calc.margin_calc(
            cost=200, sell=500,
            shipping_cost=50, packaging_cost=20,
        )
        # total_cost = 200 + 50 + 20 = 270
        assert r["total_cost"] == 270.0
        # profit = 500 - 270 = 230
        assert r["profit"] == 230.0

    def test_unprofitable_sale(self):
        r = quick_calc.margin_calc(cost=400, sell=300)
        assert r["profit"] < 0
        assert r["profitable"] is False

    def test_zero_sell_price(self):
        r = quick_calc.margin_calc(cost=100, sell=0)
        assert r["margin_pct"] == 0
        assert r["profit"] == -100

    def test_zero_cost(self):
        r = quick_calc.margin_calc(cost=0, sell=500)
        assert r["profit"] == 500
        assert r["markup_pct"] == 0  # can't compute markup on zero cost

    def test_markup_percentage(self):
        r = quick_calc.margin_calc(cost=200, sell=500)
        # markup = profit / total_cost * 100 = 300 / 200 * 100 = 150%
        assert r["markup_pct"] == 150.0

    def test_result_keys(self):
        r = quick_calc.margin_calc(cost=100, sell=300)
        expected = {
            "cost", "sell", "platform_fee", "total_cost",
            "net_revenue", "profit", "margin_pct", "markup_pct", "profitable",
        }
        assert set(r.keys()) == expected

    def test_all_costs_combined(self):
        r = quick_calc.margin_calc(
            cost=100, sell=500,
            platform_fee_pct=5.0,
            shipping_cost=30, packaging_cost=10,
        )
        # fee = 25, total_cost = 140, net_revenue = 475, profit = 475 - 140 = 335
        assert r["platform_fee"] == 25.0
        assert r["total_cost"] == 140.0
        assert r["profit"] == 335.0


# ---------------------------------------------------------------------------
# price_from_margin()
# ---------------------------------------------------------------------------

class TestPriceFromMargin:
    """Tests for price_from_margin()."""

    def test_basic_target_margin(self):
        r = quick_calc.price_from_margin(cost=200, target_margin_pct=30)
        assert r["error"] is False
        # sell = 200 / (1 - 0 - 0.30) = 200 / 0.70 ~= 286
        assert r["suggested_price"] == pytest.approx(286, abs=1)

    def test_with_platform_fee(self):
        r = quick_calc.price_from_margin(cost=200, target_margin_pct=20, platform_fee_pct=10)
        assert r["error"] is False
        # sell = 200 / (1 - 0.10 - 0.20) = 200 / 0.70 ~= 286
        assert r["suggested_price"] == pytest.approx(286, abs=1)

    def test_impossible_margin(self):
        """Margin + fee > 100% should return an error."""
        r = quick_calc.price_from_margin(cost=200, target_margin_pct=80, platform_fee_pct=30)
        assert r["error"] is True
        assert "msg" in r

    def test_with_shipping(self):
        r = quick_calc.price_from_margin(
            cost=200, target_margin_pct=20,
            shipping_cost=50,
        )
        assert r["error"] is False
        # total_cost = 250; sell = 250 / (1 - 0.20) = 312.5
        assert r["suggested_price"] == pytest.approx(312, abs=1)

    def test_result_includes_margin_calc_fields(self):
        r = quick_calc.price_from_margin(cost=100, target_margin_pct=30)
        assert r["error"] is False
        assert "profit" in r
        assert "margin_pct" in r


# ---------------------------------------------------------------------------
# break_even()
# ---------------------------------------------------------------------------

class TestBreakEven:
    """Tests for break_even()."""

    def test_basic_break_even(self):
        r = quick_calc.break_even(
            fixed_costs=10000,
            price_per_unit=500,
            variable_cost_per_unit=300,
        )
        assert r["achievable"] is True
        # contribution = 200; units = 10000/200 = 50
        assert r["break_even_units"] == 50
        assert r["break_even_revenue"] == 25000

    def test_unachievable(self):
        """Price below variable cost means break-even is impossible."""
        r = quick_calc.break_even(
            fixed_costs=5000,
            price_per_unit=100,
            variable_cost_per_unit=150,
        )
        assert r["achievable"] is False

    def test_contribution_margin(self):
        r = quick_calc.break_even(
            fixed_costs=1000,
            price_per_unit=100,
            variable_cost_per_unit=60,
        )
        assert r["contribution_margin"] == 40.0
        assert r["contribution_pct"] == 40.0

    def test_price_equals_variable_cost(self):
        """Zero contribution margin means can't break even."""
        r = quick_calc.break_even(
            fixed_costs=1000,
            price_per_unit=100,
            variable_cost_per_unit=100,
        )
        assert r["achievable"] is False


# ---------------------------------------------------------------------------
# roi_calc()
# ---------------------------------------------------------------------------

class TestRoiCalc:
    """Tests for roi_calc()."""

    def test_positive_roi(self):
        r = quick_calc.roi_calc(investment=1000, revenue=1500, period_months=1)
        assert r["profit"] == 500
        assert r["roi_pct"] == 50.0
        assert r["profitable"] is True

    def test_negative_roi(self):
        r = quick_calc.roi_calc(investment=1000, revenue=800)
        assert r["profit"] == -200
        assert r["roi_pct"] == -20.0
        assert r["profitable"] is False

    def test_annualized_roi(self):
        r = quick_calc.roi_calc(investment=1000, revenue=1100, period_months=2)
        # monthly_roi = 10% / 2 = 5%; annual = 5% * 12 = 60%
        assert r["monthly_roi"] == 5.0
        assert r["annual_roi"] == 60.0

    def test_payback_months(self):
        r = quick_calc.roi_calc(investment=1000, revenue=1500, period_months=3)
        # profit = 500 over 3 months. monthly profit = 500/3 ~ 166.67
        # payback = 1000 / 166.67 ~ 6.0 months
        assert r["payback_months"] == pytest.approx(6.0)

    def test_zero_investment(self):
        r = quick_calc.roi_calc(investment=0, revenue=500)
        assert r["roi_pct"] == 0

    def test_no_profit_no_payback(self):
        r = quick_calc.roi_calc(investment=1000, revenue=800)
        assert r["payback_months"] is None  # 0 from code when not profitable

    def test_result_keys(self):
        r = quick_calc.roi_calc(investment=100, revenue=200)
        expected = {
            "investment", "revenue", "profit", "roi_pct",
            "monthly_roi", "annual_roi", "payback_months", "profitable",
        }
        assert set(r.keys()) == expected


# ---------------------------------------------------------------------------
# discount_impact()
# ---------------------------------------------------------------------------

class TestDiscountImpact:
    """Tests for discount_impact()."""

    def test_basic_discount(self):
        r = quick_calc.discount_impact(
            original_price=500, discount_pct=20,
            cost=200, current_qty=100,
        )
        assert r["discount_price"] == 400
        assert r["profit_per_unit_before"] == 300
        assert r["profit_per_unit_after"] == 200

    def test_discount_reduces_profit_per_unit(self):
        r = quick_calc.discount_impact(
            original_price=1000, discount_pct=10,
            cost=500, current_qty=50,
        )
        assert r["profit_per_unit_after"] < r["profit_per_unit_before"]

    def test_scenarios_count(self):
        r = quick_calc.discount_impact(
            original_price=500, discount_pct=20,
            cost=200, current_qty=100,
        )
        assert len(r["scenarios"]) == 5  # multipliers: 1.0, 1.2, 1.5, 2.0, 3.0

    def test_scenario_1x_is_current_qty(self):
        r = quick_calc.discount_impact(
            original_price=500, discount_pct=10,
            cost=200, current_qty=100,
        )
        # First scenario should be at current qty (multiplier 1.0)
        assert r["scenarios"][0]["qty"] == 100

    def test_units_needed_to_match(self):
        """Calculate how many extra units needed at discount to match original total profit."""
        r = quick_calc.discount_impact(
            original_price=500, discount_pct=20,
            cost=200, current_qty=100,
        )
        # orig_profit = 300 * 100 = 30000
        # disc_profit_per_unit = 200
        # needed_total = 30000 / 200 = 150 units; extra = 150 - 100 = 50
        assert r["units_needed_to_match"] == 50

    def test_zero_discount(self):
        r = quick_calc.discount_impact(
            original_price=500, discount_pct=0,
            cost=200, current_qty=100,
        )
        assert r["discount_price"] == 500
        assert r["profit_per_unit_after"] == r["profit_per_unit_before"]

    def test_discount_below_cost(self):
        """Discount that pushes price below cost => negative profit per unit."""
        r = quick_calc.discount_impact(
            original_price=300, discount_pct=50,
            cost=200, current_qty=50,
        )
        assert r["profit_per_unit_after"] < 0
        assert r["units_needed_to_match"] is None


# ---------------------------------------------------------------------------
# shipping_calc (quick_calc version)
# ---------------------------------------------------------------------------

class TestShippingCalcQuick:
    """Tests for quick_calc.shipping_calc()."""

    def test_returns_list(self):
        results = quick_calc.shipping_calc(1.0)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_sorted_by_cost(self):
        results = quick_calc.shipping_calc(2.0)
        costs = [r["cost"] for r in results]
        assert costs == sorted(costs)

    def test_specific_carriers(self):
        results = quick_calc.shipping_calc(1.0, carriers=["kerry", "flash"])
        assert len(results) == 2
        carriers = {r["carrier"] for r in results}
        assert carriers == {"kerry", "flash"}

    def test_unknown_carrier_skipped(self):
        results = quick_calc.shipping_calc(1.0, carriers=["kerry", "nonexistent"])
        assert len(results) == 1

    def test_kerry_cost_for_1kg(self):
        results = quick_calc.shipping_calc(1.0, carriers=["kerry"])
        # kerry: base=50, per_kg=15. For 1 kg: 50 + max(0, (1-1)*15) = 50
        assert results[0]["cost"] == 50

    def test_kerry_cost_for_3kg(self):
        results = quick_calc.shipping_calc(3.0, carriers=["kerry"])
        # kerry: base=50, per_kg=15. For 3 kg: 50 + (3-1)*15 = 50 + 30 = 80
        assert results[0]["cost"] == 80

    def test_platform_free_shipping_subsidy(self):
        """Platform carriers (shopee_std, lazada_std) have a free subsidy."""
        results = quick_calc.shipping_calc(1.0, carriers=["shopee_std"])
        # shopee_std: base=0, per_kg=0, max_free=40
        # cost = max(0, 1*0 - 40) = 0
        assert results[0]["cost"] == 0
