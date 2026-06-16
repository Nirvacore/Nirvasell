# NIRVACORE v1 — Monorepo Consolidation Plan

> **ปัญหา:** ตอนนี้มี repo กระจัดกระจายหลายตัวบน GitHub (NirvaSell, NirvaProcure,
> NirvaFleet, NirvaWealth, NIRVA Research & Docs, NirvaCore Builder,
> Nirvacore:manu, Nirvacore2, NirvaDeploy, MU TEA …) → ดูแลยาก ข้อมูลกระจาย
> ขัดกับหลัก **"One Data"** ของ Nirva เอง
>
> **เป้าหมาย:** รวมทุกอย่างเข้า **repo เดียว = `nirvacore-v1` (มีอยู่แล้ว)** โดย
> **ไม่ทิ้งงานเก่า** และเก็บประวัติ git ไว้

> ⚠️ **สถานะ: PAUSED (รอ audit)** — ตาม NIRVA MASTER COMMAND CENTER governance
> (*audit before refactor · do not merge automatically*) การ "ดูดรวม" ในแผนนี้
> **ระงับไว้ก่อน** จนกว่าจะ audit ครบทั้ง 6 repo ดู **`NIRVA_REPO_AUDIT.md`** เป็นตัวหลัก
> แผนนี้เก็บไว้เป็น *ทางเลือก topology หนึ่ง* เท่านั้น ยังไม่ใช่ข้อสรุป

---

## 0. ผลสำรวจจริง (org `Nirvacore`, 14 มิ.ย. 2026) — มีแค่ 6 repo
| repo | ภาษา | ขนาด | private? | แผน |
|---|---|---|---|---|
| **`nirvacore-v1`** | TypeScript | 6.5 MB | ✅ | **= ตัวหลัก (monorepo home)** ดูโครงสร้างภายในก่อน |
| `Nirvasell` | Python | 1.3 MB | – | → `apps/sell/` + ดึง packages ขึ้น root |
| `Nirvaprocure` | TypeScript | 1.0 MB | – | → `apps/procure/` |
| `nirvadeploy` | TypeScript | 2.3 MB | ✅ | → `apps/deploy/` |
| `nirvatic` | JavaScript | **99 MB** ⚠️ | ✅ | ทำความสะอาด node_modules ก่อน → `apps/nirvatic/` |
| `MUTEA` | – | 15 KB | – | ว่าง → ข้าม/placeholder |

> หมายเหตุสำคัญ: ชื่อในรูป (NirvaWealth, Fleet, Builder, manu, Core2,
> Research&Docs) **ไม่ใช่ repo จริงบน GitHub** — มีแค่ 6 ตัวข้างบน. และ
> `nirvacore-v1` **มีอยู่แล้ว** จึง **ไม่ต้องสร้างใหม่**.

---

## 1. ทำไมต้อง Monorepo (repo เดียว)
| Multi-repo (ตอนนี้) | Monorepo `nirvacore` (เป้าหมาย) |
|---|---|
| 10+ repo จำยาก | 1 repo จุดเดียว |
| โค้ดที่ใช้ร่วม (standards_kb, payroll engine) ต้องก๊อปไปมา | import ตรงข้าม package ได้เลย |
| เวอร์ชันไม่ตรงกัน | atomic commit ข้ามทั้งระบบ |
| ตั้ง CI/สิทธิ์ 10 รอบ | ตั้งครั้งเดียว |
| ขัดหลัก One Data | สอดคล้อง One Data |

สำหรับ **founder คนเดียว + ทีม AI (NOVA)** → monorepo ชนะขาด

---

## 2. โครงสร้างเป้าหมาย `nirvacore/`
```
nirvacore/
├── apps/                       # แอปที่รันได้ (แต่ละตัว deploy เองได้)
│   ├── sell/                   ← NirvaSell        (Streamlit reseller OS เดิม)
│   ├── procure/                ← NIRVAPROCURE
│   ├── fleet/                  ← NirvaFleet
│   ├── deploy/                 ← NirvaDeploy
│   ├── wealth/                 ← NirvaWealth Intelligence
│   ├── builder/                ← NIRVACORE BUILDER
│   └── manu/                   ← Nirvacore:manu (manufacturing)
├── packages/                   # ความรู้/engine ใช้ร่วมทุกแอป
│   ├── standards_kb/           ← (มีแล้วใน NirvaSell — ย้ายขึ้นมา)
│   ├── nirva_os/               ← (มีแล้วใน NirvaSell)
│   ├── nirva_research/         ← (มีแล้ว: payroll engine ฯลฯ)
│   └── research_docs/          ← NIRVA RESEARCH & DOCS
├── ventures/                   # ธุรกิจปลายน้ำ (รันบน nirvacore)
│   └── mu_tea/                 ← MU TEA (MUVERSE)
├── docs/                       # เอกสารรวมทั้งกลุ่ม
├── scripts/
└── README.md                   # แผนที่ของทั้งระบบ
```

