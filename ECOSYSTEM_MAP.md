# ECOSYSTEM_MAP.md
> repo จริง → โครงสร้าง NIRVA Ecosystem · 2026-06-14
> ⚠️ map จากหลักฐาน (audit แล้ว) + provisional (รอ audit) — **ไม่ใช่คำสั่งให้รวม/ย้าย**

## ภาพรวม BEST GROUP (จาก Master Prompt)
```
BEST GROUP
├── 🛡️ BEST SERVICE   (ธุรกิจจริง: Investigation, Cleaning, Security, FM, Rental, Manpower)
├── 💻 NIRVA          (Business OS: NirvaOS, NirvaCore, NirvaCloud, NirvaDeploy,
│                       NirvaGov, NirvaProcure, NirvaTrade, NirvaWealth, Academy, Research, Media)
├── 🤖 NOVA           (AI Workforce: agents, knowledge, voice, vision, studio)
├── 🌱 MUVERSE        (Consumer: Mu Tea, Living, Wellness, Academy, Retreat, Store...)
├── 🪷 SOUL           (Alternative Living: food/water/energy/emergency security)
└── 🚀 FUTURE VENTURES
```

## repo จริง → ตำแหน่งใน ecosystem
| repo (จริง) | ชั้น | map → ส่วนของ ecosystem | ความมั่นใจ |
|---|---|---|---|
| **Nirvasell** (`nirva.sell`) | A | NIRVA → commerce/seller OS (เกี่ยว NirvaOS *Commercial* / MUVERSE *Mu Store*) | 🟢 หลักฐาน |
| **Nirvaprocure** | A | NIRVA → **NirvaProcure** (procurement OS) | 🟢 หลักฐาน |
| **MUTEA** | C | MUVERSE → **Mu Tea** (brand + research KB) | 🟢 หลักฐาน |
| **nirvacore-v1** | A? | NIRVA → **NirvaCore (ERP)** — ผู้สมัคร Source of Truth | ⚪ รอ audit |
| **nirvadeploy** | A/B? | NIRVA → **NirvaDeploy** | ⚪ รอ audit |
| **nirvatic** | ? | ? (อาจ NirvaTrade / service เก่า / archive) — **ห้ามเดาจากชื่อ** | ⚪ รอ audit |

## แพ็กเกจฝังใน Nirvasell (cross-cutting, ผิดบ้าน)
| แพ็กเกจ | ชั้น | บ้านที่เหมาะ (ตาม org chart) |
|---|---|---|
| `standards_kb/` | C | **NirvaGov** (ISO) |
| `nirva_os/` (blueprint) | C/B | **NirvaCore / NirvaOS** core |
| `nirva_research/` (+payroll_engine) | C | **NirvaCore HR/Payroll** + **Nirva Research** |

## ส่วนของ ecosystem ที่ "ยังไม่มี repo จริง"
NirvaOS, NirvaCloud, NirvaGov, NirvaTrade, NirvaWealth, Academy, Media,
NOVA (ทั้งหมด), MUVERSE อื่นๆ, SOUL (ทั้งหมด), Future Ventures
→ ปัจจุบันเป็น *แนวคิด/แผน* ยังไม่มี code repo (ห้ามสร้างจนกว่าจะมีเหตุผลเชิงคุณค่า — *build only what creates value*)

> สรุป: ของจริงตอนนี้มี 6 repo · audit แล้ว 3 · ที่เหลือรอสิทธิ์ · **ยังไม่ถึงขั้นตอนวาง topology สุดท้าย**
