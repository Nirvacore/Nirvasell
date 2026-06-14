#!/usr/bin/env bash
# NIRVA MASTER COMMAND CENTER — Local + Cursor Audit collector
# รันบน "MacBook ของคุณ" (ไม่ใช่ cloud) เพื่อเก็บหลักฐานจริงสำหรับ Phase 2
#   bash local_audit.sh > nirva_local_audit_$(date +%Y%m%d).txt
# จากนั้นส่งไฟล์ผลลัพธ์กลับมาให้ผม — ผมจะกรอกลง LOCAL_AUDIT_REPORT.md / CURSOR_PROJECT_REGISTRY.md
# อ่านอย่างเดียว: ไม่ย้าย ไม่เปลี่ยนชื่อ ไม่ลบ อะไรทั้งสิ้น

set -u
echo "# NIRVA LOCAL AUDIT — $(date) — host: $(hostname)"

echo; echo "## 1) Dev folders"
for base in "$HOME/Projects" "$HOME/Documents" "$HOME/Desktop" "$HOME/Downloads" "$HOME/NIRVA" "$HOME/Developer" "$HOME/Code" "$HOME/src"; do
  [ -d "$base" ] || { echo "absent: $base"; continue; }
  echo "### $base"
  /usr/bin/find "$base" -maxdepth 2 -type d 2>/dev/null | head -100
done

echo; echo "## 2) Git repos (ทั้ง HOME) + remote + last commit"
/usr/bin/find "$HOME" -maxdepth 5 -name '.git' -type d 2>/dev/null | while read -r g; do
  d=$(dirname "$g")
  origin=$(git -C "$d" config --get remote.origin.url 2>/dev/null)
  last=$(git -C "$d" log -1 --format='%ci' 2>/dev/null)
  branch=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null)
  dirty=$(git -C "$d" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  echo "REPO: $d"
  echo "  origin:   ${origin:-<none>}"
  echo "  branch:   ${branch:-?}   uncommitted: ${dirty}"
  echo "  last:     ${last:-?}"
  echo "  stack:    $(ls "$d" 2>/dev/null | grep -iE 'package.json|pyproject.toml|requirements.txt|go.mod|Cargo.toml|pubspec.yaml|Gemfile' | tr '\n' ' ')"
done

echo; echo "## 3) 🚩 RISK scan (artifact/secret ที่อาจถูก track)"
/usr/bin/find "$HOME" -maxdepth 6 \( -name 'node_modules' -o -name 'dist' -o -name '.next' -o -name '.env' \) 2>/dev/null | grep -v '/Library/' | head -50

echo; echo "## 4) Cursor recent projects"
for cfg in "$HOME/Library/Application Support/Cursor/User/globalStorage/storage.json" \
           "$HOME/.config/Cursor/User/globalStorage/storage.json"; do
  if [ -f "$cfg" ]; then
    echo "### $cfg"
    # ดึงรายการ path ที่เคยเปิด (history) แบบหยาบ
    grep -oE '"file://[^"]+"|"path":"[^"]+"' "$cfg" 2>/dev/null | sort -u | head -100
  else
    echo "absent: $cfg"
  fi
done
ls -1 "$HOME/Library/Application Support/Cursor/User/workspaceStorage" 2>/dev/null | head -50

echo; echo "## 5) Claude Desktop / CLI projects (ถ้ามี)"
ls -1 "$HOME/.claude/projects" 2>/dev/null | head -50
ls -1 "$HOME/Library/Application Support/Claude" 2>/dev/null | head -20

echo; echo "# END — ส่งไฟล์นี้กลับให้ NIRVA MASTER COMMAND CENTER"
