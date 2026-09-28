"""Target-price advice from configured platform-fee assumptions.

The calculations in this module are advisory. They do not observe current
market prices and therefore must not be presented as market optimization.
"""
from __future__ import annotations

import math

import fees as fees_mod
from i18n_inline import marketplace_fee_label


CANONICAL_PLATFORMS = tuple(fees_mod.DEFAULT_FEES)
_FEE_FIELDS = (
    "commission_pct",
    "payment_pct",
    "transaction_pct",
    "vat_on_fees",
)


def _is_finite_number(value, *, positive: bool = False) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        finite = math.isfinite(value)
    except (OverflowError, TypeError):
        return False
    if not finite:
        return False
    return value > 0 if positive else value >= 0


def _error(code: str, **details) -> dict:
    return {"error": code, **details}


def _validated_fee_config(platform: str, fees: dict) -> tuple[dict | None, dict | None]:
    if platform not in CANONICAL_PLATFORMS:
        return None, _error("unknown_platform")
    config = fees.get(platform)
    if not isinstance(config, dict):
        return None, _error("missing_fee_config")
    if any(
        field not in config or not _is_finite_number(config[field])
        for field in _FEE_FIELDS
    ):
        return None, _error("invalid_fee_config")
    return config, None


def _fee_rate(config: dict) -> float:
    base = sum(config[field] for field in _FEE_FIELDS[:3]) / 100
    return base * (1 + config["vat_on_fees"] / 100)


def _quote(*, price: float, cost: float, shipping: float,
           platform: str, fees: dict) -> dict:
    try:
        platform_fee = round(fees_mod.platform_fee(price, platform, fees), 2)
    except (OverflowError, TypeError, ValueError):
        return _error("nonfinite_calculation")
    net = round(price - cost - shipping - platform_fee, 2)
    if not math.isfinite(platform_fee) or not math.isfinite(net):
        return _error("nonfinite_calculation")
    margin = net / price * 100
    if not math.isfinite(margin):
        return _error("nonfinite_calculation")
    return {
        "price": price,
        "platform_fee": platform_fee,
        "net": net,
        "actual_margin_pct": round(margin, 1),
    }


def target_price(*, cost: float, target_margin_pct: float = 20,
                 platform: str = "shopee", shipping: float = 0,
                 psychological: bool = True,
                 fees: dict | None = None) -> dict:
    """Return advisory raw and selected target-price economics.

    The selected price is either the raw target rounded upward to cents or a
    psychological price that never falls below that raw target.
    """
    if (
        not _is_finite_number(cost, positive=True)
        or not _is_finite_number(target_margin_pct, positive=True)
        or not _is_finite_number(shipping)
        or not isinstance(psychological, bool)
    ):
        return _error("invalid_input")

    configured_fees = fees_mod.load() if fees is None else fees
    if not isinstance(configured_fees, dict):
        return _error("invalid_fee_config")
    config, error = _validated_fee_config(platform, configured_fees)
    if error:
        return error

    fee_rate = _fee_rate(config)
    target = target_margin_pct / 100
    denominator = 1 - fee_rate - target
    numerator = cost + shipping
    if not math.isfinite(fee_rate):
        return _error("invalid_fee_config")
    if not math.isfinite(numerator):
        return _error("invalid_input")
    if denominator <= 0:
        return _error(
            "margin_too_high",
            max_margin=round(max(0, (1 - fee_rate) * 100), 1),
        )

    raw_candidate = numerator / denominator
    raw_cents = raw_candidate * 100
    if not math.isfinite(raw_candidate) or not math.isfinite(raw_cents):
        return _error("invalid_input")
    raw_price = math.ceil(raw_cents) / 100
    selected_price = _psych_round_up(raw_price) if psychological else raw_price
    raw = _quote(
        price=raw_price,
        cost=cost,
        shipping=shipping,
        platform=platform,
        fees=configured_fees,
    )
    selected = _quote(
        price=selected_price,
        cost=cost,
        shipping=shipping,
        platform=platform,
        fees=configured_fees,
    )
    if raw.get("error"):
        return {**raw, "platform": platform}
    if selected.get("error"):
        return {**selected, "platform": platform}
    return {
        "error": None,
        "kind": "target_price_advice",
        "evidence": "configured_fee_assumption",
        "platform": platform,
        "platform_label": marketplace_fee_label(platform),
        "cost": cost,
        "shipping": shipping,
        "target_margin_pct": target_margin_pct,
        "fee_rate_pct": round(fee_rate * 100, 2),
        "raw": raw,
        "selected": selected,
    }


def optimal_price(**kwargs) -> dict:
    """Compatibility alias for the validated target-price contract."""
    return target_price(**kwargs)


def compare_platforms(cost: float, target_margin_pct: float = 20,
                      shipping: float = 0, psychological: bool = True,
                      fees: dict | None = None) -> list[dict]:
    configured_fees = fees_mod.load() if fees is None else fees
    if not isinstance(configured_fees, dict):
        return []
    results = []
    for platform in CANONICAL_PLATFORMS:
        if platform not in configured_fees:
            continue
        row = target_price(
            cost=cost,
            target_margin_pct=target_margin_pct,
            platform=platform,
            shipping=shipping,
            psychological=psychological,
            fees=configured_fees,
        )
        row.setdefault("platform", platform)
        row.setdefault("platform_label", marketplace_fee_label(platform))
        results.append(row)
    results.sort(
        key=lambda row: (
            row.get("error") is not None,
            row.get("selected", {}).get("price", math.inf),
        )
    )
    return results


def margin_at_price(cost: float, sell: float, platform: str,
                    shipping: float = 0, fees: dict | None = None) -> dict:
    if (
        not _is_finite_number(cost, positive=True)
        or not _is_finite_number(sell, positive=True)
        or not _is_finite_number(shipping)
    ):
        return _error("invalid_input")
    configured_fees = fees_mod.load() if fees is None else fees
    if not isinstance(configured_fees, dict):
        return _error("invalid_fee_config")
    config, error = _validated_fee_config(platform, configured_fees)
    if error:
        return error
    if not math.isfinite(_fee_rate(config)):
        return _error("invalid_fee_config")
    return {
        "error": None,
        **_quote(
            price=sell,
            cost=cost,
            shipping=shipping,
            platform=platform,
            fees=configured_fees,
        ),
    }


def _psych_round_up(price: float) -> int:
    if price <= 20:
        return math.ceil(price)
    if price < 100:
        step = 5
    elif price < 1000:
        step = 10
    elif price < 10000:
        step = 100
    else:
        step = 500
    return math.ceil((price + 1) / step) * step - 1
