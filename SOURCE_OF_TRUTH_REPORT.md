# SOURCE_OF_TRUTH_REPORT.md
> Phase 2 · Part 5 + Part 8 · 2026-06-14

## Hierarchy (ตาม Phase 2)
- **Code Truth → GitHub**
- **Decision Truth → Claude**
- **Knowledge Truth → NotebookLM**
- **Workspace Truth → MacBook / Cursor**

## Source of Truth ต่อ component (เท่าที่มีหลักฐาน)
| Component | Code Truth | Decision Truth | Knowledge Truth | Workspace Truth | สรุป SoT | Confidence |
|---|---|---|---|---|---|---|
| nirva.sell | `Nirvasell` ✅ | this repo's `DECISION_LOG` | `standards_kb`/`nirva_research` (embedded) | ? (Mac) | **GitHub** (code) | Med |
| NirvaProcure | `Nirvaprocure` ✅ | repo `STATUS.md` | repo docs | Cursor (ref'd) | **GitHub** | Med |
| Mu Tea | `MUTEA` ✅ | repo README | `MUTEA/docs` | ? | **GitHub** | Med |
| NirvaCore (ERP) | `nirvacore-v1` 🔒 (ยังไม่เปิด) | ? | ? | ? | **UNRESOLVED** | Low |
| NirvaDeploy | `nirvadeploy` 🔒 | ? | ? | ? | Pending | Low |
| nirvatic | `nirvatic` 🔒 | ? | ? | ? | Pending | Low |
| NirvaGov(ISO) | *(ไม่มี repo)* | Claude | `standards_kb` | ? | กระจาย → ต้องตั้งบ้าน | Low |

## Part 8 — NirvaCore อยู่ที่ไหนจริง?
**คำถาม:** Where does NirvaCore actually live today?
**ตัวเลือก:** GitHub / Local / Cursor / Claude Artifacts / Hybrid / Unknown

**หลักฐานที่มี:**
- มี repo `nirvacore-v1` (private, TS, 6.5MB, 2 issues, active 2026-06-13) — *ยังเปิดไฟล์ไม่ได้* (scope/private)
- `nirva_os` blueprint (แนวคิด core) ฝังอยู่ใน `Nirvasell`
- decision artifacts อยู่ใน Claude/this repo
- ความเป็นไปได้ว่ามีงานบน Mac/Cursor — *ยังไม่ยืนยัน*

**ข้อสรุป:**
> ⛔ **Source of Truth ของ NirvaCore = UNRESOLVED (ยังพิสูจน์ไม่ได้)**
> หลักฐานชี้ว่า *น่าจะเป็น Hybrid* (code candidate=`nirvacore-v1` 🔒 + blueprint ฝังใน Nirvasell + decisions ใน Claude) แต่ **ยังไม่มีหลักฐานเพียงพอ** จะฟันธง — ต้องเปิด `nirvacore-v1` + audit Mac/Cursor ก่อน

**สิ่งที่ต้องมีเพื่อปิดเคส:**
1. สิทธิ์อ่าน `nirvacore-v1` (ดูว่าเป็น ERP จริง / shell ว่าง / prototype)
2. ผล `local_audit.sh` จาก Mac (มี folder nirvacore ในเครื่องไหม, ตรงกับ remote ไหม)
3. ยืนยันว่ามี deployment/ผู้ใช้จริงหรือไม่ (ตัดสิน A vs P)
