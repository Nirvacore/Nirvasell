# BEST_RISK_REGISTER.md
> BEST GROUP Back Office · 2026-06-14 · Severity: 🟢Low 🟡Med 🟠High 🔴Critical
> ⛔ flag เท่านั้น — ไม่แก้/ไม่ย้าย/ไม่ลบ

| # | Risk | Severity | หลักฐาน/เหตุผล | Mitigation (เสนอ — ยังไม่ทำ) |
|---|---|---|---|---|
| B1 | **09_HR มีข้อมูล PDPA** (แฟ้มพนักงาน/สัญญา/สวัสดิการ) | 🔴 | นโยบาย PDPA | จำกัดสิทธิ์เข้าถึง · เข้ารหัส · ไม่ push ขึ้น cloud/GitHub · ไม่ log เนื้อหา |
| B2 | **ไม่พบที่อยู่ 03_FINANCE / 09_HR ชัดเจน** (เลขนำหน้าข้าม 1,3) | 🟠 | registry: ไม่มี folder ชื่อตรง | สืบว่าฝังใน `ERP`/`4Document` ก่อนสร้างโครง · ห้ามเดา |
| B3 | **NIRVAPROCURE ปนใน BEST** | 🟠 | separation policy | แยกไป NIRVA-HQ (ขั้นต่างหาก) ไม่ดูดเข้า BEST-HQ |
| B4 | **บันทึกลูกค้า (6Job) สูญ = เสียหายสัญญา/กฎหมาย** | 🔴 | งานลูกค้า AOT/BOT/รพ. | backup ก่อนแตะ · ห้ามลบ · ทำ release backup ถาวร |
| B5 | **สัญญา/ISO/ราชการ (4Document) สูญ** | 🔴 | เอกสารผูกพันกฎหมาย | เช่นเดียว B4 |
| B6 | **โฟลเดอร์ชื่อแปลก/encoding เสีย** | 🟡 | นโยบาย unknown folder | flag + รอ review · ห้าม rename/move/delete (ดู BEST_UNKNOWN_FOLDER_REPORT) |
| B7 | **`Backup` เดิมอาจไม่มี retention/verify** | 🟡 | ชื่อ folder เดียว | ตรวจว่าครบ/อ่านได้ ก่อนพึ่งพา |
| B8 | **ทำจาก cloud มองไม่เห็นไฟล์จริง** | 🟡 | environment | ใช้ `best_audit.sh` บน Mac ก่อนทุกการตัดสิน |
| B9 | **ถือว่าโฟลเดอร์ทิ้งได้** | 🔴 | คำเตือนผู้ใช้ | สมมุติฐาน "ทุกอย่างคือบันทึกธุรกิจ active" จนพิสูจน์ตรงข้าม |

## ลำดับจัดการ (ก่อนลงมือใดๆ)
1. B1/B4/B5 (Critical) — ของผูกพันกฎหมาย/PDPA: backup + จำกัดสิทธิ์ก่อน
2. B2/B3 (High) — หาที่อยู่การเงิน/HR + แยก NIRVAPROCURE
3. B6/B7/B8/B9 — สืบ/ยืนยันด้วย audit
