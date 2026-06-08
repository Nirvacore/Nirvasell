"""AI-powered customer messages — turn CRM data into revenue.

Generates personalized messages for different customer segments:
  - Re-engage dormant customers ("คิดถึงนะคะ กลับมาช้อปไหม")
  - Thank VIP customers ("ขอบคุณที่อุดหนุนมาตลอด")
  - Welcome first-time buyers ("ยินดีต้อนรับ ออเดอร์แรกส่งแล้วนะ")
  - Promotion blasts for specific segments

Uses Claude Haiku for fast, cheap generation. Returns ready-to-paste
messages the seller copies into LINE/FB/Shopee chat."""
from __future__ import annotations


SEGMENT_PROMPTS = {
    "dormant": {
        "th": (
            "คุณเป็นผู้ช่วยร้านค้าออนไลน์ไทย เขียนข้อความทักลูกค้าที่ไม่ได้ซื้อนานแล้ว\n"
            "ชื่อลูกค้า: {name}\n"
            "ซื้อครั้งสุดท้าย: {last_order}\n"
            "เคยซื้อ: {order_count} ครั้ง ยอดรวม ฿{total_spent}\n"
            "ชื่อร้าน: {shop_name}\n\n"
            "เขียนข้อความ LINE/FB สั้นๆ 2-3 บรรทัด เป็นกันเอง อบอุ่น ไม่กดดัน "
            "ให้รู้สึกว่าร้านคิดถึง ไม่ใช่ขายของ อาจมีโปรพิเศษเล็กน้อย"
        ),
        "en": (
            "You are a Thai online shop assistant. Write a re-engagement message.\n"
            "Customer: {name}\nLast order: {last_order}\n"
            "History: {order_count} orders, ฿{total_spent} total\nShop: {shop_name}\n\n"
            "Write 2-3 line friendly LINE/FB message. Warm, not pushy."
        ),
    },
    "vip_thank": {
        "th": (
            "คุณเป็นผู้ช่วยร้านค้าออนไลน์ไทย เขียนข้อความขอบคุณลูกค้า VIP\n"
            "ชื่อลูกค้า: {name}\n"
            "ซื้อทั้งหมด: {order_count} ครั้ง ยอดรวม ฿{total_spent}\n"
            "ชื่อร้าน: {shop_name}\n\n"
            "เขียนข้อความ LINE/FB สั้นๆ 2-3 บรรทัด ให้รู้สึกว่าเป็นคนพิเศษจริงๆ "
            "อาจให้ส่วนลด VIP exclusive หรือสิทธิพิเศษ"
        ),
        "en": (
            "Write a VIP thank-you message for a loyal customer.\n"
            "Customer: {name}\n{order_count} orders, ฿{total_spent} total\nShop: {shop_name}\n\n"
            "Short, warm, make them feel special. 2-3 lines."
        ),
    },
    "welcome": {
        "th": (
            "คุณเป็นผู้ช่วยร้านค้าออนไลน์ไทย เขียนข้อความต้อนรับลูกค้าใหม่\n"
            "ชื่อลูกค้า: {name}\n"
            "ชื่อร้าน: {shop_name}\n\n"
            "เขียนข้อความ LINE/FB สั้นๆ 2-3 บรรทัด ต้อนรับ ขอบคุณ แนะนำให้กลับมาซื้ออีก"
        ),
        "en": (
            "Write a welcome message for a first-time buyer.\n"
            "Customer: {name}\nShop: {shop_name}\n\n"
            "Short welcome + thank you. 2-3 lines."
        ),
    },
    "promo": {
        "th": (
            "คุณเป็นผู้ช่วยร้านค้าออนไลน์ไทย เขียนข้อความโปรโมชัน\n"
            "ชื่อลูกค้า: {name}\n"
            "โปรโมชัน: {promo_detail}\n"
            "ชื่อร้าน: {shop_name}\n\n"
            "เขียนข้อความ LINE/FB สั้นๆ 2-4 บรรทัด น่าสนใจ มี urgency เล็กน้อย"
        ),
        "en": (
            "Write a promotion message.\n"
            "Customer: {name}\nPromo: {promo_detail}\nShop: {shop_name}\n\n"
            "Short, compelling, slight urgency. 2-4 lines."
        ),
    },
}


def generate_message(*, segment: str, customer: dict, shop_name: str = "",
                     api_key: str, lang: str = "th",
                     promo_detail: str = "") -> str:
    template = (SEGMENT_PROMPTS.get(segment, {}).get(lang)
                or SEGMENT_PROMPTS.get(segment, {}).get("th", ""))
    if not template:
        return ""

    prompt = template.format(
        name=customer.get("name", "ลูกค้า"),
        last_order=customer.get("last_order", "—"),
        order_count=customer.get("order_count", 0),
        total_spent="{:,.0f}".format(customer.get("total_spent", 0)),
        shop_name=shop_name or "ร้านเรา",
        promo_detail=promo_detail,
    )

    from anthropic import Anthropic
    msg = Anthropic(api_key=api_key).messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def batch_generate(*, segment: str, customers: list[dict],
                   shop_name: str = "", api_key: str, lang: str = "th",
                   promo_detail: str = "") -> list[dict]:
    results = []
    for c in customers:
        try:
            msg = generate_message(
                segment=segment, customer=c, shop_name=shop_name,
                api_key=api_key, lang=lang, promo_detail=promo_detail,
            )
            results.append({"customer": c, "message": msg, "ok": True})
        except Exception as e:
            results.append({"customer": c, "message": str(e), "ok": False})
    return results
