# Contributing to NirvaSell

> **สถานะ: กำลังเขียนใหม่เข้า NirvaCore**
> Repo นี้เป็น Python/Streamlit ซึ่ง **จะไม่ใช้ต่อ**
> Feature ทั้งหมดกำลังถูกเขียนใหม่เป็น TypeScript ใน [nirvacore-v1](https://github.com/Nirvacore/nirvacore-v1)

---

## Tech Stack เดิม (ห้ามใช้ต่อ)

```
Language:   Python 3.11
Framework:  Streamlit 1.56
Database:   SQLite (per-user)
AI:         Anthropic Claude API
```

**ทำไมต้องเปลี่ยน**:
- Streamlit ไม่ scale — single-threaded, no multi-tenant
- SQLite ไม่รองรับ concurrent writes
- แยก tech stack จากทุก repo อื่น (Python vs TypeScript)
- ไม่มี proper auth / permission system

---

## Tech Stack ใหม่ (ใช้ใน NirvaCore)

```
Backend:    TypeScript · NestJS 10 · Prisma ORM 5.x · PostgreSQL 16
Frontend:   TypeScript · Next.js 14 · React 18 · TailwindCSS
```

ดู CONTRIBUTING.md ของ nirvacore-v1 สำหรับรายละเอียดทั้งหมด

---

## Module ที่ย้ายเข้า NirvaCore แล้ว

| Python Module เดิม | อยู่ที่ NirvaCore |
|--------------------|-------------------|
| `rfm.py` (RFM Segmentation) | `sell-analytics/rfm.service.ts` |
| `demand_forecast.py` | `sell-analytics/demand-forecast.service.ts` |
| Catalog/Products | `catalog/` |
| Orders | `orders/` |
| Customers | `customers/` |
| P&L | `accounting/` |

## Module ที่รอเขียนใหม่ (เลือกทำ)

**สำคัญสูง**:
| Python file | คำอธิบาย | ความซับซ้อน |
|-------------|----------|------------|
| `abc_analysis.py` | ABC สินค้าขายดี/ช้า | ต่ำ |
| `auto_pricing.py` | ปรับราคาอัตโนมัติ | กลาง |
| `biz_health.py` | Business Health Score | กลาง |
| `promo_engine.py` | Promotion/Coupon Engine | กลาง |
| `shipping_calc.py` | คำนวณค่าส่ง | ต่ำ |
| `tax_report.py` | สรุปภาษี/ใบกำกับ | กลาง |

**สำคัญปานกลาง**:
| Python file | คำอธิบาย | ความซับซ้อน |
|-------------|----------|------------|
| `ads_tracker.py` | ROI โฆษณา | กลาง |
| `batch_ops.py` | Bulk operations | ต่ำ |
| `live_dashboard.py` | Live streaming sales | สูง |
| `multi_platform.py` | Shopee/Lazada/LINE sync | สูง |
| `returns.py` | คืนสินค้า/เปลี่ยน | กลาง |

---

## วิธีเขียนใหม่จาก Python → TypeScript

### 1. อ่าน Python file เดิม
```bash
cat Nirvasell/abc_analysis.py
```

### 2. เข้าใจ logic — ไม่ต้องแปลตรงๆ
- Python ใช้ pandas → NestJS ใช้ Prisma queries
- SQLite queries → PostgreSQL via Prisma
- Streamlit UI → Next.js React components

### 3. ตัวอย่างการแปลง

**Python เดิม (rfm.py)**:
```python
with db.conn() as c:
    customers = c.execute(
        "SELECT id, name, order_count, total_spent, last_order FROM customers"
    ).fetchall()
for cust in customers:
    recency_days = (now - last_dt).days
```

**TypeScript ใหม่ (rfm.service.ts)**:
```typescript
const customers = await this.prisma.order.groupBy({
  by: ['customerId'],
  where: { companyId, status: { notIn: ['CANCELLED', 'REFUNDED'] } },
  _count: { _all: true },
  _sum: { total: true },
  _max: { createdAt: true },
});
```

### 4. สร้าง NestJS module ตาม pattern ใน NirvaCore

ดู CONTRIBUTING.md ของ nirvacore-v1 สำหรับ step-by-step guide

---

## ไฟล์ Python ทั้งหมด (299 ไฟล์, 142 หน้า)

อ่าน reference ได้ที่ `/home/user/Nirvasell/` — ใช้เป็นแหล่งอ้างอิง business logic
แต่ **ห้าม deploy Python ใหม่** — เขียน TypeScript ใน NirvaCore เท่านั้น
