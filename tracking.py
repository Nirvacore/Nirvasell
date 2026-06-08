"""Tracking link generator + customer notification composer.

After seller marks order shipped (Fulfillment page), they still have to
notify the customer individually in LINE/FB chat. This module turns each
shipment into a ready-to-paste message with the carrier's public tracking
URL filled in.

Coverage: the 8 carriers we already support in fulfillment.py."""
from __future__ import annotations


# Public tracking URLs per Thai carrier. Each function takes a tracking
# number string and returns the full deep-link.
CARRIER_TRACK_URL = {
    "kerry":    lambda t: f"https://th.kerryexpress.com/th/track/?track={t}",
    "flash":    lambda t: f"https://www.flashexpress.com/fle/tracking?se={t}",
    "thaipost": lambda t: f"https://track.thailandpost.co.th/?trackNumber={t}",
    "j&t":      lambda t: f"https://www.jtexpress.co.th/index/query/gzquery.html?bills={t}",
    "ninjavan": lambda t: f"https://www.ninjavan.co/th-th/tracking?id={t}",
    "best":     lambda t: f"https://www.best-inc.co.th/track-search?ids={t}",
    "scg":      lambda t: f"https://www.scgexpress.co.th/tracking?track={t}",
    "dhl":      lambda t: f"https://www.dhl.com/th-en/home/tracking.html?tracking-id={t}",
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


# ---- Customer notification messages -----------------------------------

# Multi-language templates. {placeholders} get resolved per order.
TEMPLATES = {
    "th": {
        "friendly": (
            "สวัสดีค่ะ! 🎉\n"
            "ของของคุณส่งออกแล้วนะคะ\n\n"
            "📦 Order: {order_id}\n"
            "🚚 ขนส่ง: {carrier_label}\n"
            "🔍 Tracking: {tracking_number}\n"
            "🔗 ติดตามได้ที่: {tracking_url}\n\n"
            "ปกติถึงใน 1-3 วันค่ะ ขอบคุณที่อุดหนุน {shop_name} นะคะ ✨"
        ),
        "formal": (
            "เรียน ลูกค้า\n\n"
            "ทาง {shop_name} ได้ส่งสินค้าของท่านแล้วเมื่อวันนี้\n\n"
            "เลขที่คำสั่งซื้อ: {order_id}\n"
            "ขนส่งโดย: {carrier_label}\n"
            "หมายเลขติดตาม: {tracking_number}\n"
            "ลิงก์ติดตาม: {tracking_url}\n\n"
            "ขอบคุณที่ใช้บริการค่ะ"
        ),
        "short": (
            "ส่งของแล้วค่ะ 📦\n{carrier_label}: {tracking_number}\n{tracking_url}"
        ),
    },
    "en": {
        "friendly": (
            "Hello! 🎉\n"
            "Your order has been shipped!\n\n"
            "📦 Order: {order_id}\n"
            "🚚 Carrier: {carrier_label}\n"
            "🔍 Tracking: {tracking_number}\n"
            "🔗 Track here: {tracking_url}\n\n"
            "Usually arrives in 1-3 days. Thank you for shopping with {shop_name}! ✨"
        ),
        "formal": (
            "Dear Customer,\n\n"
            "{shop_name} has dispatched your order today.\n\n"
            "Order ID: {order_id}\n"
            "Carrier: {carrier_label}\n"
            "Tracking #: {tracking_number}\n"
            "Track link: {tracking_url}\n\n"
            "Thank you for your purchase."
        ),
        "short": (
            "Shipped! 📦\n{carrier_label}: {tracking_number}\n{tracking_url}"
        ),
    },
    "zh": {
        "friendly": (
            "您好!🎉\n您的订单已发货!\n\n"
            "📦 订单: {order_id}\n🚚 物流: {carrier_label}\n"
            "🔍 单号: {tracking_number}\n🔗 查询: {tracking_url}\n\n"
            "通常 1-3 天送达。感谢您选择 {shop_name}!✨"
        ),
        "formal": (
            "尊敬的顾客:\n\n{shop_name} 已于今日为您发货。\n\n"
            "订单号: {order_id}\n物流: {carrier_label}\n"
            "单号: {tracking_number}\n查询: {tracking_url}\n\n感谢惠顾。"
        ),
        "short": (
            "已发货 📦\n{carrier_label}: {tracking_number}\n{tracking_url}"
        ),
    },
}


CARRIER_LABELS = {
    "kerry":    "Kerry Express",
    "flash":    "Flash Express",
    "thaipost": "ไปรษณีย์ไทย",
    "j&t":      "J&T Express",
    "ninjavan": "Ninja Van",
    "best":     "BEST Express",
    "scg":      "SCG Express",
    "dhl":      "DHL",
}


def compose(*, order_id: str, carrier: str, tracking_number: str,
            tone: str = "friendly", lang: str = "th",
            shop_name: str = "") -> str:
    """Build the customer message. `tone` = friendly | formal | short."""
    carrier_key = (carrier or "").strip().lower()
    template = (TEMPLATES.get(lang) or TEMPLATES["en"]).get(tone)
    if not template:
        template = TEMPLATES[lang]["friendly"]
    return template.format(
        order_id=order_id or "—",
        carrier_label=CARRIER_LABELS.get(carrier_key, carrier or "—"),
        tracking_number=tracking_number or "—",
        tracking_url=tracking_url(carrier_key, tracking_number) or "—",
        shop_name=shop_name or "เรา",
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
