# DECISION_LOG.md
> บันทึกการตัดสินใจ NIRVA MASTER COMMAND CENTER (เรียงใหม่→เก่า)

---

### 2026-06-14 · D-005 · MUTEA จัดชั้นใหม่ D → **C**
- **หลักฐาน:** clone จริง พบ README "Mu Tea research knowledge base" + 7 ไฟล์ .md (brand + 4 research reports) ไม่มีโค้ด
- **ตัดสิน:** เป็น Knowledge/Research (C) ไม่ใช่ placeholder ว่าง (D)
- **บทเรียน:** ตอกย้ำกฎ *ห้ามเดาจากชื่อ/ขนาด* — 15KB ไม่ได้แปลว่าว่าง

### 2026-06-14 · D-004 · ยืนยัน Nirvasell=A, Nirvaprocure=A ด้วยหลักฐาน
- Nirvasell: 298 .py, commerce OS จริง → **A**
- Nirvaprocure: backend+frontend+mobile+db schema, "90+ tasks shipped" → **A**
- ทั้งคู่ Risk 🟢 (มีแค่ .env.example = template, ไม่มี node_modules/dist tracked)

### 2026-06-14 · D-003 · Source of Truth ของ NirvaCore = **ยังไม่ชี้ขาด**
- เหตุผล: ผู้สมัครหลัก `nirvacore-v1` เป็น private ยังไม่มีสิทธิ์เปิด
- การกระทำ: **รอเพิ่ม scope** ก่อนยืนยัน — ห้ามเดา

### 2026-06-14 · D-002 · เปลี่ยนวิธีเข้าถึง public repo = git clone
- github MCP ถูกล็อก scope แค่ `nirvasell` → ใช้ `git clone` ตรงสำหรับ public repo แทน (network เปิด)
- private repo ทำแบบนี้ไม่ได้ → ต้องรอสิทธิ์

### 2026-06-14 · D-001 · ❌ ยกเลิก/ระงับแผน auto-merge เป็น monorepo
- เหตุผล: ขัด Repository Rules (*audit before refactor · do not merge automatically · preserve before replacing*)
- การกระทำ: ทำ **audit + classify (A/B/C/D) ก่อน**, NIRVACORE_V1_PLAN.md → สถานะ PAUSED

---

## ข้อห้าม (ยังมีผลตลอดช่วง audit)
- ⛔ ห้าม merge / rename / archive / delete repo ใดๆ
- ⛔ ห้ามเดาจากชื่อ — ใช้หลักฐานเท่านั้น
- ⛔ ห้ามลบ artifact/secret ที่เจอเอง — **flag เป็น Risk** แล้วรอยืนยัน

## รอดำเนินการ (Next)
1. [รอผู้ใช้] เพิ่มสิทธิ์ private: `nirvacore-v1`, `nirvadeploy`, `nirvatic`
2. audit 3 ตัวนั้นด้วยหลักฐาน → ปิด D-003 (ชี้ขาด Source of Truth)
3. ยืนยัน Risk `nirvatic` (99MB)
4. เสนอ topology สุดท้าย — *หลัง audit ครบเท่านั้น*
