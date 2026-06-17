# nirva.sell

**ระบบปฏิบัติการสำหรับแม่ค้าออนไลน์** — จัดการทุกอย่างตั้งแต่สต็อก ออเดอร์ กำไร โปรโมชั่น ไลฟ์สด ไปจนถึงใบกำกับภาษี ในแอปเดียว

🌐 **142 หน้า · 19 ภาษา UI · 17 สกุลเงิน · SQLite per-user · Self-host ได้**

## ฟรีตลอด · MIT License

```
✓ ทุกฟีเจอร์ครบ — ไม่มี trial หมดอายุ ไม่ล็อกฟีเจอร์
✓ SKU ไม่จำกัด · ออเดอร์ไม่จำกัด · ผู้ใช้ไม่จำกัด
✓ BYOK (คุณจ่าย Anthropic เอง ไม่บวกกลาง)
✓ Self-host ได้ (Streamlit Cloud / Docker / VPS / Local)
✓ Open source — fork ได้ ใช้ในเชิงพาณิชย์ได้
```

## Setup

```bash
git clone https://github.com/Nirvacore/Nirvasell.git
cd Nirvasell

python3 -m pip install -r requirements.txt

cp .env.example .env   # ใส่ ANTHROPIC_API_KEY (optional — ต้องการเฉพาะ AI features)
python3 -m streamlit run app.py --server.port 8501
```

เปิด **http://localhost:8501**

8 วิธี sign in: Email · Magic link · Google · Apple · Microsoft · GitHub · Facebook · LINE

---

## สำหรับนักพัฒนา / โคเซอร์

- **[CONTRIBUTING.md](CONTRIBUTING.md)** — อะไรทำใน repo นี้ได้ · module ย้ายแล้ว/รอ port · Python→TypeScript
- **[ECOSYSTEM_MAP.md](ECOSYSTEM_MAP.md)** — NirvaSell อยู่ตรงไหนใน BEST GROUP / NIRVA
- **[NIRVACORE_V1_PLAN.md](NIRVACORE_V1_PLAN.md)** — แผน monorepo (รอ audit ก่อน merge จริง)

