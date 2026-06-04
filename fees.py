"""Platform fee math + multi-currency display.

All prices stored in THB internally. UI converts on the fly using FX_RATES_VS_THB.
Update rates from exchangerate-api.com or similar in production.

Fee defaults are typical Thailand marketplace rates — override per-tier in
`data/fee_overrides.json`. Global marketplaces have separate fee entries.
"""
from __future__ import annotations
import json
from pathlib import Path


# ---- Currencies -----------------------------------------------------------

FX_RATES_VS_THB: dict[str, float] = {
    "THB": 1.0,
    "USD": 0.0286,
    "EUR": 0.0263,
    "GBP": 0.0223,
    "JPY": 4.25,
    "CNY": 0.205,
    "SGD": 0.0386,
    "AUD": 0.0431,
    "MYR": 0.134,
    "IDR": 466.0,
    "VND": 727.0,
    "PHP": 1.66,
    "KRW": 41.5,
    "HKD": 0.222,
    "TWD": 0.918,
    "INR": 2.40,
    "AED": 0.105,
}

CURRENCY_LABELS: dict[str, str] = {
    "THB": "บาท ฿", "USD": "US $", "EUR": "€", "GBP": "£",
    "JPY": "¥", "CNY": "¥ CNY", "SGD": "S$", "AUD": "A$",
    "MYR": "RM", "IDR": "Rp", "VND": "₫", "PHP": "₱",
    "KRW": "₩", "HKD": "HK$", "TWD": "NT$", "INR": "₹", "AED": "د.إ",
}


def _live_rates() -> dict[str, float]:
    """Pull cached live rates if available. Fall back to static."""
    try:
        from live_data import fetch_fx_rates
        data = fetch_fx_rates()
        return data.get("rates") or {}
    except Exception:
        return {}


def convert_from_thb(thb: float, target: str, prefer_live: bool = True) -> float:
    if prefer_live:
        live = _live_rates()
        if target in live:
            return thb * live[target]
    rate = FX_RATES_VS_THB.get(target, 1.0)
    return thb * rate


def format_money(thb: float, currency: str = "THB") -> str:
    val = convert_from_thb(thb, currency)
    sym = CURRENCY_LABELS.get(currency, currency)
    if currency in ("JPY", "IDR", "VND", "KRW", "TWD"):
        return f"{sym} {val:,.0f}"
    if currency == "THB":
        return f"฿{val:,.0f}"
    return f"{sym} {val:,.2f}"


# ---- Platform fees --------------------------------------------------------

# (commission %, payment %, transaction %, VAT on fees %) — sum + VAT = total cut
DEFAULT_FEES: dict[str, dict] = {
    # Thailand marketplaces
    "shopee": {
        "label": "Shopee TH",
        "commission_pct": 6.42, "payment_pct": 3.21, "transaction_pct": 0.0,
        "vat_on_fees": 7.0, "currency": "THB",
    },
    "lazada": {
        "label": "Lazada TH",
        "commission_pct": 5.0, "payment_pct": 2.0, "transaction_pct": 0.0,
        "vat_on_fees": 7.0, "currency": "THB",
    },
    "tiktok": {
        "label": "TikTok Shop TH",
        "commission_pct": 5.0, "payment_pct": 2.0, "transaction_pct": 0.0,
        "vat_on_fees": 7.0, "currency": "THB",
    },
    # Global marketplaces (typical referral / final value fees)
    "shopify": {
        "label": "Shopify (own store)",
        "commission_pct": 0.0, "payment_pct": 2.9, "transaction_pct": 0.3,
        "vat_on_fees": 0.0, "currency": "USD",
    },
    "amazon_us": {
        "label": "Amazon US",
        "commission_pct": 15.0, "payment_pct": 0.0, "transaction_pct": 0.0,
        "vat_on_fees": 0.0, "currency": "USD",
    },
    "ebay_us": {
        "label": "eBay US",
        "commission_pct": 12.55, "payment_pct": 0.30, "transaction_pct": 0.0,
        "vat_on_fees": 0.0, "currency": "USD",
    },
    "etsy": {
        "label": "Etsy",
        "commission_pct": 6.5, "payment_pct": 3.0, "transaction_pct": 0.25,
        "vat_on_fees": 0.0, "currency": "USD",
    },
    "amazon_jp": {
        "label": "Amazon JP",
        "commission_pct": 15.0, "payment_pct": 0.0, "transaction_pct": 0.0,
        "vat_on_fees": 10.0, "currency": "JPY",
    },
    "rakuten": {
        "label": "Rakuten JP",
        "commission_pct": 8.0, "payment_pct": 0.0, "transaction_pct": 0.0,
        "vat_on_fees": 10.0, "currency": "JPY",
    },
    "tokopedia": {
        "label": "Tokopedia ID",
        "commission_pct": 4.5, "payment_pct": 0.5, "transaction_pct": 0.0,
        "vat_on_fees": 11.0, "currency": "IDR",
    },
}

ROOT = Path(__file__).parent
OVERRIDES_PATH = ROOT / "data" / "fee_overrides.json"


def load() -> dict[str, dict]:
    if OVERRIDES_PATH.exists():
        try:
            data = json.loads(OVERRIDES_PATH.read_text())
            merged = {k: {**v} for k, v in DEFAULT_FEES.items()}
            for k, v in data.items():
                if k in merged:
                    merged[k].update(v)
                else:
                    merged[k] = v
            return merged
        except Exception:
            pass
    return {k: {**v} for k, v in DEFAULT_FEES.items()}


def save(fees: dict[str, dict]):
    OVERRIDES_PATH.parent.mkdir(exist_ok=True)
    OVERRIDES_PATH.write_text(json.dumps(fees, indent=2, ensure_ascii=False))


def platform_fee(sell_price: float, platform: str, fees: dict | None = None) -> float:
    if fees is None:
        fees = load()
    f = fees.get(platform, {})
    base_pct = (f.get("commission_pct", 0) + f.get("payment_pct", 0) + f.get("transaction_pct", 0)) / 100
    base_fee = sell_price * base_pct
    vat = base_fee * (f.get("vat_on_fees", 0) / 100)
    return base_fee + vat


def net_profit(cost: float, sell: float, platform: str, fees: dict | None = None,
               extra_cost: float = 0.0) -> dict:
    fee = platform_fee(sell, platform, fees)
    net = sell - cost - fee - extra_cost
    margin = (net / sell * 100) if sell > 0 else 0
    return {
        "sell": sell, "cost": cost,
        "platform_fee": fee, "extra_cost": extra_cost,
        "net": net, "margin_pct": margin,
    }


def best_platform(cost: float, sell: float, fees: dict | None = None) -> str:
    if fees is None:
        fees = load()
    return max(fees, key=lambda p: net_profit(cost, sell, p, fees)["net"])