> หมายเหตุ: `Nirvacore2` และ repo ที่ซ้ำ/ทดลอง → ตรวจก่อนว่ามีของจริงไหม
> ถ้าไม่มี → **archive** (ไม่ลบ แค่ปิด) เพื่อกันสับสน

---

## 3. ตารางแมป repo เก่า → ที่อยู่ใหม่
| repo เดิม | ปลายทางใน nirvacore | วิธี |
|---|---|---|
| NirvaSell | `apps/sell/` + ย้าย `packages/*` ขึ้น root | subtree |
| NIRVAPROCURE | `apps/procure/` | subtree |
| NirvaFleet | `apps/fleet/` | subtree |
| NirvaDeploy | `apps/deploy/` | subtree |
| NirvaWealth Intelligence | `apps/wealth/` | subtree |
| NIRVACORE BUILDER | `apps/builder/` | subtree |
| Nirvacore:manu | `apps/manu/` | subtree |
| NIRVA Research & Docs | `packages/research_docs/` | subtree |
| MU TEA | `ventures/mu_tea/` | subtree |
| Nirvacore2 | ตรวจสอบ → archive ถ้าว่าง | - |

---

## 4. วิธีรวมแบบเก็บประวัติ git (`git subtree`)
`git subtree` ดูดทั้ง repo (โค้ด + history) มาไว้ในโฟลเดอร์ย่อย — ไม่ทิ้งงาน

```bash
# ตัวอย่าง: ดูด NirvaProcure เข้ามาที่ apps/procure/
git subtree add --prefix=apps/procure \
  https://github.com/Nirvacore/NirvaProcure.git main
```
ดูสคริปต์อัตโนมัติที่ [`scripts/consolidate_to_nirvacore.sh`](scripts/consolidate_to_nirvacore.sh)

---

## 5. Runbook — ทำตามทีละขั้น
**ฝั่งคุณ (บน GitHub — กดเมาส์):**
1. สร้าง repo ใหม่ชื่อ **`nirvacore`** (เปล่าๆ ไม่ต้อง init README ก็ได้) ใน org `Nirvacore`
2. (ทางเลือก) เพิ่ม repo เก่าทั้งหมด + `nirvacore` เข้าสิทธิ์ของ session นี้ เพื่อให้ผมรันให้ได้

**ฝั่งผม (รันให้ได้ถ้าได้สิทธิ์):**
3. clone `nirvacore`, วางโครงสร้าง `apps/ packages/ ventures/ docs/`
4. รัน `scripts/consolidate_to_nirvacore.sh` → subtree ดูดทุก repo เข้าตำแหน่ง
5. ย้าย `packages/*` (standards_kb, nirva_os, nirva_research) จาก apps/sell ขึ้น root
6. แก้ import paths + เพิ่ม README รวม + ตั้ง CI ครั้งเดียว
7. commit + push + เปิด PR

**หลังเสร็จ:**
8. repo เก่าทุกตัว → กด **Archive** บน GitHub (ไม่ลบ เก็บไว้อ้างอิง ประวัติอยู่ครบใน nirvacore แล้ว)

---

## 6. สิ่งที่ผมต้องการจากคุณเพื่อลงมือ
ตอนนี้สิทธิ์ผมเข้าถึงได้แค่ `nirvacore/nirvasell` — ขอ **อย่างใดอย่างหนึ่ง**:
- **(ก)** คุณสร้าง repo `nirvacore` + เพิ่ม repo เก่าเข้าสิทธิ์ session → ผมรันทั้งหมดให้
- **(ข)** คุณรัน `scripts/consolidate_to_nirvacore.sh` เองบนเครื่อง (ผมเขียน + อธิบายทุกบรรทัดให้)

> ⚠️ **ยังไม่ต้องลบ repo เก่าใดๆ** จนกว่าจะ subtree เข้ามาครบและยืนยันว่างานอยู่ครบ
> "เก็บก่อน รวมทีหลัง ค่อย archive" — ไม่มีอะไรหาย

---

## 7. งานที่ทำไปแล้ว (อยู่ใน NirvaSell / PR #8) จะกลายเป็น
- `apps/sell/` (แอป Streamlit)
- `packages/standards_kb/`, `packages/nirva_os/`, `packages/nirva_research/`
ทั้งหมดย้ายเข้าโครงใหม่ได้ทันที — **ไม่ต้องเขียนใหม่**
