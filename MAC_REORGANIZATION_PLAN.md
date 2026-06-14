# MAC_REORGANIZATION_PLAN.md
> NIRVA MASTER COMMAND CENTER · Phase 3A (Mapping) · 2026-06-14
> **PLAN ONLY — no move / no delete / no overwrite / no git history rewrite / no repo rename**
> ลงมือได้เฉพาะหลังคุณอนุมัติ (สคริปต์ default = dry-run)

## Source of Truth (ยืนยันโดยผู้ใช้ — user-attested)
- **Code Truth:** `~/nirvacore` ↔ `github.com/Nirvacore/nirvacore-v1` ↔ branch `main`
- **Workspace:** `~/NIRVA`
> หมายเหตุ: ยืนยันโดยผู้ใช้ (ผมยังไม่ได้เปิดไฟล์เอง) — ก่อนย้าย "หัวใจ" สคริปต์จะ **ตรวจ remote/branch ให้ตรงก่อน** (กันย้ายผิดตัว)

## ปลายทางที่เสนอ (`~/NIRVA-HQ/`)
```
~/NIRVA-HQ/
├── 01-Core/        # หัวใจ ERP (nirvacore)
├── 02-Products/    # ผลิตภัณฑ์ที่มี repo/โค้ด
├── 03-Ventures/    # ธุรกิจ/แบรนด์ทดลอง
├── 04-Knowledge/   # เอกสาร/สเปก/decisions
├── 05-Workspace/   # พื้นที่ทำงานรวม
├── 06-Archive/     # ของเก่า/experiment
└── 07-Backups/     # สำเนา/zip/snapshot
```

## ตาราง Mapping (ทุกโฟลเดอร์)
Risk: 🔴High / 🟡Med / 🟢Low · Confidence จากชื่อ+ยืนยันผู้ใช้

### Home `~/`
| Current path | Purpose (ประเมิน) | → Destination | Risk | Conf | หมายเหตุ |
|---|---|---|---|---|---|
| `~/nirvacore` | **หัวใจ ERP** (SoT, ↔nirvacore-v1) | `01-Core/nirvacore` | 🔴 | High | ตรวจ remote=main ก่อนย้าย · backup ก่อน |
| `~/NIRVA` | Workspace รวม | `05-Workspace/NIRVA` | 🟡 | Med | อาจมีของกระจาย — สำรวจก่อน |
| `~/nirvawealth` | NirvaWealth (**local-only, ไม่มี repo**) | `03-Ventures/nirvawealth` | 🔴 | Low | **backup สำคัญสุด** (ถ้าหายคือสูญ) |
| `~/mu-tea` | Mu Tea (↔repo MUTEA) | `03-Ventures/mu-tea` | 🟢 | Low | มี remote — กู้ได้ |
| `~/Claude` | decisions/เอกสาร AI | `04-Knowledge/Claude` | 🟡 | Low | อาจซ้ำกับ `~/Documents/Claude` — **ไม่รวมอัตโนมัติ** |
| `~/Doc.for.ERP` | เอกสาร ERP | `04-Knowledge/Doc.for.ERP` | 🟢 | Low | |
| `~/nirva-archive` | เก็บถาวร | `06-Archive/nirva-archive` | 🟢 | Low | |
| `~/nirva-backup-*` | สำรอง | `07-Backups/nirva-backup-*` | 🟢 | Low | คงสภาพ |

### Downloads `~/Downloads/` — ⚠️ ย้ายออกจาก Downloads (ห้ามเป็น SoT)
| Current path | Purpose | → Destination | Risk | Conf | หมายเหตุ |
|---|---|---|---|---|---|
| `~/Downloads/nirva deploy` | NirvaDeploy working (↔nirvadeploy?) | `02-Products/nirva-deploy` | 🔴 | Low | ตรวจ .git/remote ก่อน · อาจ local-only |
| `~/Downloads/nirva-landing` | landing page | `02-Products/nirva-landing` | 🟡 | Low | |
| `~/Downloads/deploy` | deploy artifact | `06-Archive/deploy-review` | 🟡 | Low | ไม่ชัด → พักที่ archive รอตรวจ |
| `~/Downloads/nirva_deploy.zip` | snapshot zip | `07-Backups/nirva_deploy.zip` | 🟢 | Low | |
| `~/Downloads/NirvaGovTH Dev Spec.docx` | spec NirvaGov | `04-Knowledge/NirvaGov/` | 🟢 | Low | |

### Documents `~/Documents/`
| Current path | Purpose | → Destination | Risk | Conf | หมายเหตุ |
|---|---|---|---|---|---|
| `~/Documents/Claude` | decisions/เอกสาร | `04-Knowledge/Claude-Documents` | 🟡 | Low | **แยกชื่อ** กัน collide กับ `~/Claude` (ไม่ merge) |
| `~/Documents/VCode` | workspace โค้ด | `05-Workspace/VCode` | 🟡 | Low | ตรวจว่ามี repo ข้างในไหม |

## หลักความปลอดภัยที่ฝังในแผน
1. **Backup ก่อนย้ายทุกครั้ง** (tar → `07-Backups/`)
2. ของชื่อชนกัน (`Claude` 2 ที่) → **ตั้งชื่อปลายทางต่างกัน ไม่ merge อัตโนมัติ**
3. ไม่ลบต้นทางอัตโนมัติ · ไม่ทับไฟล์ (ถ้าปลายทางมีอยู่ = หยุด)
4. git repo: ย้ายทั้งโฟลเดอร์เฉยๆ — **ไม่แตะ .git history / ไม่เปลี่ยนชื่อ remote**
5. **ตัวที่ไม่มี remote (nirvawealth) = สำคัญสุด** → แนะนำสร้าง repo + push ก่อน (แยกขั้น)

ขั้นต่อไป: `scripts/nirva_backup.sh` (3B) → `scripts/nirva_reorg.sh` (3C)
