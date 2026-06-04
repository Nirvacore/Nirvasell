#!/usr/bin/env python3
"""Seed a "demo" user with rich sample data so first-time visitors see a
fully populated system without uploading anything.

Idempotent — re-running keeps the same demo user, refreshes data."""
from __future__ import annotations
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import auth
import db
import user_settings as us


DEMO_EMAIL = "demo@nirva.sell"
DEMO_PASSWORD = "demopass123"
DEMO_NAME = "Demo User"


PRODUCTS = [
    # Networking — Zyxel + Cisco — same model from 2 suppliers (for Sourcing demo)
    {"sku":"SYNNEX-ZYX-GS1920-48HPV2","name":"Zyxel GS1920-48HPV2 48-Port Gigabit Smart PoE+ Switch",
     "brand":"Zyxel","category":"Networking · Switch","cost_price":15200,"sell_price":17480,"stock":25,
     "specs":"48x Gigabit PoE+ (370W), 4 SFP, Smart Web GUI, VLAN/QoS/IGMP, 3yr warranty"},
    {"sku":"VSTECS-ZYX-G19248","name":"GS1920-48HPV2 Smart PoE Switch 48 ports",
     "brand":"Zyxel","category":"Networking · Switch","cost_price":14800,"sell_price":17030,"stock":3,
     "specs":"48-port Gigabit, PoE+ 370W, web management"},
    {"sku":"SYNNEX-CSC-RV340","name":"Cisco RV340 Dual-WAN Gigabit VPN Router",
     "brand":"Cisco","category":"Networking · Router","cost_price":8990,"sell_price":10340,"stock":10,
     "specs":"Dual WAN, 50 IPsec VPN sessions, 4 LAN, USB 3G/4G backup"},
    {"sku":"VSTECS-CSC-RV340","name":"Cisco RV340 Router 50 IPsec VPN",
     "brand":"Cisco","category":"Networking · Router","cost_price":9450,"sell_price":10870,"stock":40,
     "specs":"Dual WAN, VPN, web GUI"},
    {"sku":"VSTECS-CSC-RV340-ALT","name":"RV340 Gigabit Dual-WAN VPN Router (Cisco)",
     "brand":"Cisco","category":"Networking · Router","cost_price":8750,"sell_price":10070,"stock":1,
     "specs":"Dual WAN VPN router"},
    # WiFi
    {"sku":"VSTECS-TPL-EAP245","name":"TP-Link EAP245 AC1750 Gigabit Wireless Access Point",
     "brand":"TP-Link","category":"Networking · WiFi","cost_price":3500,"sell_price":4030,"stock":40,
     "specs":"AC1750 dual-band, Ceiling mount, 802.3af PoE, Omada SDN, 5yr warranty"},
    {"sku":"VSTECS-UBQ-UDM-SE","name":"Ubiquiti UniFi UDM-SE Dream Machine SE All-in-One",
     "brand":"Ubiquiti","category":"Networking · Gateway","cost_price":14500,"sell_price":16680,"stock":5,
     "specs":"8x Gigabit + 2x SFP+, IPS 3.5 Gbps, 128GB SSD, 1yr warranty"},
    # Laptops
    {"sku":"VSTECS-MIC-LCP3","name":"Microsoft Surface Laptop 3 13.5 i5/8GB/256GB",
     "brand":"Microsoft","category":"Laptop","cost_price":24900,"sell_price":28640,"stock":3,
     "specs":"Intel i5-1035G7, 8GB, 256GB SSD, 13.5 PixelSense, Platinum"},
    {"sku":"SYNNEX-HPS-PW850","name":"HP ProBook 450 G8 i7/16GB/512GB",
     "brand":"HP","category":"Laptop · Business","cost_price":32500,"sell_price":37380,"stock":8,
     "specs":"i7-1165G7, 16GB DDR4, 512GB NVMe, 15.6 FHD, Win11 Pro, 3yr on-site"},
    # Peripherals
    {"sku":"SYNNEX-LGI-MX350","name":"Logitech MX Master 3S Wireless Mouse Graphite",
     "brand":"Logitech","category":"Accessories · Mouse","cost_price":2790,"sell_price":3210,"stock":50,
     "specs":"8K DPI, Quiet clicks, 70-day battery, USB-C, MagSpeed scroll"},
    {"sku":"VSTECS-RZR-BLK-V3","name":"Razer BlackWidow V3 Pro Wireless Mechanical Keyboard",
     "brand":"Razer","category":"Accessories · Keyboard","cost_price":7990,"sell_price":9190,"stock":12,
     "specs":"Green switches, Doubleshot ABS, Chroma RGB, 192hr battery, BT/2.4GHz/USB-C"},
    # Storage
    {"sku":"SYNNEX-SAM-T5-1TB","name":"Samsung T5 Portable SSD 1TB USB 3.1",
     "brand":"Samsung","category":"Storage · SSD","cost_price":3290,"sell_price":3790,"stock":30,
     "specs":"540 MB/s read, AES-256, USB-C + USB-A cable, 3yr warranty"},
    {"sku":"VSTECS-WDC-SN570-2T","name":"WD Blue SN570 NVMe SSD 2TB M.2 PCIe Gen3",
     "brand":"WD","category":"Storage · NVMe","cost_price":4490,"sell_price":5170,"stock":18,
     "specs":"3500 MB/s read, 3000 MB/s write, M.2 2280, 5yr warranty"},
]


