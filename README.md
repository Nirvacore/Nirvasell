# nirva.sell

**AI Sales Workspace** สำหรับนักขาย "ซื้อมาขายไป" — drop ไฟล์ → 1 ปุ่ม → ได้เนื้อหาขายทุกอย่าง + รู้กำไรจริงต่อแพลตฟอร์มทั่วโลก

🌐 **7 UI languages · 13 AI output languages · 17 currencies · 10 marketplaces**

## ฟรีตลอด · MIT License

```
✓ ทุกฟีเจอร์ครบ — ไม่มี trial หมดอายุ ไม่ล็อกฟีเจอร์
✓ SKU ไม่จำกัด
✓ BYOK (คุณจ่าย Anthropic เอง ไม่บวกกลาง)
✓ Self-host ได้ (Streamlit Cloud / Docker / VPS)
✓ Open source — fork ได้ ใช้ในเชิงพาณิชย์ได้
```

**ทำไม:** เครื่องมือขายของควรเข้าถึงได้สำหรับทุกคน. ค่าใช้แอปไม่ควรเป็นด่านแรกที่ทำให้ reseller รายเล็กเริ่มไม่ได้.

**ถ้าอยากช่วยให้ระบบอยู่ต่อ:** Pay-what-you-can ที่หน้า [💝 Support](pages/A_💝_Support.py). ฿20 ก็ขอบคุณ ฿2,000 ก็ขอบคุณ ใช้ฟรีก็ขอบคุณเหมือนกัน

## Workflow ครบสำหรับ Reseller

```
1. วาง pricelist (Excel/CSV/PDF/text paste)
            ↓
2. AI สกัดสินค้า + auto-mapping คอลัมน์
            ↓
3. เห็นกำไรสุทธิแต่ละแพลตฟอร์ม (หัก fee แล้ว) → รู้ขายที่ไหนคุ้มที่สุด
            ↓
4. กดปุ่ม "✨ ทำให้หมด" — 1 AI call ต่อสินค้า → ได้ 7 เนื้อหา:
   🛒 Listing  💚 LINE  📘 Facebook  🎵 TikTok  ✉️ Email  💬 Q&A  🔥 Promo
            ↓
5. ดาวน์โหลด CSV ไป bulk-upload Shopee/Lazada/TikTok ทันที
```

## What you get (8 AI tasks)

| | Task | จุดเด่นสำหรับ reseller |
|---|---|---|
| 🛒 | **Marketplace Listing** | Title + Description + Tags → Shopee/Lazada/TikTok CSV bulk |
| 💚 | **LINE Broadcast** | ข้อความสั้นๆ สำหรับ LINE OA — ปั่นยอดกลุ่ม VIP |
| 📘 | **Facebook Post** | Story-style + hashtags — feed traffic ฟรี |
| 🎵 | **TikTok 30s Script** | Hook + shot list — UGC-ready |
| ✉️ | **Email Blast** | Subject + preheader + body HTML — รักษาฐานลูกค้าเก่า |
| 💬 | **Customer Q&A** | 8 คำถาม-คำตอบสำเร็จรูป — ลดเวลาตอบแชต |
| 🔥 | **Promo / Flash Sale** | Urgency copy + ราคาหลังลดอัตโนมัติ |
| 📦 | **Bundle Proposal** | รวมหลายชิ้น + ส่วนลด + คำขาย |

## 💰 Profit Math จริง (ไม่ใช่แค่ markup %)

Sidebar slider บอกแค่ markup % — แต่ Workspace แสดง **กำไรสุทธิหักค่า fee** ของแต่ละแพลตฟอร์ม:

```
ตัวอย่าง: cost ฿15,200 → sell ฿17,480 (markup 15%)

  Shopee   fee ฿1,801 (10.3%)  →  net ฿479    (2.7% margin) 😱 เกือบขาดทุน
  Lazada   fee ฿1,309 (7.5%)   →  net ฿971    (5.6% margin) ✓
  TikTok   fee ฿1,309 (7.5%)   →  net ฿971    (5.6% margin) ✓
```

ปรับ fee เองได้ใน `data/fee_overrides.json` ตาม category / seller tier

## Setup

```bash
cd /Users/machd/Claude/nirva

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env  # ใส่ ANTHROPIC_API_KEY
streamlit run app.py
```

เปิด http://localhost:8501

## Pages

```
ทำงาน (app)        → drop / paste → 1 click → ทุกอย่าง
สินค้าของฉัน        → browse / filter, รูปสินค้า, edit รายตัว
ให้ AI ทำให้        → เลือก task เฉพาะ (ถ้าไม่ใช้ all-in-one)
ของที่ทำไว้แล้ว     → edit inline, regenerate, download
ดึงจาก reseller    → import จาก scraper (Synnex/VSTECS)
```

## รับ input หลายแบบ

- **Excel / CSV / TSV** — auto-detect คอลัมน์ Thai/English
- **PDF pricelist** — สกัด text + Claude แปลงเป็นตาราง
- **Paste text** — คัดลอกตารางจาก email dealer วางได้เลย
- **reseller/ DB** — bridge อ่านโดยตรง พร้อมรูปจาก Cloudinary

## เปลี่ยนภาษา

URL: `?lang=th` | `?lang=en` | `?lang=zh` | `?lang=ja` | `?lang=ko` | `?lang=vi` | `?lang=id`

## โครงสร้าง

```
nirva/
├── app.py                  # Workspace (single-page flow)
├── _sidebar.py / _theme.py / _components.py
├── i18n.py                 # 7 ภาษา ทั้งหมดในไฟล์เดียว
├── db.py                   # SQLite store
├── parser.py               # Excel/CSV → DataFrame + auto column mapping
├── intake.py               # universal reader (Excel/CSV/PDF/text)
├── generate.py             # Claude batch + parallel + all-in-one runner
├── fees.py                 # Shopee/Lazada/TikTok fee math
├── bridge_reseller.py      # import จาก reseller/ scraper
├── tasks/                  # 8 AI tasks (+ 1 all-in-one mega task)
│   ├── listing.py  line_post.py  fb_post.py  tiktok_script.py
│   ├── email_blast.py  bundle.py  customer_qa.py  promotion.py
│   └── all_in_one.py
├── exporters/              # Shopee / Lazada / TikTok CSV writers
├── pages/                  # Catalog · Generate · History · Import
└── landing.html
```

## เพิ่ม Task ใหม่

ทำไฟล์ `tasks/my_task.py`:

```python
TASK = {"key": "my_task", "label": "...", "icon": "🎁", "blurb": "...",
        "output_fields": ["a", "b"]}

def build_prompt(row): ...
def parse(text) -> dict: ...
```

เพิ่มชื่อใน `tasks/__init__.py` — UI ทุกหน้า auto-pick-up

## Roadmap

- [ ] Competitor URL scan (paste Shopee link → คู่แข่งราคาเท่าไหร่)
- [ ] Performance dashboard (อะไรขายดี / ไม่ดี)
- [ ] Inventory sync (alert when stock < N)
- [ ] Repricing suggestions (อายุ stock + market trend)
- [ ] Stripe subscription gate (free 10 / pro unlimited)
