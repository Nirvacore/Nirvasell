"""AI Price Optimizer — suggest selling prices per platform to hit target margin.

Thai resellers often guess prices. This module does the math:
  cost + markup + platform_fee + shipping + VAT = minimum selling price

Then AI suggests psychological pricing (e.g. ฿999 instead of ฿1,012)."""
from __future__ import annotations

import fees as fees_mod
from i18n_inline import marketplace_fee_label


def optimal_price(*, cost: float, target_margin_pct: float = 20,
                  platform: str = "shopee", shipping: float = 0,
                  fees: dict | None = None) -> dict:
    if fees is None:
        fees = fees_mod.load()

    f = fees.get(platform, {})
    comm = f.get("commission_pct", 0) / 100
    pay = f.get("payment_pct", 0) / 100
    txn = f.get("transaction_pct", 0) / 100
    vat = f.get("vat_on_fees", 0) / 100

    fee_rate = (comm + pay + txn) * (1 + vat)
    target = target_margin_pct / 100

    # sell = (cost + shipping) / (1 - fee_rate - target)
    denom = 1 - fee_rate - target
    if denom <= 0:
        return {"error": "margin_too_high", "max_margin": round((1 - fee_rate) * 100, 1)}

    raw_price = (cost + shipping) / denom
    return {
        "raw_price": round(raw_price, 2),
        "suggested": _psych_round(raw_price),
        "cost": cost,
        "shipping": shipping,
        "platform": platform,
        "fee_rate_pct": round(fee_rate * 100, 2),
        "target_margin_pct": target_margin_pct,
        "actual_margin_pct": round(
            (raw_price - cost - shipping - raw_price * fee_rate) / raw_price * 100, 1
        ),
    }


def compare_platforms(cost: float, target_margin_pct: float = 20,
                      shipping: float = 0) -> list[dict]:
    fees = fees_mod.load()
    results = []
    for plat in fees:
        r = optimal_price(
            cost=cost, target_margin_pct=target_margin_pct,
            platform=plat, shipping=shipping, fees=fees,
        )
        r["platform_label"] = marketplace_fee_label(plat)
        results.append(r)
    results.sort(key=lambda r: r.get("suggested") or r.get("raw_price") or 99999)
    return results


def margin_at_price(cost: float, sell: float, platform: str,
                    shipping: float = 0) -> dict:
    fee = fees_mod.platform_fee(sell, platform)
    net = sell - cost - fee - shipping
    margin = (net / sell * 100) if sell > 0 else 0
    return {
        "sell": sell, "cost": cost, "shipping": shipping,
        "fee": round(fee, 2), "net": round(net, 2),
        "margin_pct": round(margin, 1),
    }


def _psych_round(price: float) -> int:
    if price <= 0:
        return 0
    if price < 100:
        return int(round(price / 5) * 5) - 1 if price > 20 else int(round(price))
    if price < 1000:
        r = int(round(price / 10) * 10)
        return r - 1 if r > 50 else r
    if price < 10000:
        r = int(round(price / 100) * 100)
        return r - 1
    r = int(round(price / 500) * 500)
    return r - 1
