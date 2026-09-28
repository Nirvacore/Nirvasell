"""Contract tests for bounded, fail-closed target-price advice."""

from __future__ import annotations

import math
import sys
import types

if "i18n_inline" not in sys.modules:
    inline = types.ModuleType("i18n_inline")
    inline.currency_label = lambda value: value
    inline.marketplace_fee_label = lambda value: value
    sys.modules["i18n_inline"] = inline

import price_optimizer


FEES = {
    "shopee": {
        "commission_pct": 10.0,
        "payment_pct": 0.0,
        "transaction_pct": 0.0,
        "vat_on_fees": 0.0,
    },
    "lazada": {
        "commission_pct": 5.0,
        "payment_pct": 2.0,
        "transaction_pct": 0.0,
        "vat_on_fees": 7.0,
    },
}


def test_target_price_recomputes_raw_and_selected_economics() -> None:
    result = price_optimizer.target_price(
        cost=71.0,
        target_margin_pct=20.0,
        platform="shopee",
        shipping=0.0,
        psychological=True,
        fees=FEES,
    )

    assert result["error"] is None
    assert result["kind"] == "target_price_advice"
    assert result["evidence"] == "configured_fee_assumption"
    assert result["raw"]["price"] == 101.43
    assert result["selected"]["price"] == 109
    assert result["selected"]["price"] >= result["raw"]["price"]
    assert result["raw"]["actual_margin_pct"] >= 20.0
    assert result["selected"]["actual_margin_pct"] >= 20.0

    for quote in (result["raw"], result["selected"]):
        assert quote["platform_fee"] == round(quote["price"] * 0.10, 2)
        assert quote["net"] == round(
            quote["price"] - 71.0 - quote["platform_fee"], 2
        )
        assert quote["actual_margin_pct"] == round(
            quote["net"] / quote["price"] * 100, 1
        )

    raw_selected = price_optimizer.target_price(
        cost=71.0,
        target_margin_pct=20.0,
        platform="shopee",
        psychological=False,
        fees=FEES,
    )
    assert raw_selected["selected"] == raw_selected["raw"]


def test_contract_rejects_unknown_platform_and_invalid_numbers() -> None:
    unknown_fees = {**FEES, "unknown": FEES["shopee"]}
    assert price_optimizer.target_price(
        cost=100, target_margin_pct=20, platform="unknown", fees=unknown_fees
    )["error"] == "unknown_platform"
    assert price_optimizer.margin_at_price(
        100, 200, "unknown", fees=unknown_fees
    )["error"] == "unknown_platform"

    invalid_cases = (
        {"cost": 0, "target_margin_pct": 20, "shipping": 0},
        {"cost": -1, "target_margin_pct": 20, "shipping": 0},
        {"cost": math.nan, "target_margin_pct": 20, "shipping": 0},
        {"cost": 10**400, "target_margin_pct": 20, "shipping": 0},
        {"cost": 100, "target_margin_pct": 0, "shipping": 0},
        {"cost": 100, "target_margin_pct": math.inf, "shipping": 0},
        {"cost": 100, "target_margin_pct": 20, "shipping": -1},
        {"cost": 1e308, "target_margin_pct": 20, "shipping": 1e308},
    )
    for values in invalid_cases:
        result = price_optimizer.target_price(
            platform="shopee", fees=FEES, **values
        )
        assert result["error"] == "invalid_input", values

    for sell in (0, -1, math.nan, math.inf):
        assert price_optimizer.margin_at_price(
            100, sell, "shopee", fees=FEES
        )["error"] == "invalid_input"


def test_fee_evidence_and_impossible_targets_fail_closed() -> None:
    missing = {"lazada": FEES["lazada"]}
    assert price_optimizer.target_price(
        cost=100, target_margin_pct=20, platform="shopee", fees=missing
    )["error"] == "missing_fee_config"

    for bad_value in (-1.0, math.nan, math.inf, 10**400):
        invalid_fees = {
            "shopee": {**FEES["shopee"], "commission_pct": bad_value}
        }
        assert price_optimizer.target_price(
            cost=100, target_margin_pct=20,
            platform="shopee", fees=invalid_fees,
        )["error"] == "invalid_fee_config"

    overflowing_fees = {
        "shopee": {
            **FEES["shopee"],
            "commission_pct": 1e308,
            "payment_pct": 1e308,
        }
    }
    assert price_optimizer.target_price(
        cost=100, target_margin_pct=20,
        platform="shopee", fees=overflowing_fees,
    )["error"] == "invalid_fee_config"

    impossible = price_optimizer.target_price(
        cost=100,
        target_margin_pct=95,
        platform="shopee",
        fees=FEES,
    )
    assert impossible["error"] == "margin_too_high"
    assert impossible["max_margin"] == 90.0


def test_compare_uses_only_canonical_platforms_and_selected_contract() -> None:
    configured = {**FEES, "unknown": FEES["shopee"]}
    rows = price_optimizer.compare_platforms(
        cost=100,
        target_margin_pct=20,
        psychological=True,
        fees=configured,
    )
    assert [row["platform"] for row in rows] == ["lazada", "shopee"]
    assert all(row["selected"]["price"] >= row["raw"]["price"] for row in rows)
    assert all(row["kind"] == "target_price_advice" for row in rows)


def test_margin_quote_rejects_nonfinite_calculation_outputs() -> None:
    overflowing_fees = {
        "shopee": {
            "commission_pct": 90.0,
            "payment_pct": 0.0,
            "transaction_pct": 0.0,
            "vat_on_fees": 100.0,
        }
    }
    result = price_optimizer.margin_at_price(
        cost=100.0,
        sell=1e308,
        platform="shopee",
        fees=overflowing_fees,
    )
    assert result["error"] == "nonfinite_calculation"


if __name__ == "__main__":
    test_target_price_recomputes_raw_and_selected_economics()
    test_contract_rejects_unknown_platform_and_invalid_numbers()
    test_fee_evidence_and_impossible_targets_fail_closed()
    test_compare_uses_only_canonical_platforms_and_selected_contract()
    test_margin_quote_rejects_nonfinite_calculation_outputs()
    print("price optimizer contract: 5 passed")
