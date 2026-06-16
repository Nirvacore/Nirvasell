# CLAUDE_PROJECT_REGISTRY.md
> Phase 2 · Part 3 (Claude Project Audit) · 2026-06-14

## ⚠️ Access Limitation
"Claude Projects" บน **claude.ai (web/desktop)** — session นี้ (Claude Code CLI) **อ่านรายการ project บน claude.ai ไม่ได้**
สิ่งที่เห็นบน VM = config ของ CLI เองเท่านั้น:
- `/root/.claude/projects/` → มีแค่ `-home-user-Nirvasell` (transcript ของ session นี้)
- `.claude.json` → อ้างถึง `/home/user/Nirvasell` เท่านั้น
→ **ไม่ใช่** รายการ Claude.ai Projects ของคุณ

## ✅ วิธีเก็บ (ให้คุณทำ)
จาก claude.ai → ส่งรายชื่อ Project + คำอธิบายสั้นมาให้ (หรือ export) ผมจะ map ให้ตามตารางล่าง

## สิ่งที่เป็น "Decision Truth" และพิสูจน์ได้แล้ว (อยู่ในรีโปนี้)
session Claude Code นี้ได้สร้าง decision artifacts จริง = แหล่ง Decision Truth ปัจจุบันของ NIRVA:
| Artifact | เนื้อหา | ตำแหน่ง |
|---|---|---|
| `DECISION_LOG.md` | D-001..D-007 (governance) | `Nirvasell` repo |
| `REPO_AUDIT_REPORT.md` / `AUDIT_LOG.md` | audit หลักฐาน | `Nirvasell` repo |
| `REPO_REGISTRY.md` / `ECOSYSTEM_MAP.md` | ทะเบียน + map | `Nirvasell` repo |

## Template — map Claude.ai Projects → ecosystem (BEST/NIRVA/NOVA/MUVERSE/SOUL/FUTURE)
| Claude Project | Purpose | Ecosystem component | Contains decisions? | Has source docs? | Notes |
|---|---|---|---|---|---|
| _(รอรายการจาก claude.ai)_ | | | | | |

> หมายเหตุ governance: ตอนนี้ Decision Truth ถูกเก็บ **ปนใน Nirvasell repo** — อนาคตควรมีที่อยู่กลาง (เช่น repo `nirva-governance` หรือ Claude Project เฉพาะ) แต่ **ยังไม่ย้าย** (Phase 2 = วาดแผนที่เท่านั้น)
