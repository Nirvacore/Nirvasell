# CURSOR_PROJECT_REGISTRY.md
> Phase 2 · Part 2 (Cursor Audit) · 2026-06-14

## ⚠️ Access Limitation
Cursor เก็บข้อมูล recent projects ใน `~/Library/Application Support/Cursor/...` บน **MacBook**
environment นี้ = cloud VM → **ไม่มี Cursor data** (ตรวจแล้ว absent ทุก path)

**หลักฐานทางอ้อมที่พบ:** commit ใน `Nirvaprocure` ระบุ *"after concurrent Cursor Phase 15 merge"* → ยืนยันว่า **Cursor ถูกใช้พัฒนา Nirvaprocure จริง** (แต่รายละเอียด project list ต้องดึงจาก Mac)

## ✅ วิธีเก็บ (ให้คุณทำ)
รัน `scripts/local_audit.sh` บน Mac (Part 4 ของสคริปต์ดึง Cursor recent/workspaceStorage ให้) แล้วส่งผลกลับ

## Template (Classification: A/P/B/C/D)
| Cursor Project | Local Path | GitHub repo | Last opened (ประเมิน) | Purpose | Class | Evidence |
|---|---|---|---|---|---|---|
| _(รอข้อมูลจาก Mac)_ | | | | | | |
| Nirvaprocure | ? | `Nirvaprocure` | active (commit 2026-06-14) | procurement OS | **B** | commit ref "Cursor Phase 15" |
