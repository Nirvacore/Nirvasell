#!/usr/bin/env bash
# NIRVA MASTER COMMAND CENTER — Local Inventory collector (Phase 2A)
# รันบน "MacBook ของคุณ" (ไม่ใช่ cloud) เพื่อเก็บหลักฐานจริงทุก field
#   bash local_audit.sh > nirva_local_$(date +%Y%m%d).txt
# แล้วส่งไฟล์ผลกลับมา → ผมกรอกลง LOCAL_REGISTRY.md / LOCAL_CONFLICT_REPORT.md / LOCAL_SOURCE_OF_TRUTH.md
# DISCOVERY ONLY — อ่านอย่างเดียว: ไม่ย้าย ไม่เปลี่ยนชื่อ ไม่ลบ ไม่ทำ git ใดๆ

set -u
echo "# NIRVA LOCAL INVENTORY — $(date) — host: $(hostname)"

# โฟลเดอร์ฐานที่จะสแกน (ครอบคลุมที่ผู้ใช้รายงาน)
BASES=("$HOME" "$HOME/Downloads" "$HOME/Documents" "$HOME/Desktop" "$HOME/Projects" "$HOME/NIRVA" "$HOME/Developer" "$HOME/Code")

probe() {   # probe <dir>  → รายงานทุก field ที่ Phase 2A ต้องการ
  local d="$1"
  [ -d "$d" ] || return
  local mod git origin branch dirty
  mod=$(/bin/date -r "$d" '+%Y-%m-%d' 2>/dev/null)
  if [ -d "$d/.git" ]; then
    git="yes"
    origin=$(git -C "$d" config --get remote.origin.url 2>/dev/null)
    branch=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null)
    dirty=$(git -C "$d" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  else git="no"; origin=""; branch=""; dirty=""; fi
  echo "FOLDER: $d"
  echo "  last_modified: ${mod:-?}"
  echo "  git:           $git   origin: ${origin:-<none>}   branch: ${branch:-}   uncommitted: ${dirty:-}"
  echo "  package.json:  $([ -f "$d/package.json" ] && echo yes || echo no)"
  echo "  Docker:        $( { [ -f "$d/Dockerfile" ] || [ -f "$d/docker-compose.yml" ]; } && echo yes || echo no)"
  echo "  Prisma:        $( { [ -d "$d/prisma" ] || ls "$d"/**/schema.prisma >/dev/null 2>&1; } && echo yes || echo no)"
  echo "  README:        $(ls "$d"/README* >/dev/null 2>&1 && echo yes || echo no)"
  echo "  node_modules:  $([ -d "$d/node_modules" ] && echo "YES ($(du -sh "$d/node_modules" 2>/dev/null|cut -f1))" || echo no)"
  echo "  size:          $(du -sh "$d" 2>/dev/null | cut -f1)"
  echo "  top_entries:   $(ls -1 "$d" 2>/dev/null | head -12 | tr '\n' ',' )"
}

echo; echo "## ===== SCAN: direct children of each base ====="
declare -A seen
for base in "${BASES[@]}"; do
  [ -d "$base" ] || { echo "absent base: $base"; continue; }
  echo; echo "### BASE: $base"
  for child in "$base"/*/; do
    child="${child%/}"
    [ -d "$child" ] || continue
    [ -n "${seen[$child]:-}" ] && continue
    seen[$child]=1
    probe "$child"
  done
done

echo; echo "## ===== Downloads: ไฟล์ archive/zip/docx (production asset?) ====="
ls -lh "$HOME/Downloads"/*.zip "$HOME/Downloads"/*.docx "$HOME/Downloads"/*.tar* 2>/dev/null

echo; echo "## ===== Cursor recent ====="
for cfg in "$HOME/Library/Application Support/Cursor/User/globalStorage/storage.json" "$HOME/.config/Cursor/User/globalStorage/storage.json"; do
  [ -f "$cfg" ] && { echo "### $cfg"; grep -oE '"file://[^"]+"' "$cfg" 2>/dev/null | sort -u | head -100; } || echo "absent: $cfg"
done

echo; echo "# END — ส่งไฟล์นี้กลับให้ NIRVA MASTER COMMAND CENTER"