> **Feature ใหม่ → [nirvacore-v1](https://github.com/Nirvacore/nirvacore-v1)** · repo นี้ = legacy + reference

---

## หน้าทั้งหมด (142 หน้า)

### 🧠 Knowledge & Compliance
| หน้า | ฟีเจอร์ |
|------|---------|
| 🧠 Knowledge Hub | ความรู้องค์กร — Vision, SOP, decisions, risks (knowledge graph) |
| 📚 Standards | Universal Compliance Graph — 60+ มาตรฐาน, 20 controls, evidence reuse |
| 📋 Policies | ดึง/วางนโยบาย marketplace → Claude สกัด fees → sync Knowledge Hub |
| 🛡 Compliance | สถานะมาตรฐานที่เกี่ยวข้อง + ลิงก์ไป Standards Graph |

### 📊 Dashboard & Core
| หน้า | ฟีเจอร์ |
|------|---------|
| 🏠 Dashboard | KPI รวม รายได้วันนี้ / สัปดาห์ / เดือน |
| 🌅 Daily Briefing | Morning digest: เมื่อวาน + alerts + งานวันนี้ |
| 🏆 KPIs | 16 ตัวชี้วัด พร้อม health score 0–100 |
| 🔔 Alerts | แจ้งเตือนอัจฉริยะ 6 ประเภท ตั้ง threshold ได้ |

### 🛍 Products & Inventory
| หน้า | ฟีเจอร์ |
|------|---------|
| 📦 Catalog | รายการสินค้าทั้งหมด ค้นหา แก้ไข |
| 🔄 Stock Turnover | อัตราหมุนเวียน + days-on-hand |
| ☠ Dead Stock | ตรวจสินค้าค้างสต็อก + แนะนำแก้ไข |
| 📈 SKU Trends | Rising stars, declining, สินค้าใหม่ |
| 🔤 ABC Analysis | Pareto 80/15/5 ต่อรายได้ |
| ⭐ Product Score | คะแนนสุขภาพรวม + BCG quadrant |

### 📦 Orders & Fulfillment
| หน้า | ฟีเจอร์ |
|------|---------|
| 🛒 Orders | ออเดอร์ทั้งหมด, status, แพลตฟอร์ม |
| 📋 Pick & Pack | Pick list + pack slips copy-ready |
| 🚀 Fulfillment | ยืนยันจัดส่ง บันทึกเลขพัสดุ bulk update |
| 🚚 Shipping | เปรียบ carrier ทุกเจ้า + true margin หลังค่าส่ง |
| 🔄 Returns | บันทึกคืนสินค้า วิเคราะห์เหตุผล loss |

### 💰 Finance
| หน้า | ฟีเจอร์ |
|------|---------|
| 📊 P&L | งบกำไรขาดทุน: รายเดือน / ไตรมาส / ปี |
| 💹 SKU Profit | กำไรต่อ SKU พร้อม health flag |
| 💵 Cash Flow | เงินเข้า/ออก รายวัน/เดือน + forecast |
| 🗓 Profit Calendar | กำไรรายวัน + วันดี/แย่สุด |
| 💰 Expenses | บันทึกค่าใช้จ่าย แยกหมวดหมู่ |
| 💰 Budget Tracker | งบประมาณรายเดือน + progress bar |

### 🧾 Documents
| หน้า | ฟีเจอร์ |
|------|---------|
| 🧾 Invoices | ใบแจ้งหนี้ dynamic line items |
| 📄 Tax Invoice | ใบกำกับภาษี VAT 7% + running number |
| 📱 PromptPay QR | สร้าง QR รับเงิน EMVCo standard |

### 📣 Marketing & Promotions
| หน้า | ฟีเจอร์ |
|------|---------|
| 📢 Promotions | โปรโมชั่น 6 ประเภท activate/pause |
| 🎟 Vouchers | โค้ดส่วนลด + เทมเพลต 8 เทศกาล |
| 💡 Price Optimizer | ราคาขายที่เหมาะสมต่อแพลตฟอร์ม |
| ⚡ Flash Sale | จัดการ flash sale + active-now banner |
| 📣 Ad Tracker | ติดตาม ROAS ทุกแคมเปญ |
| 📡 Channel Perf | เปรียบรายได้/growth แต่ละแพลตฟอร์ม |

### 👥 Customers
| หน้า | ฟีเจอร์ |
|------|---------|
| 👥 Customers | รายชื่อ VIP/dormant tier Bronze→Diamond |
| 🎯 RFM | RFM segmentation 9 กลุ่ม |
| 🎁 Loyalty | ระบบแต้ม 5 tier rewards catalogue |
| 🌟 Influencers | CRM อินฟลู + commission tracking |

### 📦 Purchasing & Stock
| หน้า | ฟีเจอร์ |
|------|---------|
| 🛒 Purchase Orders | สร้าง PO + send + receive stock |
| 📦 Restock Planner | วางแผนสั่งซื้อ critical/urgent/soon |
| 🔮 Demand Forecast | พยากรณ์ความต้องการ 30/60/90 วัน |
| 🏭 Wholesale | ราคาขายส่งขั้นบันได + quick quote |

### 📝 Operations
| หน้า | ฟีเจอร์ |
|------|---------|
| 📅 Content Calendar | ปฏิทินโพสต์ 7 แพลตฟอร์ม |
| 🔴 Live Sell | บันทึกออเดอร์ระหว่างไลฟ์สด |
| 💬 Quick Replies | เทมเพลตตอบแชต + variable substitution |
| ⭐ Reviews | ติดตามรีวิว reply workflow |
| 📝 Notes | โน้ต/task/reminder/issue/idea |
| 📈 Analytics | AOV trend, hourly heatmap, repeat buyers |
| 📤 Export | ดาวน์โหลดข้อมูลทั้งร้านเป็น ZIP |

---

## โครงสร้างไฟล์

```
nirva/
├── app.py                  # Entry point
├── _sidebar.py             # Sidebar shared component
├── _theme.py               # Zen minimal CSS theme
├── i18n.py                 # 3,800+ keys · 19 ภาษา
├── auth.py                 # Multi-provider auth (8 วิธี)
├── db.py                   # SQLite multi-tenant
├── knowledge_hub.py        # Knowledge graph (v80)
├── policy_watcher.py       # Marketplace policy cron (v81 bridge)
├── standards_kb/           # Universal Compliance Graph (v80)
├── nirva_os/               # Architecture blueprint (JSON)
├── nirva_research/         # Payroll / SOP research pack
├── pages/                  # 142 หน้า
├── *.py                    # 80+ backend modules
└── data/users/             # Per-user SQLite databases
```

## Security

- **SQLite per-user** — ข้อมูลแต่ละ user แยกไฟล์กัน `data/users/{id}.db`
- **BYOK** — API key ส่งตรงถึง Anthropic ไม่ผ่าน server กลาง
- **ENV only** — credentials ทั้งหมดใน `.env` ไม่อยู่ใน code
- Port 8501 ไม่เปิด internet โดยตรง — ใช้ reverse proxy

## License

MIT — ใช้ฟรี ใช้เชิงพาณิชย์ได้ fork ได้ ไม่ต้องขออนุญาต
