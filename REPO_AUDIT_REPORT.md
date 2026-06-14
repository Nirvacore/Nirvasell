# REPO_AUDIT_REPORT.md
> NIRVA MASTER COMMAND CENTER · Audit Round 1 · 2026-06-14
> หลักการ: *Reality before imagination · Audit before refactor · ไม่เดาจากชื่อ · ใช้หลักฐาน*
> สถานะ: **AUDIT ONLY** — ยังไม่ merge / rename / archive / delete ใดๆ

## วิธีเก็บหลักฐาน
- Public repo (`Nirvasell`, `Nirvaprocure`, `MUTEA`): **clone ตรงผ่าน git แล้วเปิดไฟล์จริง** ✅
- Private repo (`nirvacore-v1`, `nirvadeploy`, `nirvatic`): **ยังไม่มีสิทธิ์** → ยังไม่ audit (รอเพิ่ม scope)
- github MCP scope ของ session = `nirvacore/nirvasell` เท่านั้น (ตัวอื่นต้อง clone หรือเพิ่ม scope)

---

## 1) Nirvasell — ชั้น **A (Production System)** ✅ ยืนยันด้วยหลักฐาน
| ด้าน | หลักฐาน |
|---|---|
| ตัวตน | `nirva.sell` — "ระบบปฏิบัติการสำหรับแม่ค้าออนไลน์" (README) |
| ขนาด | working tree 5.7MB · .git 2.0MB · **17 commits** |
| โค้ด | **298 ไฟล์ .py** · 37 .md · 21 .json · Streamlit, 140 หน้า, 19 ภาษา, MIT |
| ขอบเขต | stock / order / CRM / finance / analytics / invoice / live-sell |
| 🚩 Risk | **ไม่มี** node_modules/dist/build tracked · มีแค่ `.env.example`, `.streamlit/secrets.toml.example` = **template ปลอดภัย** |
| หมายเหตุ | ฝัง 3 แพ็กเกจที่ไม่ใช่งานค้าขาย: `standards_kb/`(C), `nirva_os/`(C/B), `nirva_research/`+payroll(C) → ดู DECISION_LOG |

## 2) Nirvaprocure — ชั้น **A (Production System)** ✅ ยืนยันด้วยหลักฐาน
| ด้าน | หลักฐาน |
|---|---|
| ตัวตน | "AI-augmented procurement OS for Thailand & ASEAN SMEs" (README) |
| ขนาด | working tree 5.1MB · .git 1.4MB · **75 commits** · active (commit ล่าสุด 2026-06-14) |
| โค้ด | **135 .ts + 49 .tsx** · 30 .md · full-stack จริง |
| สถาปัตยกรรม | `backend/`(Node+TS, fly.toml) · `frontend/`(Next.js 14) · `mobile/`(Flutter, 26 จอ) · `api/`(openapi.yaml) · `database/`(SQL schema phase1-5: gov/stock/2fa/portal/anomaly/budget) · `design-system/` |
| สถานะภายใน | STATUS.md: "~230 files, 90+ tasks shipped, typecheck clean, ready for pilot + Fly.io" |
| 🚩 Risk | **ไม่มี** node_modules/dist tracked · มีแค่ `backend/.env.example`, `frontend/.env.example` = template ปลอดภัย · `frontend/package-lock.json` = ปกติ |

## 3) MUTEA — ชั้น **C (Knowledge / Research)** ✅ *(แก้จากที่เดาว่า D-placeholder — ผิด!)*
| ด้าน | หลักฐาน |
|---|---|
| ตัวตน | "Mu Tea — A gentle lifestyle brand... Japanese tea / mindfulness" + "research knowledge base" (commit msg) |
| ขนาด | 264KB · **2 commits** · เอกสารล้วน |
| เนื้อหา | **7 ไฟล์ .md** ใน `docs/brand/` + `docs/research/` (4 research reports: matcha, supply-chain, hojicha, Thai import regulatory) |
| โค้ด | **ไม่มีโค้ดเลย** → เป็น knowledge base ไม่ใช่ระบบ |
| 🚩 Risk | ไม่มี |
| หมายเหตุสำคัญ | README ระบุชัด: *"Anti-overengineering Rule: Do NOT build ERP. Do NOT over-engineer."* → ห้ามเอาไปยัดเป็นระบบ |

---

## 4) ยังไม่ได้ audit (รอสิทธิ์ private)
| repo | ภาษา/ขนาด (metadata) | ทำไมต้องสอบ |
|---|---|---|
| `nirvacore-v1` | TS / 6.5MB | **ผู้สมัคร Source of Truth ของ NirvaCore** — ต้องเปิดดูก่อนชี้ขาด |
| `nirvadeploy` | TS / 2.3MB | desc: Thai PaaS · MCP · Stripe+BTC · PDPA |
| `nirvatic` | JS / **99MB** ⚠️ | ใหญ่ผิดปกติ — สงสัย node_modules/build artifact tracked → **flag Risk ล่วงหน้า** รอยืนยัน |

---

## 5) สรุป Risk (ภาพรวม)
| repo | Risk | ระดับ |
|---|---|---|
| Nirvasell | สะอาด (มีแค่ .env.example) | 🟢 |
| Nirvaprocure | สะอาด (มีแค่ .env.example) | 🟢 |
| MUTEA | สะอาด | 🟢 |
| nirvatic | สงสัย 99MB = artifact tracked | 🔴 รอยืนยัน (ยังไม่แตะ) |
| nirvacore-v1 / nirvadeploy | ยังไม่ทราบ | ⚪ รอ audit |

## 6) Source of Truth — NirvaCore
> **ยังชี้ขาดไม่ได้** ด้วยหลักฐาน ณ ตอนนี้
> 3 repo ที่ audit แล้วต่างเป็น *ผลิตภัณฑ์ของตัวเอง* (nirva.sell, NirvaProcure) หรือ *knowledge* (Mu Tea) — ไม่มีตัวใดเป็น "NirvaCore ERP" โดยตรง
> ผู้สมัครหลักคือ **`nirvacore-v1`** (private, locked) → **ต้องได้สิทธิ์ก่อนจึงยืนยัน**
