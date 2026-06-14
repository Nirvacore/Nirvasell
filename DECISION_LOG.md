# DECISION_LOG.md
> บันทึกการตัดสินใจ NIRVA MASTER COMMAND CENTER (เรียงใหม่→เก่า)

---

### 2026-06-14 · D-011 · Phase 2B "Find the Heart" — ยังระบุไม่ได้
- focus `~/nirvacore` + `~/NIRVA` → ทั้งคู่ absent บน VM (cloud) → ตอบ Q1-5 ด้วยหลักฐานไม่ได้
- สร้าง `scripts/find_heart.sh` (เจาะ 2 โฟลเดอร์, ไม่สแกนทั้งเครื่อง) + decision rule สำเร็จรูป
- NirvaCore SoT แคบเหลือ 3 ผู้สมัคร: `nirvacore-v1`(remote) · `~/nirvacore` · `~/NIRVA` → **ยัง UNRESOLVED**
- Output: HEART_REPORT.md, SOURCE_OF_TRUTH_UPDATE.md, CONFLICT_UPDATE.md

### 2026-06-14 · D-010 · Phase 2A House Cleaning = discovery only
- ใช้รายการโฟลเดอร์ที่ผู้ใช้รายงานเป็นหลักฐาน → LOCAL_REGISTRY/LOCAL_CONFLICT/LOCAL_SOURCE_OF_TRUTH
- 🔴 flag: Downloads อาจมี production asset (nirva deploy/deploy/zip) → "Downloads ต้องไม่เป็น SoT"
- flag duplicate L1-L6 (ไม่ resolve) · `~/nirvawealth` = local-only ไม่มี repo (เสี่ยงสูญ)
- เสนอ future structure แบบ informational เท่านั้น · ทุก classification = Confidence Low (จากชื่อ)
- ⛔ ไม่ย้าย/เปลี่ยนชื่อ/ลบ/merge/git ใดๆ

### 2026-06-14 · D-009 · Part 9 Recommendations (ยังไม่แนะนำ migration)
**ต้องยืนยันถัดไป (เรียงความสำคัญ):**
1. เปิด `nirvacore-v1` (สิทธิ์ private) → ปิด C2 / SoT ของ NirvaCore
2. รัน `scripts/local_audit.sh` บน Mac → ปิด C6/C7 + เติม Local/Cursor registry
3. ตรวจ `nirvatic` 99MB (C4) เมื่อมีสิทธิ์
4. ขอรายการ Claude.ai Projects + NotebookLM notebooks → ปิด C8/C9
**หลักฐานที่ยังขาด:** ผล audit Mac/Cursor · เนื้อใน private 3 repo · มี deployment/ลูกค้าจริงไหม (ตัดสิน A vs P)
**รอได้ปลอดภัย:** การจัดบ้าน knowledge/decision (C1/C3), การวาง topology — ทำหลังแผนที่ครบ
**สำคัญ:** *preserve ก่อน — ยังไม่ merge/move/rename/delete อะไรทั้งสิ้น*

### 2026-06-14 · D-008 · Phase 2 environment = cloud VM (ไม่ใช่ MacBook)
- หลักฐาน: `root@vm`, ไม่มี `~/Projects ~/Documents ~/Desktop ~/Downloads ~/NIRVA`, ไม่มี Cursor/Claude-desktop data
- ผล: Part 1-4 (Local/Cursor/Claude/Knowledge) **ทำจากที่นี่ไม่ได้** → บันทึก Access Limitation + สร้าง `scripts/local_audit.sh` ให้รันบน Mac
- ❌ ห้ามสรุปว่า "ไม่มีงาน" — เป็นคนละเครื่อง

### 2026-06-14 · D-007 · NIRVA = Pre-Production state
- ไม่มี repo ใดพิสูจน์ว่า mission-critical · NirvaCore = Pending Verification

### 2026-06-14 · D-006 · Re-score classification ตามเกณฑ์ business-dependency
- **เกณฑ์ใหม่:** A ต้องมี *production use จริง / ลูกค้า / ธุรกิจเสียหายถ้าล่ม* — ไม่ใช่แค่โค้ดสมบูรณ์
- **ผล:**
  - Nirvasell: A → **B** (ไม่มีหลักฐาน production/ลูกค้า)
  - Nirvaprocure: A → **B** (STATUS.md: "ready for first pilot" = pre-production)
  - MUTEA: **C** (venture/exploration คงเดิม)
  - private 3 ตัว: → **ยังไม่จัด** (รอ audit; technical maturity ≠ A)
- **สรุป:** ปัจจุบัน **ไม่มี repo ใดเป็น A**
- **อัปเดต:** AUDIT_LOG.md, REPO_AUDIT_REPORT.md, REPO_REGISTRY.md · *ไม่แตะ repo ใด*

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
