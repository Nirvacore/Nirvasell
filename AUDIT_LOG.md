# AUDIT_LOG.md
> NIRVA MASTER COMMAND CENTER · structured audit log · 2026-06-14
> ฟิลด์ทุก entry: **Access method · Evidence path · Findings · Risk · Classification (ชั่วคราว) · Confidence**
> ขอบเขต: *audit เท่านั้น* — ไม่แก้ไฟล์ต้นทาง / ไม่ merge / rename / archive / delete

Access method legend: `MCP` = github MCP · `git-clone` = clone ตรง · `denied` = scope ปฏิเสธ · `failed` = network/auth ล้ม · `pending` = รอสิทธิ์
Confidence legend: **High** = เปิดไฟล์จริงครบ · **Medium** = เปิดบางส่วน · **Low** = metadata เท่านั้น · **None** = ยังเข้าไม่ได้

---

## ENTRY 1 — Nirvasell
- **Access method:** `MCP` ✅ (get_file_contents `/` สำเร็จ — payload 86KB ใหญ่เกินจอแต่คืนครบ) + `git-clone`/local (working dir)
- **Evidence path:** `/home/user/Nirvasell/` (working tree, 17 commits) · MCP dump: `…/tool-results/mcp-github-get_file_contents-1781424017689.txt`
- **Findings:**
  - `nirva.sell` = "ระบบปฏิบัติการสำหรับแม่ค้าออนไลน์" (README), Streamlit, 140 หน้า, 19 ภาษา, MIT
  - **298 ไฟล์ .py** · 37 .md · 21 .json · domains: stock/order/CRM/finance/analytics/invoice/live-sell
  - ฝัง 3 แพ็กเกจ cross-cutting: `standards_kb/` (ISO+graph), `nirva_os/` (blueprint), `nirva_research/` (research + `payroll_engine.py`)
- **Risk:** 🟢 ไม่มี node_modules/dist/build tracked · มีแค่ `.env.example` + `.streamlit/secrets.toml.example` = template ปลอดภัย (ไม่ใช่ secret จริง)
- **Classification (ชั่วคราว):** **A (Production)** — core commerce product. (3 แพ็กเกจฝัง = C, แยกภายหลัง)
- **Confidence:** **High**

## ENTRY 2 — Nirvaprocure
- **Access method:** `MCP` → `denied` (scope=nirvasell) → fallback `git-clone` ✅
- **Evidence path:** `/tmp/_audit/Nirvaprocure/` (75 commits, depth-50 clone)
- **Findings:**
  - "AI-augmented procurement OS for Thailand & ASEAN SMEs" (README)
  - full-stack: `backend/`(Node+TS, fly.toml) · `frontend/`(Next.js 14) · `mobile/`(Flutter, 26 จอ) · `api/`(openapi.yaml) · `database/`(SQL schema phase1-5) · `design-system/`
  - **135 .ts + 49 .tsx** · STATUS.md: "~230 files, 90+ tasks shipped, typecheck clean, ready for pilot + Fly.io"
- **Risk:** 🟢 ไม่มี node_modules/dist tracked · มีแค่ `backend/.env.example`, `frontend/.env.example` = template · `frontend/package-lock.json` = ปกติ
- **Classification (ชั่วคราว):** **A (Production)**
- **Confidence:** **High**

## ENTRY 3 — MUTEA
- **Access method:** `MCP` → `denied` (scope=nirvasell) → fallback `git-clone` ✅
- **Evidence path:** `/tmp/_audit/MUTEA/` (2 commits)
- **Findings:**
  - "Mu Tea — gentle lifestyle brand / Japanese tea / mindfulness" + "research knowledge base" (commit msg)
  - **เอกสารล้วน 7 .md** ใน `docs/brand/` + `docs/research/` (4 research reports: matcha / supply-chain / hojicha-genmaicha / Thai import regulatory) — **ไม่มีโค้ด**
  - README สั่งชัด: "Anti-overengineering Rule: Do NOT build ERP"
- **Risk:** 🟢 ไม่มี
- **Classification (ชั่วคราว):** **C (Knowledge/Research)** *(แก้จากเดา D — หลักฐานชี้ C)*
- **Confidence:** **High**

---

## ENTRY 4 — nirvacore-v1  ⚠️ ACCESS LIMITATION
- **Access method:** `MCP` → `denied` (scope=nirvasell) · `git-clone` → `pending` (private, ต้อง auth/scope)
- **Evidence path:** *(ยังไม่มี — ยังไม่เปิดไฟล์)* · metadata: TS, 6.5MB, private, 2 issues, active
- **Findings:** ⛔ **ยังไม่ทราบ** — ห้ามสรุปว่าว่าง/มีของ จนกว่าจะเปิดไฟล์จริง
- **Risk:** ⚪ ยังประเมินไม่ได้
- **Classification (ชั่วคราว):** A? (ผู้สมัคร Source of Truth ของ NirvaCore)
- **Confidence:** **None** (Access Limitation)

## ENTRY 5 — nirvadeploy  ⚠️ ACCESS LIMITATION
- **Access method:** `MCP` → `denied` · `git-clone` → `pending` (private)
- **Evidence path:** *(ยังไม่มี)* · metadata: TS, 2.3MB, private · desc "Thai PaaS · MCP · Stripe+BTC · PDPA"
- **Findings:** ⛔ ยังไม่ทราบ
- **Risk:** ⚪ ยังประเมินไม่ได้
- **Classification (ชั่วคราว):** A/B?
- **Confidence:** **None** (Access Limitation)

## ENTRY 6 — nirvatic  ⚠️ ACCESS LIMITATION + 🔴 PRE-FLAG
- **Access method:** `MCP` → `denied` · `git-clone` → `pending` (private)
- **Evidence path:** *(ยังไม่มี)* · metadata: JS, **99MB**, private, เก่าสุด (2025-07), desc "Service"
- **Findings:** ⛔ ยังไม่ทราบ — แต่ 99MB ผิดปกติมาก
- **Risk:** 🔴 **pre-flag** สงสัย artifact/node_modules ถูก track (รอเปิดยืนยัน — ยังไม่แตะ)
- **Classification (ชั่วคราว):** ? (อาจ A-service / D-archive)
- **Confidence:** **None** (Access Limitation)

---

## สรุป Access
| repo | MCP | git-clone | ผล | Confidence |
|---|---|---|---|---|
| Nirvasell | ✅ | ✅ local | audit สำเร็จ | High |
| Nirvaprocure | denied | ✅ | audit สำเร็จ | High |
| MUTEA | denied | ✅ | audit สำเร็จ | High |
| nirvacore-v1 | denied | pending | **Access Limitation** | None |
| nirvadeploy | denied | pending | **Access Limitation** | None |
| nirvatic | denied | pending | **Access Limitation** | None |

> 3/6 audit ครบด้วยหลักฐาน · 3/6 ติด Access Limitation (private) — **ไม่ถือว่าว่าง** เป็นแค่ยังเข้าไม่ถึง
> ขั้นต่อไป: ผู้ใช้เพิ่มสิทธิ์ private 3 ตัว → audit ต่อ → ปิด Source of Truth (D-003)
