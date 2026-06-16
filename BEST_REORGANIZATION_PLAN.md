# BEST_REORGANIZATION_PLAN.md
> BEST GROUP Back Office · 10-Year Structure · 2026-06-14
> **PROPOSAL ONLY — DRY_RUN=1 · ไม่ execute · รออนุมัติ**
> กฎ: backup ก่อน · ไม่ลบ/ทับ/เปลี่ยนชื่ออัตโนมัติ · ไม่ย้าย SoT โดยไม่อนุมัติ · DRY-RUN เสมอ · ออกรายงานก่อนลงมือ

## โครงเป้าหมาย `~/BEST-HQ/`
```
BEST-HQ
├── 01_ERP          # ERP exports (payroll/attendance/บัญชี/รายงานผู้บริหาร)
├── 02_STORE        # คลัง/สินทรัพย์/ยูนิฟอร์ม/อุปกรณ์/นับสต็อก
├── 03_FINANCE      # AP/AR/bank/ภาษี/ใบแจ้งหนี้/ใบเสร็จ
├── 04_DOCUMENT     # สัญญา/ISO/PDPA/tender/ราชการ/กฎหมาย
├── 05_OPERATION    # checklist/QC/รายงานหัวหน้า/ตรวจ/incident
├── 06_JOB          # งานลูกค้า (ดูโครงย่อยล่าง)
├── 07_MARKETING    # profile/นำเสนอ/ข้อเสนอ/โซเชียล/แคมเปญ/ดีไซน์
├── 08_CAR          # ทะเบียน/ประกัน/ซ่อม/GPS/น้ำมัน/อุบัติเหตุ
├── 09_HR           # แฟ้มพนักงาน/สัญญาจ้าง/สวัสดิการ/อบรม/ประเมิน  ← PDPA
├── 10_PROCUREMENT  # PR/PO/vendor/ใบเสนอราคา/ใบส่งของ
├── 11_IT           # device/license/MAC/network/install/config
├── 12_MANAGEMENT   # บอร์ด/กลยุทธ์/นโยบาย/แผนปี/org chart
└── 99_BACKUP       # Daily / Weekly / Monthly / Releases
```
### โครงย่อย `06_JOB/`
```
06_JOB/{AOT, BOT, Government, Hospital, Commercial, Other_Clients}/
  └── (ต่อลูกค้า): Contracts, Reports, Payroll_refs, Photos, Communications
```

## Mapping (user-attested → BEST-HQ)
| Current | → BEST-HQ | Risk | หมายเหตุ |
|---|---|---|---|
| `ERP` | `01_ERP` | 🔴 | mission-critical · backup ก่อน |
| `2Store` | `02_STORE` | 🟡 | |
| `4Document` | `04_DOCUMENT` | 🔴 | มีสัญญา/กฎหมาย/ISO — สำคัญ |
| `5Operation` | `05_OPERATION` | 🟡 | |
| `6Job` | `06_JOB` | 🔴 | บันทึกลูกค้า — ห้ามสูญ |
| `7Marketing` | `07_MARKETING` | 🟢 | |
| `8Car` | `08_CAR` | 🟡 | |
| `Backup` | `99_BACKUP` | 🟡 | จัด retention |
| `MAC` | `11_IT` | 🟢 | |
| `NIRVAPROCURE` | 🚫 **NIRVA-HQ** (ไม่ใช่ BEST) | 🔴 | separation policy |

## NIRVA Separation Policy (บังคับ)
- **BEST-HQ** = ปฏิบัติการธุรกิจ · **NIRVA-HQ** = ผลิตภัณฑ์เทคโนโลยี → **ห้ามปน**
- NIRVA-HQ ครอบคลุม: NirvaCore, NirvaDeploy, NirvaProcure, NirvaGov, NirvaWealth, NirvaMedia, Nova, MuVerse, Soul
- ดังนั้น `NIRVAPROCURE` ในรายการ BEST → ย้ายไป NIRVA-HQ (ขั้นแยก, ไม่ทำในแผน BEST)

## ลำดับเมื่ออนุมัติ (จะสร้าง execution script ทีหลัง)
1. รัน `best_audit.sh` (Mac) → เติมหลักฐาน + ตรวจ unknown folders
2. ทบทวน BEST_RISK_REGISTER + BEST_UNKNOWN_FOLDER_REPORT
3. `best_backup.sh` (DRY-RUN → EXECUTE)
4. **ขออนุมัติ** → ผมจึงสร้าง `best_reorg.sh` (ตอนนี้ยังไม่สร้างตาม Execution Policy)
