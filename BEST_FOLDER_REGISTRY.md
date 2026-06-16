# BEST_FOLDER_REGISTRY.md — BEST GROUP Back Office Inventory
> BEST GROUP + NIRVA MASTER COMMAND CENTER · 2026-06-14
> ⚠️ บันทึกธุรกิจจริง — **ห้ามถือว่าอะไรทิ้งได้** · discovery only

## แหล่งหลักฐาน & ข้อจำกัด
- รายการนี้ = **user-attested** (ผู้ใช้ยืนยันชื่อโฟลเดอร์) — ผมรันบน cloud VM ยังเปิดไฟล์จริงไม่ได้
- field เทคนิค (last modified / ขนาด / git / จำนวนไฟล์) = **PENDING** → รัน `scripts/best_audit.sh` บน Mac
- Confidence ทุกแถว = **Low–Med** (จากชื่อ + การยืนยัน)

## ทะเบียนโฟลเดอร์ปัจจุบัน → ปลายทาง BEST-HQ
| Current folder | หน้าที่ (ประเมิน) | → BEST-HQ | โดเมน | หมายเหตุ | Conf |
|---|---|---|---|---|---|
| `ERP` | ERP exports (payroll/บัญชี/รายงาน) | `01_ERP` | BEST | mission-critical | Med |
| `2Store` | คลัง/พัสดุ/ยูนิฟอร์ม | `02_STORE` | BEST | | Med |
| `4Document` | เอกสารองค์กร (สัญญา/ISO/PDPA/ราชการ) | `04_DOCUMENT` | BEST | | Med |
| `5Operation` | จัดการปฏิบัติการ (QC/checklist/incident) | `05_OPERATION` | BEST | | Med |
| `6Job` | งานลูกค้า (AOT/BOT/รพ./ฯลฯ) | `06_JOB` | BEST | จัดตามลูกค้า | Med |
| `7Marketing` | การตลาด/ขาย | `07_MARKETING` | BEST | | Med |
| `8Car` | ทะเบียนรถ/ประกัน/ซ่อม | `08_CAR` | BEST | | Med |
| `Backup` | สำรอง | `99_BACKUP` | BEST | จัด retention | Med |
| `MAC` | เอกสาร/ค่าเครื่อง IT | `11_IT` | BEST | | Low |
| `NIRVAPROCURE` | ผลิตภัณฑ์เทคโนโลยี | **→ NIRVA-HQ** `02_PRODUCTS/NirvaProcure` | **NIRVA** | 🔴 **ห้ามปนใน BEST-HQ** (separation policy) | Med |

## หมวดปลายทางที่ "ยังไม่มีโฟลเดอร์ต้นทางชัด" (ต้องสืบ — ห้ามเดา)
| BEST-HQ | สถานะ | คำถามที่ต้องตอบ |
|---|---|---|
| `03_FINANCE` | ❓ ไม่พบ folder ชื่อตรง | บันทึกการเงิน/บัญชี/ภาษี อยู่ใน `ERP` หรือ `4Document`? |
| `09_HR` | ❓ ไม่พบ folder ชื่อตรง | แฟ้มพนักงาน/สัญญาจ้าง อยู่ที่ไหน? (PDPA!) |
| `10_PROCUREMENT` | ❓ | PR/PO/vendor อยู่ใน `2Store`/`4Document`? (ระวังสับสนกับ NIRVAPROCURE = คนละอัน) |
| `12_MANAGEMENT` | ❓ | เอกสารบอร์ด/กลยุทธ์/นโยบาย อยู่ที่ไหน? |

> สังเกต: เลขนำหน้าเดิมข้าม 1 และ 3 (มี 2,4,5,6,7,8) → การเงิน(3) อาจถูกฝังที่อื่น = **ความเสี่ยงต้องสืบ** (ดู BEST_RISK_REGISTER)

## ฟิลด์ที่รอจาก `best_audit.sh`
last modified · ขนาด · จำนวนไฟล์/ชนิด · .git? · มีไฟล์ sensitive (PDPA)? · โฟลเดอร์ชื่อแปลก/encoding เสีย
