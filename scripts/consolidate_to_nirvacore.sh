#!/usr/bin/env bash
#
# consolidate_to_nirvacore.sh
# รวม repo ที่กระจัดกระจายเข้าเป็น monorepo เดียว "nirvacore" โดยใช้ git subtree
# (เก็บประวัติ git ของแต่ละ repo ไว้ครบ — ไม่ทิ้งงานเก่า)
#
# วิธีใช้:
#   1) สร้าง repo เปล่าชื่อ nirvacore บน GitHub (org: Nirvacore)
#   2) แก้ค่า ORG ด้านล่างถ้าจำเป็น และตรวจรายการ REPOS ว่าตรงกับของจริง
#      (คอมเมนต์ตัวที่ยังไม่มี / ยังว่างออกได้)
#   3) รัน:  bash scripts/consolidate_to_nirvacore.sh
#
# ปลอดภัย: สคริปต์นี้ไม่ลบ repo เก่าใดๆ. มันแค่ "ดูดสำเนา+ประวัติ" เข้ามา.
# หลังยืนยันว่าครบแล้ว ค่อยไป Archive repo เก่าบน GitHub เองด้วยมือ.

set -euo pipefail

ORG="Nirvacore"
BASE="https://github.com/${ORG}"
BRANCH_DEFAULT="main"   # ถ้า repo ไหนใช้ master ให้ใส่คู่ใน REPOS

# รูปแบบ:  "ชื่อ-repo|ปลายทางในโฟลเดอร์|branch"
# คอมเมนต์ (#) ตัวที่ยังไม่มีจริง หรือยังว่าง
REPOS=(
  "NirvaSell|apps/sell|main"
  "NIRVAPROCURE|apps/procure|main"
  "NirvaFleet|apps/fleet|main"
  "NirvaDeploy|apps/deploy|main"
  "NirvaWealth|apps/wealth|main"
  "NIRVACORE-BUILDER|apps/builder|main"
  "Nirvacore-manu|apps/manu|main"
  "NirvaResearchDocs|packages/research_docs|main"
  "MU-TEA|ventures/mu_tea|main"
  # "Nirvacore2|_review/nirvacore2|main"   # ← ตรวจก่อนว่ามีของจริงไหม
)

echo "==> ตรวจว่าอยู่ใน repo nirvacore (เปล่า) จริง"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "❌ ต้องรันในโฟลเดอร์ git ของ nirvacore"; exit 1; }

# โครงสร้างหลัก
mkdir -p apps packages ventures docs scripts
[ -f README.md ] || echo "# nirvacore — Nirva unified monorepo (v1)" > README.md
git add -A && git commit -m "chore: scaffold nirvacore monorepo structure" || true

for entry in "${REPOS[@]}"; do
  name="${entry%%|*}"; rest="${entry#*|}"
  prefix="${rest%%|*}"; branch="${rest##*|}"
  [ -z "$branch" ] && branch="$BRANCH_DEFAULT"
  url="${BASE}/${name}.git"

  echo ""
  echo "==> ดูด ${name}  →  ${prefix}  (branch ${branch})"
  if [ -d "$prefix" ]; then
    echo "    ข้าม: ${prefix} มีอยู่แล้ว"
    continue
  fi
  # subtree add เก็บ history ของ repo ต้นทางไว้ใต้ prefix
  if git subtree add --prefix="$prefix" "$url" "$branch"; then
    echo "    ✅ สำเร็จ: ${name}"
  else
    echo "    ⚠️  ข้าม ${name} (อาจยังไม่มี repo / branch ไม่ตรง / ว่าง) — ตรวจแล้วรันซ้ำเฉพาะตัวได้"
  fi
done

echo ""
echo "==> เสร็จขั้น subtree. ขั้นถัดไป (ทำมือ/ผมช่วย):"
echo "    1) ย้าย apps/sell/{standards_kb,nirva_os,nirva_research} ขึ้น packages/"
echo "    2) แก้ import paths + ตั้ง CI ครั้งเดียว"
echo "    3) git push -u origin main แล้วเปิด PR"
echo "    4) ยืนยันงานครบ → ค่อยไป Archive repo เก่าบน GitHub"
