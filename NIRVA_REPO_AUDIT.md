# NIRVA Repository Audit Register
> ออกโดย **NIRVA MASTER COMMAND CENTER** · 2026-06-14
> หลักการ: *Reality before imagination · Audit before refactor · Preserve before replacing · Do not merge automatically · Use evidence*

จัดชั้น (Repository Rules):
**A** = Production System · **B** = Reusable Product · **C** = Knowledge/Research · **D** = Archive/Placeholder

---

## 1. ขอบเขตหลักฐาน (สำคัญ — อ่านก่อน)
- Session นี้เข้าถึงได้จริง **เฉพาะ `Nirvacore/Nirvasell`** (อ่าน source ได้เต็ม)
- อีก 5 repo อ่าน source **ไม่ได้** (scope ปิด) → จัดชั้นจาก **metadata เท่านั้น** = *provisional, ต้อง audit ซ้ำ*
- ❌ ยังไม่ merge / ไม่ refactor repo ใดทั้งสิ้น จนกว่าจะ audit ครบด้วยหลักฐาน

---

## 2. ทะเบียน 6 repo (org Nirvacore)

| # | repo | ภาษา/ขนาด | ชั้น | หลักฐาน | map → ecosystem |
|---|---|---|---|---|---|
| 1 | **Nirvasell** | Python / 1.3MB | **A** ✅ยืนยัน | อ่านเต็ม: `nirva.sell` "OS แม่ค้าออนไลน์" 140 หน้า 19 ภาษา MIT, 298 ไฟล์ .py, ~150 โมดูล (stock/order/CRM/finance/analytics) | NirvaOS *Commercial/Operations* · ค้าขาย |
| 2 | **nirvacore-v1** | TS / 6.5MB 🔒 | A (provisional) | metadata: active, 2 issues, โค้ดเยอะสุดฝั่ง core | **NirvaCore (ERP)** |
| 3 | **nirvadeploy** | TS / 2.3MB 🔒 | A/B (provisional) | desc: "Thai-first PaaS · MCP · Stripe+BTC · PDPA" | **NirvaDeploy** |
| 4 | **Nirvaprocure** | TS / 1.0MB | A/B (provisional) | ชื่อ + active | **NirvaProcure** |
| 5 | **nirvatic** | JS / **99MB** 🔒 | ⚠️ ต้องสอบ | เก่าสุด (2025-07), desc แค่ "Service", ใหญ่ผิดปกติ (น่าจะมี node_modules) → อาจเป็น **D-Archive** หรือ service เก่าจริง | ? (อาจ NirvaTrade / legacy) |
| 6 | **MUTEA** | – / 15KB | **D** (placeholder) | ว่าง 15KB จองชื่อ | MUVERSE → **Mu Tea** |

---

## 3. สิ่งที่พบใน Nirvasell ที่ต้องตัดสินใจ (One source of truth)
Nirvasell เป็นแอปค้าขาย (A) แต่มี **3 แพ็กเกจฝังอยู่ที่ไม่ใช่งานค้าขาย** (ถูกใส่ไว้ใน session ก่อน):

| แพ็กเกจใน Nirvasell | เนื้อหา | ชั้น | บ้านที่ควรอยู่ |
|---|---|---|---|
| `standards_kb/` | ISO/มาตรฐาน + knowledge graph (`graph.py`, `build_reports.py`) | **C** | **NirvaGov** (ISO) |
| `nirva_os/` | blueprint ของ OS (`blueprint.py`) | C/B | **NirvaCore / NirvaOS** core |
| `nirva_research/` | research + **payroll engine** (`payroll_engine.py`, `research.py`) | **C** | **NirvaCore HR/Payroll** + **Nirva Research** |

➡️ คำแนะนำ: *ไม่ลบ* แต่พิจารณา **แยกออก (extract, เก็บ git history)** ไปยังบ้านที่ถูกต้อง เพื่อเลี่ยง duplication และให้ commerce app โฟกัสงานค้าขาย — **รอ audit core ก่อนค่อยย้าย**

---

## 4. Next Actions (ตามลำดับ — ไม่ข้าม)
1. **[ต้องการสิทธิ์]** เพิ่ม scope ให้ session อ่าน: `nirvacore-v1`, `nirvadeploy`, `Nirvaprocure`, `nirvatic`
2. Audit แต่ละตัวด้วยหลักฐาน (โครงสร้าง, README, มี node_modules/secret ไหม) → ยืนยันชั้น A/B/C/D
3. ตัดสิน `nirvatic` (99MB): real service → cleanup ; legacy → **D-Archive**
4. วาง topology สุดท้าย (หลาย repo มีระเบียบ หรือ monorepo) — **ตัดสินหลัง audit ครบเท่านั้น**
5. ค่อยดำเนินการย้าย/รวม โดยเก็บ git history ทุกครั้ง

> ⛔ ห้าม: เดาจากชื่อ, merge อัตโนมัติ, ลบของก่อนยืนยันสำเนา
