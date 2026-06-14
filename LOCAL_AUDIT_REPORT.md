# LOCAL_AUDIT_REPORT.md
> Phase 2 · Part 1 (Local Machine Audit) · 2026-06-14

## ⚠️ Access Limitation (สำคัญ — อ่านก่อน)
audit นี้สั่งให้สแกน `~/Projects ~/Documents ~/Desktop ~/Downloads ~/NIRVA` บน **MacBook** แต่ session ปัจจุบันรันบน **cloud VM ชั่วคราว** (`root@vm`) ที่ clone repo มาสดๆ

ตรวจจริงแล้ว (หลักฐาน):
| path ที่สั่งสแกน | ผลบน VM นี้ |
|---|---|
| `~/Projects` `~/Documents` `~/Desktop` `~/Downloads` `~/NIRVA` | **absent ทั้งหมด** |
| Cursor data (`.cursor`, `~/Library/Application Support/Cursor`) | **absent** |
| Claude Desktop (`~/Library/Application Support/Claude`) | **absent** |
| git repos บน VM | มีแค่ `/home/user/Nirvasell`, `/tmp/_audit/{Nirvaprocure,MUTEA}` (ที่ผม clone), `/opt/*` (system) |

➡️ **สรุป:** ไม่สามารถ audit MacBook จาก environment นี้ได้ — **ไม่ใช่ "เครื่องว่าง"** แต่เป็นคนละเครื่อง

## ✅ วิธีเก็บหลักฐานจริง (ให้คุณทำ)
1. เปิด Terminal บน **MacBook**
2. รัน:
   ```bash
   bash scripts/local_audit.sh > nirva_local_audit_$(date +%Y%m%d).txt
   ```
   (สคริปต์ **อ่านอย่างเดียว** — ไม่ย้าย/เปลี่ยนชื่อ/ลบ ตามกฎ Phase 2)
3. ส่งไฟล์ `.txt` กลับมา → ผมกรอกลงตารางด้านล่าง + อัปเดต `NIRVA_REGISTRY.md`, `CURSOR_PROJECT_REGISTRY.md`

## Template (จะเติมเมื่อได้ผลจาก Mac)
| Folder | Purpose (ประเมิน) | Last modified | Git? | Remote origin | Stack | Production evidence | Match GitHub repo |
|---|---|---|---|---|---|---|---|
| _(รอข้อมูล)_ | | | | | | | |

## สิ่งที่ยืนยันได้แล้วจาก VM (subset)
| Folder | Git | Remote | Stack | หมายเหตุ |
|---|---|---|---|---|
| `/home/user/Nirvasell` | ✅ | github.com/Nirvacore/Nirvasell | Python/Streamlit | working copy ของ session นี้ (branch `claude/standards-knowledge-graph-kbyxo1`) |
| `/tmp/_audit/Nirvaprocure` | ✅ | github.com/Nirvacore/Nirvaprocure | TS | clone ชั่วคราวเพื่อ audit (จะหายเมื่อ container รีไซเคิล) |
| `/tmp/_audit/MUTEA` | ✅ | github.com/Nirvacore/MUTEA | Markdown | clone ชั่วคราวเพื่อ audit |
