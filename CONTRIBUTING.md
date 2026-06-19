# Contributing to NirvaSell

> **สถานะ: Legacy reference · feature ใหม่ไปที่ NirvaCore**
>
> Repo นี้เป็น Python/Streamlit (nirva.sell) — **ใช้รันได้ แต่ไม่เพิ่มฟีเจอร์ใหม่ที่นี่**
> งานใหม่เขียนเป็น **TypeScript** ใน [nirvacore-v1](https://github.com/Nirvacore/nirvacore-v1)

---

## ภาษา / stack ต่อ repo (NIRVA Ecosystem)

| Repo | ภาษา | Framework / DB | บทบาท |
|------|------|----------------|-------|
| **[nirvacore-v1](https://github.com/Nirvacore/nirvacore-v1)** | **TypeScript** | NestJS 10 · Next.js 14 · Prisma · PostgreSQL | **ERP หลัก — ที่เขียนต่อ** |
| **Nirvasell** (repo นี้) | Python 3.11+ | Streamlit · SQLite per-user | Legacy + reference · maintenance เท่านั้น |
| **Nirvaprocure** | TypeScript | (กำลังรวมเข้า nirvacore-v1) | Procurement OS |
| **nirvadeploy** | TypeScript | — | Deploy / infra tooling |
| `nirva_research/` (ใน repo นี้) | Python (stdlib) | JSON data + `payroll_engine.py` | สูตร/กฎธุรกิจ — **port logic ไป TS** ไม่ deploy Python ใหม่ |
| `standards_kb/` (ใน repo นี้) | Python + JSON | dependency-free graph | Compliance — บ้านในอนาคต = **NirvaGov** package ใน nirvacore-v1 |

**กฎภาษา (บังคับ):**

1. ฟีเจอร์ production ใหม่ → **TypeScript ใน nirvacore-v1** เท่านั้น
2. Repo นี้ → แก้ bug / docs / i18n / cron ได้ · **ห้าม** เพิ่มหน้า Streamlit หรือ module Python ใหม่
3. Python ใน `nirva_research/` และ `standards_kb/` = **อ้างอิง business logic** — อ่านแล้วแปลเป็น NestJS service + Prisma
4. มี prototype Python ERP บน branch เก่า (`claude/nirva-ecosystem-v3`) — **ไม่ใช่ Source of Truth**; SoT คือ TypeScript ใน nirvacore-v1 (ดู [REPO_REGISTRY.md](REPO_REGISTRY.md))

ดูสถาปัตยกรรมเต็ม: [docs/NIRVA_ARCHITECTURE.md](docs/NIRVA_ARCHITECTURE.md) · [docs/NIRVAFORGE.md](docs/NIRVAFORGE.md) (NestJS + FastAPI สำหรับงาน AI)

---

## อ่านก่อนเขียนโค้ด

| เอกสาร | ใช้เมื่อไหร่ |
|--------|-------------|
| [ECOSYSTEM_MAP.md](ECOSYSTEM_MAP.md) | repo นี้อยู่ตรงไหนใน NIRVA ecosystem |
| [NIRVACORE_V1_PLAN.md](NIRVACORE_V1_PLAN.md) | แผน monorepo (สถานะ **PAUSED — รอ audit**) |
| [standards_kb/README.md](standards_kb/README.md) | Universal Compliance Graph (ย้ายไป NirvaGov ในอนาคต) |
| [CHANGELOG.md](CHANGELOG.md) | ประวัติ v79–v81 ของ Python app |

---

## อะไรทำใน repo นี้ได้ (ปลอดภัย)

| ทำได้ | ห้าม / ไปทำที่ NirvaCore |
|-------|-------------------------|
| แก้ bug, dependency, security patch | ฟีเจอร์ใหม่ (หน้า/module ใหม่) |
| อัปเดต docs, i18n, CONTRIBUTING | RFM, Forecast, Catalog, Orders (ย้ายแล้ว) |
| ปรับ `policy_watcher`, cron scripts | Auth multi-tenant แบบ production |
| รักษา self-host / Docker ให้รันได้ | Procure logic (อยู่ NirvaProcure → NirvaCore) |

---

## Tech stack

### เดิม (repo นี้)

```
Language:   Python 3.11+
Framework:  Streamlit 1.56
Database:   SQLite (per-user ใน data/users/)
AI:         Anthropic Claude API (BYOK)
```

### ใหม่ (NirvaCore)

```
Backend:    TypeScript · NestJS 10 · Prisma · PostgreSQL 16
Frontend:   TypeScript · Next.js 14 · React 18 · TailwindCSS
```

ดู **CONTRIBUTING.md ของ nirvacore-v1** สำหรับ step-by-step สร้าง module (7 ขั้น + tests)

---

## Module ที่ย้ายเข้า NirvaCore แล้ว

| Python (NirvaSell) | NirvaCore |
|--------------------|-----------|
| `rfm.py` | `sell-analytics/rfm.service.ts` · `/sell/rfm` |
| `demand_forecast.py` | `sell-analytics/demand-forecast.service.ts` · `/sell/forecast` |
| Catalog / products | `catalog/` |
| Orders | `orders/` |
| Customers | `customers/` |
| P&L | `accounting/` |

---

## Module ใน repo นี้ — สถานะ migration

### Python-only (v80–v81) — อ้างอิง business logic ได้

| Module / หน้า | คำอธิบาย | บ้านใน ecosystem (ตาม ECOSYSTEM_MAP) |
|---------------|----------|--------------------------------------|
| `knowledge_hub.py` · `00_🧠_KnowledgeHub` | Knowledge graph องค์กร | NirvaOS / shared packages |
| `standards_kb/` · `01_📚_Standards` | One Data · Many Standards | **NirvaGov** |
| `policy_watcher.py` · `E_📋_Policies` | Marketplace fee watcher | NirvaSell → NirvaCore commerce |
| `nirva_os/` | Architecture blueprint (JSON) | NirvaCore / NirvaOS |
| `nirva_research/` | Payroll / SOP research pack | NirvaCore HR + Research |

### รอ port (ความสำคัญสูง → ต่ำ)

| Python file | คำอธิบาย | ความซับซ้อน |
|-------------|----------|------------|
| `abc_analysis.py` | ABC/Pareto สินค้า | ต่ำ |
| `sku_profit.py` · `pnl_statement.py` | กำไรต่อ SKU / P&L | กลาง |
| `promo_engine.py` · `vouchers.py` | โปรโมชั่น / คูปอง | กลาง |
| `shipping_calc.py` | ค่าส่งหลาย carrier | ต่ำ |
| `tax_report.py` · `tax_invoice.py` | ภาษี / ใบกำกับ | กลาง |
| `fulfillment.py` | Pick/pack / tracking | กลาง |
| `compliance.py` | Pre-flight marketplace rules | ต่ำ |

---

## วิธีเขียนใหม่ Python → TypeScript

### 1. อ่าน Python เดิม (reference เท่านั้น)

```bash
# ตัวอย่าง — อย่า deploy Python ใหม่
cat rfm.py
cat knowledge_hub.py
```

### 2. แปล logic — ไม่ copy-paste UI

- `pandas` / raw SQL → **Prisma queries**
- SQLite per-user → **PostgreSQL + companyId tenant**
- Streamlit page → **Next.js route + NestJS controller**
- `kh.capture(...)` → service + Prisma model ใน NirvaCore

### 3. ตัวอย่าง (RFM — ย้ายแล้ว)

**Python:**

```python
with db.conn() as c:
    rows = c.execute(
        "SELECT buyer_phone, COUNT(*), SUM(total_amount), MAX(order_date) "
        "FROM orders GROUP BY buyer_phone"
    ).fetchall()
```

**TypeScript (NirvaCore):**

```typescript
const customers = await this.prisma.order.groupBy({
  by: ['customerId'],
  where: { companyId, status: { notIn: ['CANCELLED', 'REFUNDED'] } },
  _count: { _all: true },
  _sum: { total: true },
  _max: { createdAt: true },
});
```

### 4. Checklist ก่อน PR ที่ NirvaCore

- [ ] Module + service + controller + DTO
- [ ] Prisma schema migration (ถ้ามี table ใหม่)
- [ ] Unit tests (ดู `sell-analytics` เป็นต้นแบบ)
- [ ] หน้า Next.js (ถ้ามี UI)
- [ ] อัปเดต CONTRIBUTING checklist ใน nirvacore-v1

---

## NirvaProcure

Repo **Nirvaprocure** กำลังรวมเข้า NirvaCore — ดู CONTRIBUTING.md ของ repo นั้นสำหรับ raw SQL → Prisma checklist

---

## รัน / ทดสอบ repo นี้ (maintenance)

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py --server.port 8501
python3 -m standards_kb.graph          # validate compliance graph
python3 scripts/policy_check.py        # cron policy watcher (optional)
```

---

## สรุปหนึ่งบรรทัด

**NirvaSell = หนังสืออ้างอิง + legacy app · NirvaCore = ที่เขียนต่อ**