SAMPLE_LISTINGS = {
    "SYNNEX-ZYX-GS1920-48HPV2": {
        "title": "Zyxel GS1920-48HPV2 สวิตช์ 48 พอร์ต Gigabit PoE+ Smart Web ประกัน 3 ปี",
        "description": "• 48x Gigabit PoE+ พลังงานรวม 370W\n• Smart Web GUI — ตั้งค่าง่ายผ่านเบราว์เซอร์\n• รองรับ VLAN / QoS / IGMP Snooping\n• เหมาะสำหรับออฟฟิศ 50-150 เครื่อง\n• ประกันศูนย์ไทย 3 ปี · ส่งฟรีทั่วประเทศ",
        "tags": "switch,zyxel,poe,gigabit,48port,gs1920,smart,network",
    },
    "SYNNEX-CSC-RV340": {
        "title": "Cisco RV340 เราเตอร์ Dual-WAN VPN ระดับธุรกิจ รับประกันศูนย์",
        "description": "• Dual WAN auto-failover ไม่มี downtime\n• รองรับ IPsec VPN 50 sessions พร้อมกัน\n• 4 LAN gigabit + USB 3G/4G backup\n• Web GUI ภาษาไทย ตั้งค่าง่าย\n• เหมาะกับ SME 25-50 user",
        "tags": "router,cisco,vpn,dual-wan,rv340,business,sme",
    },
    "SYNNEX-LGI-MX350": {
        "title": "Logitech MX Master 3S เมาส์ไร้สาย 8K DPI Quiet Click แบต 70 วัน",
        "description": "• เซ็นเซอร์ 8K DPI ใช้ได้ทุกพื้นผิว แม้กระจก\n• Quiet click ลดเสียงคลิก 90% เหมาะ work-from-home\n• แบตเตอรี่ 70 วัน · USB-C ชาร์จเร็ว\n• MagSpeed scroll หมุน 1,000 บรรทัดต่อวินาที\n• เชื่อม 3 อุปกรณ์สลับด้วยปุ่มเดียว",
        "tags": "mouse,logitech,mx-master,wireless,8k-dpi,quiet,productivity",
    },
}


# Generate fake orders (for Dashboard demo)
def _fake_orders(skus: list[str]) -> list[dict]:
    import random
    random.seed(42)
    orders = []
    days_back = 30
    order_n = 1
    for sku in skus:
        # 1-5 orders per SKU
        for _ in range(random.randint(1, 5)):
            d = datetime.now() - timedelta(
                days=random.randint(1, days_back),
                hours=random.randint(0, 23),
            )
            qty = random.randint(1, 3)
            # Pull cost_price for sku
            base = next((p["sell_price"] for p in PRODUCTS if p["sku"] == sku), 1000)
            unit = base
            orders.append({
                "order_id": f"DEMO-{order_n:05d}",
                "sku": sku,
                "platform": random.choice(["shopee", "lazada", "tiktok"]),
                "qty": qty,
                "unit_price": unit,
                "total_price": unit * qty,
                "currency": "THB",
                "order_date": d.isoformat(),
                "status": "paid",
            })
            order_n += 1
    return orders


def seed():
    print("Seeding demo user…")
    auth.init()

    # 1. Ensure demo user exists
    existing = next(
        (u for u in auth.list_users() if u["email"] == DEMO_EMAIL),
        None,
    )
    if existing:
        print(f"  Demo user exists (id={existing['id']})")
        demo = existing
    else:
        ok, msg = auth.signup(DEMO_EMAIL, DEMO_PASSWORD, DEMO_NAME)
        if not ok:
            print(f"  Signup failed: {msg}")
            return
        demo = next(u for u in auth.list_users() if u["email"] == DEMO_EMAIL)
        print(f"  Created demo user id={demo['id']}")

    # 2. Switch DB context to demo user
    import streamlit as _st
    _st.session_state = {"auth_user": demo}

    db.init()
    us.init()

    # 3. Reset + seed products
    with db.conn() as c:
        c.execute("DELETE FROM content")
        c.execute("DELETE FROM products")
        c.execute("DELETE FROM batches")
        c.execute("DELETE FROM product_groups")
        c.execute("DELETE FROM orders")

    import pandas as pd
    df = pd.DataFrame(PRODUCTS)
    bid = db.create_batch("demo-seed.xlsx", len(df))
    n = db.upsert_products(df, bid)
    print(f"  Inserted {n} products")

    # 4. Auto-group products (multi-supplier detection)
    import sourcing
    stats = sourcing.auto_group_all()
    print(f"  Auto-grouped: {stats['linked']} linked, {stats['groups_created']} groups created")

    # 5. Seed listings for a few products
    with db.conn() as c:
        for sku, listing in SAMPLE_LISTINGS.items():
            row = c.execute("SELECT id FROM products WHERE sku = ?", (sku,)).fetchone()
            if row:
                db.save_content(row["id"], "listing", listing)
    print(f"  Seeded {len(SAMPLE_LISTINGS)} listings")

    # 6. Seed orders
    import order_import as oi
    skus = [p["sku"] for p in PRODUCTS[:10]]  # only first 10
    fake_orders_df = pd.DataFrame(_fake_orders(skus))
    n_orders = oi.save_orders(fake_orders_df)
    print(f"  Inserted {n_orders} orders")

    # 7. Some default settings
    us.set("markup_percent", 15)
    us.set("round_to", 10)
    us.set("currency", "THB")
    us.set_notify_prefs({
        "batch_done": True, "policy_change": True,
        "review_block": True, "low_stock": False, "import_done": False,
    })
    print("  Settings saved")

    print(f"\n✓ Demo user ready: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    return demo


if __name__ == "__main__":
    seed()
