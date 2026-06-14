# MAC_REORGANIZATION_PLAN.md
> NIRVA LIFE OS · Mapping → `~/HQ` (10-cat) · 2026-06-14
> อิง **HQ_BLUEPRINT.md** (เอกสารหลัก) · **PLAN ONLY — ยังไม่ execute**
> กฎ: backup ก่อน · ไม่ลบ · ไม่ทับ · ไม่แตะ git history · ไม่เปลี่ยน remote · ย้ายหลังอนุมัติ

## Source of Truth (user-attested)
`~/nirvacore` ↔ `nirvacore-v1` ↔ `main` = **Code Truth** · `~/NIRVA` = Workspace

## Mapping ทุกโฟลเดอร์ → `~/HQ/`
Risk: 🔴High 🟡Med 🟢Low · Conf จากชื่อ+ยืนยันผู้ใช้

### Home `~/`
| Current | Purpose | → `~/HQ/` Destination | Risk | Conf |
|---|---|---|---|---|
| `~/nirvacore` | หัวใจ ERP (SoT) | `01_CORE/NirvaCore` | 🔴 | High |
| `~/NIRVA` | Workspace รวม (มีของหลายอย่าง) | `05_WORKSPACE/Review/NIRVA` *(แยกย่อยภายหลัง)* | 🟡 | Med |
| `~/nirvawealth` | NirvaWealth (**no repo**) | `02_PRODUCTS/NirvaWealth/source` | 🔴 | Low |
| `~/mu-tea` | Mu Tea (↔MUTEA) | `03_VENTURES/MuTea/source` | 🟢 | Low |
| `~/Claude` | decisions/เอกสาร | `04_KNOWLEDGE/Documentation/Claude` | 🟡 | Low |
| `~/Doc.for.ERP` | เอกสาร ERP | `04_KNOWLEDGE/Documentation/Doc.for.ERP` | 🟢 | Low |
| `~/nirva-archive` | เก็บถาวร | `06_ARCHIVE/Legacy/nirva-archive` | 🟢 | Low |
| `~/nirva-backup-*` | สำรอง | `07_BACKUPS/Releases/<name>` | 🟢 | Low |

### Downloads `~/Downloads/` — ⚠️ ย้ายออก (inbox only, ของเก่า >30 วันต้องไป)
| Current | Purpose | → Destination | Risk | Conf |
|---|---|---|---|---|
| `~/Downloads/nirva deploy` | NirvaDeploy working | `02_PRODUCTS/NirvaDeploy/source` | 🔴 | Low |
| `~/Downloads/nirva-landing` | landing | `02_PRODUCTS/NirvaDeploy/landing` | 🟡 | Low |
| `~/Downloads/deploy` | ไม่ชัด | `05_WORKSPACE/Review/deploy` | 🟡 | Low |
| `~/Downloads/nirva_deploy.zip` | snapshot | `07_BACKUPS/Releases/nirva_deploy.zip` | 🟢 | Low |
| `~/Downloads/NirvaGovTH Dev Spec.docx` | spec | `04_KNOWLEDGE/Documentation/NirvaGov/` | 🟢 | Low |

### Documents `~/Documents/`
| Current | Purpose | → Destination | Risk | Conf |
|---|---|---|---|---|
| `~/Documents/Claude` | เอกสาร (อาจซ้ำ ~/Claude) | `04_KNOWLEDGE/Documentation/Claude-Documents` *(ไม่ merge)* | 🟡 | Low |
| `~/Documents/VCode` | workspace โค้ด | `05_WORKSPACE/Review/VCode` | 🟡 | Low |

## หมายเหตุความปลอดภัย
- ของชื่อชนกัน (`Claude` 2 ที่) → ปลายทางต่างกัน **ไม่รวมอัตโนมัติ**
- `~/NIRVA`, `deploy`, `VCode` → ลง `05_WORKSPACE/Review/` รอ **แยกย่อยไปบ้านจริง** (ไม่เดาเนื้อใน)
- `nirvawealth` (no remote) = **backup + สร้าง repo + push ก่อน** (ขั้นแยก ก่อนพึ่ง local อย่างเดียว)

## ลำดับ execute (เมื่ออนุมัติ — รันบน Mac)
```bash
EXECUTE=1 bash scripts/hq_init.sh         # 1) สร้างโครง ~/HQ
EXECUTE=1 bash scripts/nirva_backup.sh    # 2) backup ก่อน
bash scripts/nirva_reorg.sh               # 3) ดูแผนย้าย (dry-run)
EXECUTE=1 bash scripts/nirva_reorg.sh     # 4) ย้ายจริง
```
> หมายเหตุ: แผนนี้แทนที่โครง `~/NIRVA-HQ` (7 หมวด) เดิม → ใช้ `~/HQ` (10 หมวด) ตาม HQ_BLUEPRINT.md
