# LOCAL_CONFLICT_REPORT.md
> Phase 2A · duplicate/conflict detection (FLAG only — ห้าม resolve) · 2026-06-14
> ฐาน: รายการโฟลเดอร์ที่ผู้ใช้รายงาน · ยืนยันด้วย `scripts/local_audit.sh` · Severity: Low/Med/High/Critical

## ⚠️ หลักการ: "อาจซ้ำ" ≠ "ซ้ำ"
ชื่อคล้ายกันไม่ได้แปลว่าเป็นสำเนากัน — อาจเป็น active/backup/archive/experiment คนละบทบาท
**flag ไว้ ไม่ตัดสิน** จนกว่าจะเทียบ git/last-commit/diff จริง

## กลุ่มที่ต้องสอบ (possible duplicates)
| # | กลุ่ม | สมาชิก (local) | repo ที่เกี่ยว | Severity | ทำไมต้องสอบ |
|---|---|---|---|---|---|
| L1 | **CORE** | `~/nirvacore` · `~/NIRVA` · `~/nirva-backup-*` · `~/nirva-archive` | `nirvacore-v1` | **High** | กระทบ Source of Truth ของหัวใจ ERP — ต้องรู้ตัวจริง vs backup |
| L2 | **DEPLOY** | `~/Downloads/nirva deploy` · `~/Downloads/deploy` · `~/Downloads/nirva_deploy.zip` | `nirvadeploy` | **High** | อยู่ใน Downloads + มี zip = เสี่ยงสับสนตัว production |
| L3 | **CLAUDE** | `~/Claude` · `~/Documents/Claude` | – | **Medium** | Decision Truth อาจกระจาย 2 ที่ → ขัดกันได้ |
| L4 | **MU-TEA** | `~/mu-tea` · repo `MUTEA` | `MUTEA` | **Low** | local อาจ ahead/behind remote |
| L5 | **WEALTH (orphan)** | `~/nirvawealth` | **ไม่มี repo** | **Medium** | มี local แต่ไม่มี GitHub → ยังไม่ backup บน cloud (เสี่ยงสูญ) |
| L6 | **GOV (orphan doc)** | `~/Downloads/NirvaGovTH Dev Spec.docx` · `~/Doc.for.ERP` | ไม่มี repo NirvaGov | **Medium** | knowledge ลอย ไม่มีบ้าน |

## ฟิลด์ตัดสิน (ต้องได้จาก Mac เพื่อปิด flag)
ต่อสมาชิกแต่ละตัว: `last_commit_date`, `branch`, `ahead/behind upstream`, `uncommitted count`, จำนวนไฟล์โค้ด, `node_modules?`
→ ตัวที่ **commit ล่าสุดที่สุด + เชื่อม remote + uncommitted สมเหตุผล** = ผู้สมัคร "ตัวจริง"; ตัวที่ชื่อ backup/archive + เก่า = ผู้สมัคร D

## สถานะ
- ❌ ยังไม่ resolve กลุ่มใด (ตามกฎ)
- ⏭️ ปิด L1 ก่อน (Phase 2B "Find the Heart") → ดู HEART_REPORT.md
