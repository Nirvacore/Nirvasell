# BEST_UNKNOWN_FOLDER_REPORT.md
> BEST GROUP Back Office · 2026-06-14
> นโยบาย: โฟลเดอร์ชื่อไม่ชัด/encoding เสีย → **flag · report · request review** · ❌ ไม่ rename ❌ ไม่ move ❌ ไม่ delete

## สถานะปัจจุบัน
- รายการที่ผู้ใช้ยืนยัน (ERP, 2Store, 4Document, 5Operation, 6Job, 7Marketing, 8Car, Backup, MAC, NIRVAPROCURE) = **ชื่อชัดเจน ไม่ใช่ unknown**
- ผมรันบน cloud → **ยังสแกนหา unknown folder จริงไม่ได้** (ตัวอย่างในโจทย์ `}|azA+}{`, `?":{//13…` เป็นตัวอย่างเฉย ยังไม่ยืนยันว่ามีจริง)

## วิธีตรวจจับจริง (รัน `best_audit.sh` บน Mac)
สคริปต์จะ flag โฟลเดอร์ที่:
- มีอักขระไม่ใช่ ASCII/ไทยปกติ หรือสัญลักษณ์แปลก (`{ } | ? " : / \ *`)
- ชื่อว่าง/ขึ้นต้นด้วยช่องว่าง/จุด
- encoding เสีย (อ่านเป็น `?` หรือ replacement char)

## ตารางผล (รอเติมจาก Mac)
| Unknown folder (raw) | path | ขนาด | last modified | มีไฟล์ข้างใน? | การกระทำ |
|---|---|---|---|---|---|
| _(รอผล best_audit.sh)_ | | | | | **flag → request review เท่านั้น** |

## กฎเหล็ก
> โฟลเดอร์ unknown = **ไม่แตะ** จนกว่าผู้ใช้ review ทีละตัว · อาจเป็นบันทึกธุรกิจสำคัญที่ชื่อพังเฉยๆ
