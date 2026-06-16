# REPO_REGISTRY.md
> ทะเบียน repo อย่างเป็นทางการ · org `Nirvacore` · 2026-06-14
> ชั้น (refined — business dependency): **A**=Production (มีลูกค้า/ธุรกิจพึ่งพา) · **B**=Reusable Product (pre-production) · **C**=Research/Venture/Exploration · **D**=Archive
> 🟢 audit แล้ว (หลักฐานจริง) · ⚪ รอ audit (สิทธิ์ private)

| # | repo | visibility | ภาษา | ขนาด | commits | ชั้น | สถานะ audit | Risk |
|---|---|---|---|---|---|---|---|---|
| 1 | **Nirvasell** | public | Python | 1.3MB | 17 | **B** | 🟢 ยืนยัน | 🟢 |
| 2 | **Nirvaprocure** | public | TypeScript | 1.0MB | 75 | **B** | 🟢 ยืนยัน | 🟢 |
| 3 | **MUTEA** | public | Markdown | 15KB | 2 | **C** | 🟢 ยืนยัน | 🟢 |
| 4 | **nirvacore-v1** | private | TypeScript | 6.5MB | – | ยังไม่จัด | ⚪ รอ | ⚪ |
| 5 | **nirvadeploy** | private | TypeScript | 2.3MB | – | ยังไม่จัด | ⚪ รอ | ⚪ |
| 6 | **nirvatic** | private | JavaScript | **99MB** | – | ยังไม่จัด | ⚪ รอ | 🔴 สงสัย artifact |

> **หมายเหตุ re-score:** Nirvasell & Nirvaprocure เคยจัด A → ลงเป็น **B** เพราะยังไม่มีหลักฐาน production/ลูกค้า (A ต้องมีการพึ่งพาทางธุรกิจ ไม่ใช่แค่โค้ดสมบูรณ์) — ปัจจุบัน **ไม่มี repo ใดเป็น A**

## หมายเหตุ
- มี **6 repo จริง** บน GitHub เท่านั้น (ชื่ออื่นๆ ที่เคยเห็นในรายการ UI ไม่ใช่ repo จริง)
- ยังไม่มีการ merge / rename / archive / delete ใดๆ — **ทะเบียนนี้เป็นภาพ ณ ปัจจุบันเท่านั้น**
- ตัวชั้น A/B/C/D ของ private 3 ตัวเป็น *provisional* จนกว่าจะเปิดไฟล์จริง
