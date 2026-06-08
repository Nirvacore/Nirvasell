"""LINE Notify integration — push alerts to seller's LINE.

LINE Notify is FREE, no monthly fee, no LINE OA needed. Just:
1. Go to notify-bot.line.me
2. Generate a token
3. Paste it into nirva Settings

Then nirva sends alerts:
  - New order received
  - Stock running low
  - Daily summary report
  - Slip verification result

Uses simple REST POST — no SDK, no dependencies beyond requests/urllib."""
from __future__ import annotations

import urllib.request
import urllib.parse
import json


NOTIFY_API = "https://notify-api.line.me/api/notify"
STATUS_API = "https://notify-api.line.me/api/status"


def _post(token: str, message: str) -> dict:
    data = urllib.parse.urlencode({"message": message}).encode("utf-8")
    req = urllib.request.Request(
        NOTIFY_API,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            return {"ok": body.get("status") == 200, "message": body.get("message", "")}
    except urllib.error.HTTPError as e:
        return {"ok": False, "message": f"HTTP {e.code}"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


def check_token(token: str) -> dict:
    req = urllib.request.Request(
        STATUS_API,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            return {
                "ok": body.get("status") == 200,
                "target": body.get("target", ""),
                "target_type": body.get("targetType", ""),
            }
    except Exception as e:
        return {"ok": False, "target": "", "target_type": "", "error": str(e)}


def send(token: str, message: str) -> dict:
    if not token or not token.strip():
        return {"ok": False, "message": "No LINE Notify token configured"}
    return _post(token.strip(), message)


def notify_new_order(token: str, *, order_id: str, platform: str,
                     product: str = "", amount: float = 0) -> dict:
    msg = (
        f"\n🛒 ออเดอร์ใหม่!"
        f"\n📦 {order_id}"
        f"\n🏪 {platform}"
    )
    if product:
        msg += f"\n📋 {product[:60]}"
    if amount:
        msg += f"\n💰 ฿{amount:,.0f}"
    return send(token, msg)


def notify_low_stock(token: str, *, sku: str, name: str, remaining: int) -> dict:
    msg = (
        f"\n⚠ สต็อกใกล้หมด!"
        f"\n📦 {sku} · {name[:40]}"
        f"\n📊 เหลือ {remaining} ชิ้น"
        f"\nเติมสต็อกด่วน!"
    )
    return send(token, msg)


def notify_daily_summary(token: str, *, date: str, orders: int,
                         revenue: float, profit: float) -> dict:
    msg = (
        f"\n📊 สรุปวันนี้ ({date})"
        f"\n📦 ออเดอร์: {orders}"
        f"\n💰 รายได้: ฿{revenue:,.0f}"
        f"\n📈 กำไร: ฿{profit:,.0f}"
    )
    return send(token, msg)


def notify_slip_result(token: str, *, amount: float, sender: str,
                       confidence: str) -> dict:
    icon = "✅" if confidence == "high" else ("⚠" if confidence == "medium" else "❌")
    msg = (
        f"\n{icon} ตรวจสลิป"
        f"\n💰 ฿{amount:,.0f}"
        f"\n👤 {sender}"
        f"\n🔍 ความน่าเชื่อถือ: {confidence}"
    )
    return send(token, msg)
