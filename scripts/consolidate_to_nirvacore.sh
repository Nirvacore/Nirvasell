#!/usr/bin/env bash
#
# consolidate_to_nirvacore.sh
# รวม repo ที่กระจัดกระจายเข้าเป็น monorepo เดียว "nirvacore" โดยใช้ git subtree
# (เก็บประวัติ git ของแต่ละ repo ไว้ครบ — ไม่ทิ้งงานเก่า)
#
# วิธีใช้:
#   target = repo "nirvacore-v1" ที่มีอยู่แล้ว (ไม่ต้องสร้างใหม่)
#   1) clone nirvacore-v1 มาที่เครื่อง แล้ว cd เข้าไป
#   2) ตรวจรายการ REPOS ว่าตรงกับของจริง (มี 6 repo ใน org)
#   3) รัน:  bash /path/to/consolidate_to_nirvacore.sh
#
# ⚠️ nirvatic ใหญ่ ~99MB — น่าจะเผลอ commit node_modules ก่อนดูดเข้ามาควร
#    ตรวจ/ทำความสะอาดก่อน (เพิ่ม .gitignore node_modules, git rm -r --cached)
#    ไม่งั้น monorepo จะอืดถาวร
#
# ปลอดภัย: สคริปต์นี้ไม่ลบ repo เก่าใดๆ. มันแค่ "ดูดสำเนา+ประวัติ" เข้ามา.
# หลังยืนยันว่าครบแล้ว ค่อยไป Archive repo เก่าบน GitHub เองด้วยมือ.

set -euo pipefail

ORG="Nirvacore"
BASE="https://github.com/${ORG}"
BRANCH_DEFAULT="main"   # ถ้า repo ไหนใช้ master ให้ใส่คู่ใน REPOS

# รูปแบบ:  "ชื่อ-repo|ปลายทางในโฟลเดอร์|branch"
# อิงผลสำรวจจริง org Nirvacore (มี 6 repo). target = repo nirvacore-v1 (มีอยู่แล้ว)
# คอมเมนต์ (#) ตัวที่ยังไม่อยากดูด
REPOS=(
  "Nirvasell|apps/sell|main"          # Python — งาน standards_kb/nirva_os/payroll
  "Nirvaprocure|apps/procure|main"    # TypeScript
  "nirvadeploy|apps/deploy|main"      # TypeScript (private)
  "nirvatic|apps/nirvatic|main"       # JS (private, ~99MB — ดู §cleanup ก่อน!)
  # "MUTEA|ventures/mu_tea|main"      # ว่าง 15KB — ข้ามไปก่อน
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
