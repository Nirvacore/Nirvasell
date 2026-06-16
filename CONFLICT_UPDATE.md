# CONFLICT_UPDATE.md
> Phase 2B · อัปเดต conflict (FLAG only) · 2026-06-14

## อัปเดต L1 (CORE) — ยังเปิดไม่ได้, ยกระดับการติดตาม
| Conflict | สมาชิก | Severity | สถานะ |
|---|---|---|---|
| **L1 CORE** | `~/nirvacore` · `~/NIRVA` · `~/nirva-backup-*` · `~/nirva-archive` · `nirvacore-v1`(remote) | **High** | รอ `find_heart.sh` เปิด 2 ตัวหลัก |

## คำถามที่ conflict นี้ต้องตอบ (ยังตอบไม่ได้)
1. `~/nirvacore` กับ `~/NIRVA` เป็น **คนละโปรเจกต์** หรือ **สำเนากัน**? → ดู remote + last_commit + diff
2. ตัวไหน **ตัวจริง (active)** ตัวไหน **backup/archive**? → ดู last_commit/ชื่อ
3. **GitHub `nirvacore-v1` sync กับ local ไหม?** → ดู ahead/behind
4. มี **uncommitted งานสำคัญ** ที่ยังไม่ขึ้น cloud ไหม? (เสี่ยงสูญ) → ดู uncommitted count

## conflict ใหม่ที่เป็นไปได้ (รอข้อมูลยืนยัน — ยังไม่ resolve)
| # | possible conflict | Severity (คาด) | ปิดด้วย |
|---|---|---|---|
| L1a | local code (`~/nirvacore`) ≠ GitHub (`nirvacore-v1`) | High–Critical | ahead/behind จาก find_heart.sh |
| L1b | `~/nirvacore` vs `~/NIRVA` = สำเนาที่ diverge | High | diff/last_commit |
| L1c | backup/archive ใหม่กว่าตัว "active" (สลับบทบาท) | Medium | last_commit เทียบ |

## กฎ
- ⛔ ทุก conflict **flag เท่านั้น ไม่ resolve / ไม่ลบ / ไม่ merge / ไม่ย้าย**
- ปิด L1 = เงื่อนไขก่อนจะตัดสิน SoT ของ NirvaCore (ดู SOURCE_OF_TRUTH_UPDATE.md)
