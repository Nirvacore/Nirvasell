# SOURCE_OF_TRUTH_UPDATE.md
> Phase 2B · อัปเดตต่อจาก SOURCE_OF_TRUTH_REPORT.md · 2026-06-14

## สถานะ NirvaCore SoT: **ยังคง UNRESOLVED**
เพิ่มหลักฐานใหม่จากที่ผู้ใช้รายงาน (Phase 2A): มี **ผู้สมัคร local เพิ่ม** = `~/nirvacore` และ `~/NIRVA`
แต่ **ยังเปิดไฟล์ทั้งสองไม่ได้** (cloud VM) → ยังฟันธงไม่ได้

## ภาพผู้สมัคร SoT ของ NirvaCore (ปัจจุบัน)
| ผู้สมัคร | ชนิด | สถานะหลักฐาน | บทบาทที่เป็นไปได้ |
|---|---|---|---|
| `nirvacore-v1` (GitHub 🔒) | Code Truth (remote) | metadata only (private) | ตัว backup บน cloud / อาจ active |
| `~/nirvacore` (local) | Workspace Truth | PENDING (`find_heart.sh`) | อาจเป็นตัว dev จริง |
| `~/NIRVA` (local) | Workspace Truth | PENDING | umbrella หรือ core อีกชุด |
| `~/nirva-backup-*`, `~/nirva-archive` | local | PENDING | น่าจะ D (backup/archive) |
| `nirva_os` (ใน `Nirvasell`) | blueprint | ✅ มี | แนวคิด core (ไม่ใช่ระบบเต็ม) |

## เงื่อนไขปิดเคส (เมื่อได้ผล find_heart.sh)
- ถ้า `~/nirvacore` มี remote=`nirvacore-v1` + ahead 0 → **SoT = GitHub `nirvacore-v1`** (local sync แล้ว) → Confidence Med-High
- ถ้า local สมบูรณ์กว่า remote (ahead หลาย commit / uncommitted เยอะ) → **SoT = local (Workspace)** + 🔴 conflict "GitHub ตามหลัง"
- ถ้าทั้งสอง local ไม่มี remote → **SoT = local-only** + 🔴 risk ไม่ backup
- ถ้าหลักฐานขัด/ไม่พอ → คงคำว่า **"Source of Truth remains unresolved"**

## สรุป
> **Source of Truth remains unresolved** — แต่แคบลงเหลือ 3 ผู้สมัคร (`nirvacore-v1`, `~/nirvacore`, `~/NIRVA`)
> ปิดได้ทันทีที่ได้ผล `scripts/find_heart.sh` จาก Mac
