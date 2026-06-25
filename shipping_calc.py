"""Thai Shipping Cost Calculator — compare carriers instantly.

Major Thai carriers: Kerry Express, Flash Express, J&T Express,
Thailand Post (EMS/registered), Best Express, NinjaVan.

Rates are approximate 2024-2025 standard rates. Real rates vary by
seller tier, volume discounts, and promotional periods.

Weight tiers in kg, prices in THB."""
from __future__ import annotations

from i18n_inline import carrier_name


CARRIERS: dict[str, dict] = {
    "kerry": {
        "icon": "🟠",
        "rates": [
            (0.5, 40), (1, 50), (2, 60), (3, 70), (5, 90),
            (10, 130), (15, 170), (20, 210),
        ],
        "cod_fee": 15,
        "cod_pct": 3.0,
        "est_days": "1-2",
    },
    "flash": {
        "icon": "🟡",
        "rates": [
            (0.5, 30), (1, 35), (2, 45), (3, 55), (5, 75),
            (10, 110), (15, 145), (20, 180),
        ],
        "cod_fee": 10,
        "cod_pct": 2.5,
        "est_days": "1-3",
    },
    "jt": {
        "icon": "🔴",
        "rates": [
            (0.5, 29), (1, 35), (2, 45), (3, 55), (5, 72),
            (10, 105), (15, 140), (20, 175),
        ],
        "cod_fee": 10,
        "cod_pct": 2.5,
        "est_days": "1-3",
    },
    "thaipost_ems": {
        "icon": "🔵",
        "rates": [
            (0.5, 37), (1, 42), (2, 52), (3, 62), (5, 82),
            (10, 120), (15, 160), (20, 200),
        ],
        "cod_fee": 0,
        "cod_pct": 0,
        "est_days": "1-2",
    },
    "thaipost_reg": {
        "icon": "🔵",
        "rates": [
            (0.5, 25), (1, 30), (2, 35), (3, 40), (5, 55),
            (10, 80), (15, 110), (20, 140),
        ],
        "cod_fee": 0,
        "cod_pct": 0,
        "est_days": "3-5",
    },
    "best": {
        "icon": "🟢",
        "rates": [
            (0.5, 28), (1, 33), (2, 42), (3, 52), (5, 70),
            (10, 100), (15, 135), (20, 170),
        ],
        "cod_fee": 10,
        "cod_pct": 2.0,
        "est_days": "2-4",
    },
    "ninja": {
        "icon": "🟣",
        "rates": [
            (0.5, 35), (1, 40), (2, 50), (3, 60), (5, 80),
            (10, 115), (15, 150), (20, 185),
        ],
        "cod_fee": 15,
        "cod_pct": 3.0,
        "est_days": "2-3",
    },
}


def shipping_cost(carrier: str, weight_kg: float) -> float:
    """Calculate shipping cost for a given carrier and weight."""
    info = CARRIERS.get(carrier)
    if not info:
        return 0
    for max_w, price in info["rates"]:
        if weight_kg <= max_w:
            return price
    return info["rates"][-1][1]


def cod_fee(carrier: str, order_amount: float) -> float:
    """Calculate COD handling fee."""
    info = CARRIERS.get(carrier)
    if not info:
        return 0
    flat = info.get("cod_fee", 0)
    pct = info.get("cod_pct", 0) / 100 * order_amount
    return max(flat, pct)


def compare_all(weight_kg: float, order_amount: float = 0,
                is_cod: bool = False) -> list[dict]:
    """Compare shipping cost across all carriers.
    Returns sorted by total cost (cheapest first)."""
    results = []
    for key, info in CARRIERS.items():
        ship = shipping_cost(key, weight_kg)
        cod = cod_fee(key, order_amount) if is_cod else 0
        total = ship + cod
        results.append({
            "carrier": key,
            "name": carrier_name(key),
            "icon": info["icon"],
            "shipping": ship,
            "cod_fee": cod,
            "total": total,
            "est_days": info["est_days"],
        })
    return sorted(results, key=lambda x: x["total"])


def cheapest(weight_kg: float, order_amount: float = 0,
             is_cod: bool = False) -> dict:
    """Return the cheapest carrier option."""
    all_opts = compare_all(weight_kg, order_amount, is_cod)
    return all_opts[0] if all_opts else {}


def margin_after_shipping(sell_price: float, cost_price: float,
                          weight_kg: float, carrier: str,
                          is_cod: bool = False) -> dict:
    """Calculate actual margin after shipping costs."""
    ship = shipping_cost(carrier, weight_kg)
    cod = cod_fee(carrier, sell_price) if is_cod else 0
    total_cost = cost_price + ship + cod
    profit = sell_price - total_cost
    margin = (profit / sell_price * 100) if sell_price else 0
    return {
        "sell_price": sell_price,
        "cost_price": cost_price,
        "shipping": ship,
        "cod_fee": cod,
        "total_cost": round(total_cost, 2),
        "profit": round(profit, 2),
        "margin": round(margin, 1),
    }
