"""Quick Calculator — business calculators for Thai resellers.

Margin calculator, shipping cost estimator, break-even analysis,
ROI calculator, discount impact analyzer."""
from __future__ import annotations


def margin_calc(cost: float, sell: float, platform_fee_pct: float = 0.0,
                shipping_cost: float = 0.0, packaging_cost: float = 0.0) -> dict:
    total_cost = cost + shipping_cost + packaging_cost
    fee = sell * (platform_fee_pct / 100.0)
    net_revenue = sell - fee
    profit = net_revenue - total_cost
    margin_pct = (profit / sell * 100) if sell > 0 else 0
    markup_pct = (profit / total_cost * 100) if total_cost > 0 else 0

    return {
        "cost": cost,
        "sell": sell,
        "platform_fee": round(fee, 2),
        "total_cost": round(total_cost, 2),
        "net_revenue": round(net_revenue, 2),
        "profit": round(profit, 2),
        "margin_pct": round(margin_pct, 1),
        "markup_pct": round(markup_pct, 1),
        "profitable": profit > 0,
    }


def price_from_margin(cost: float, target_margin_pct: float,
                      platform_fee_pct: float = 0.0,
                      shipping_cost: float = 0.0,
                      packaging_cost: float = 0.0) -> dict:
    total_cost = cost + shipping_cost + packaging_cost
    fee_rate = platform_fee_pct / 100.0
    margin_rate = target_margin_pct / 100.0

    if (1 - fee_rate - margin_rate) <= 0:
        return {"error": True, "msg": "Margin + fee > 100%"}

    sell = total_cost / (1 - fee_rate - margin_rate)
    return {
        "error": False,
        "suggested_price": round(sell, 0),
        "profit_per_unit": round(sell * margin_rate, 2),
        **margin_calc(cost, round(sell, 0), platform_fee_pct,
                      shipping_cost, packaging_cost),
    }


def break_even(fixed_costs: float, price_per_unit: float,
               variable_cost_per_unit: float) -> dict:
    contribution = price_per_unit - variable_cost_per_unit
    if contribution <= 0:
        return {
            "achievable": False,
            "msg": "ราคาขายต่ำกว่าต้นทุนผันแปร",
        }

    units = fixed_costs / contribution
    revenue = units * price_per_unit

    return {
        "achievable": True,
        "break_even_units": round(units, 0),
        "break_even_revenue": round(revenue, 0),
        "contribution_margin": round(contribution, 2),
        "contribution_pct": round(contribution / price_per_unit * 100, 1),
    }


def roi_calc(investment: float, revenue: float, period_months: int = 1) -> dict:
    profit = revenue - investment
    roi_pct = (profit / investment * 100) if investment > 0 else 0
    monthly_roi = roi_pct / period_months if period_months > 0 else 0
    annual_roi = monthly_roi * 12
    payback_months = (investment / (profit / period_months)
                      if profit > 0 and period_months > 0 else 0)

    return {
        "investment": investment,
        "revenue": revenue,
        "profit": round(profit, 2),
        "roi_pct": round(roi_pct, 1),
        "monthly_roi": round(monthly_roi, 1),
        "annual_roi": round(annual_roi, 1),
        "payback_months": round(payback_months, 1) if payback_months > 0 else None,
        "profitable": profit > 0,
    }


def discount_impact(original_price: float, discount_pct: float,
                    cost: float, current_qty: int) -> dict:
    disc_price = original_price * (1 - discount_pct / 100)
    orig_profit = original_price - cost
    disc_profit = disc_price - cost

    if disc_profit <= 0:
        needed_increase = None
    else:
        needed_increase = round(
            (orig_profit * current_qty / disc_profit) - current_qty, 0
        )

    orig_total = orig_profit * current_qty

    scenarios = []
    for mult in [1.0, 1.2, 1.5, 2.0, 3.0]:
        new_qty = int(current_qty * mult)
        new_total = disc_profit * new_qty
        scenarios.append({
            "qty": new_qty,
            "total_profit": round(new_total, 0),
            "vs_original": round(new_total - orig_total, 0),
            "better": new_total > orig_total,
        })

    return {
        "original_price": original_price,
        "discount_price": round(disc_price, 0),
        "discount_pct": discount_pct,
        "profit_per_unit_before": round(orig_profit, 2),
        "profit_per_unit_after": round(disc_profit, 2),
        "profit_change_pct": round(
            (disc_profit - orig_profit) / orig_profit * 100, 1
        ) if orig_profit > 0 else 0,
        "units_needed_to_match": int(needed_increase) if needed_increase else None,
        "scenarios": scenarios,
    }


SHIPPING_RATES = {
    "kerry": {"base": 50, "per_kg": 15, "max_free": 0},
    "flash": {"base": 40, "per_kg": 12, "max_free": 0},
    "j&t": {"base": 38, "per_kg": 10, "max_free": 0},
    "thaipost_ems": {"base": 37, "per_kg": 20, "max_free": 0},
    "thaipost_reg": {"base": 25, "per_kg": 15, "max_free": 0},
    "shopee_std": {"base": 0, "per_kg": 0, "max_free": 40},
    "lazada_std": {"base": 0, "per_kg": 0, "max_free": 35},
}


def shipping_calc(weight_kg: float, carriers: list = None) -> list:
    if carriers is None:
        carriers = list(SHIPPING_RATES.keys())

    results = []
    for name in carriers:
        rate = SHIPPING_RATES.get(name)
        if not rate:
            continue
        if rate["max_free"] > 0:
            cost = max(0, (weight_kg * rate["per_kg"]) - rate["max_free"])
        else:
            cost = rate["base"] + max(0, (weight_kg - 1) * rate["per_kg"])
        results.append({
            "carrier": name,
            "cost": round(cost, 0),
            "base": rate["base"],
            "per_kg": rate["per_kg"],
        })

    results.sort(key=lambda x: x["cost"])
    return results
