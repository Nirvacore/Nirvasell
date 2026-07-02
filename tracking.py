"""Tracking link generator + customer notification composer.

After seller marks order shipped (Fulfillment page), they still have to
notify the customer individually in LINE/FB chat. This module turns each
shipment into a ready-to-paste message with the carrier's public tracking
URL filled in.

Coverage: the 8 carriers we already support in fulfillment.py."""
from __future__ import annotations

from i18n import t
from i18n_inline import carrier_name, localized


# Public tracking URLs per Thai carrier. Each function takes a tracking
# number string and returns the full deep-link.
CARRIER_TRACK_URL = {
    "kerry":    lambda tn: f"https://th.kerryexpress.com/th/track/?track={tn}",
    "flash":    lambda tn: f"https://www.flashexpress.com/fle/tracking?se={tn}",
    "thaipost": lambda tn: f"https://track.thailandpost.co.th/?trackNumber={tn}",
    "j&t":      lambda tn: f"https://www.jtexpress.co.th/index/query/gzquery.html?bills={tn}",
    "ninjavan": lambda tn: f"https://www.ninjavan.co/th-th/tracking?id={tn}",
    "best":     lambda tn: f"https://www.best-inc.co.th/track-search?ids={tn}",
    "scg":      lambda tn: f"https://www.scgexpress.co.th/tracking?track={tn}",
    "dhl":      lambda tn: f"https://www.dhl.com/th-en/home/tracking.html?tracking-id={tn}",
}


def tracking_url(carrier: str, tracking_number: str) -> str:
    """Resolve carrier key → public tracking URL. Returns '' if unknown
    or no tracking number."""
    carrier = (carrier or "").strip().lower()
    tracking_number = (tracking_number or "").strip()
    if not tracking_number:
        return ""
    fn = CARRIER_TRACK_URL.get(carrier)
    return fn(tracking_number) if fn else ""


def compose(*, order_id: str, carrier: str, tracking_number: str,
            tone: str = "friendly", lang: str = "th",
            shop_name: str = "") -> str:
    """Build the customer message. `tone` = friendly | formal | short."""
    carrier_key = (carrier or "").strip().lower()
    key = f"track.msg_{tone}"
    template = localized(key, lang)
    if not template or template == key:
        template = localized("track.msg_friendly", lang)
    return template.format(
        order_id=order_id or "—",
        carrier_label=carrier_name(carrier_key) if carrier_key else (carrier or "—"),
        tracking_number=tracking_number or "—",
        tracking_url=tracking_url(carrier_key, tracking_number) or "—",
        shop_name=shop_name or t("track.shop_default"),
    )


def compose_batch(orders: list[dict], *, tone: str = "friendly",
                  lang: str = "th", shop_name: str = "") -> list[dict]:
    """Compose messages for many orders in one shot. Each input order
    dict needs: order_id, carrier, tracking_number, (optional) customer_name."""
    out = []
    for o in orders:
        msg = compose(
            order_id=str(o.get("order_id", "")),
            carrier=str(o.get("carrier", "")),
            tracking_number=str(o.get("tracking_number", "")),
            tone=tone, lang=lang, shop_name=shop_name,
        )
        out.append({
            "order_id":  o.get("order_id"),
            "customer":  o.get("customer_name") or o.get("buyer_name") or "",
            "platform":  o.get("platform") or "",
            "message":   msg,
        })
    return out
