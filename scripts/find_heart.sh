#!/usr/bin/env bash
# NIRVA Phase 2B — Find the Heart · เจาะ "เฉพาะ 2 โฟลเดอร์" (ไม่สแกนทั้งเครื่อง)
# รันบน MacBook:
#   bash find_heart.sh > nirva_heart_$(date +%Y%m%d).txt
# แล้วส่งไฟล์กลับมา → ผมเติม HEART_REPORT.md + ตอบ Q1-Q5
# DISCOVERY ONLY: ไม่ย้าย ไม่เปลี่ยนชื่อ ไม่ลบ ไม่ทำ git ใดๆ

set -u
TARGETS=("$HOME/nirvacore" "$HOME/NIRVA")
echo "# NIRVA HEART PROBE — $(date) — host: $(hostname)"

heart() {
  local d="$1"
  echo; echo "════════════════════════════════════"
  echo "FOLDER: $d"
  echo "════════════════════════════════════"
  if [ ! -d "$d" ]; then echo "  ❌ absent"; return; fi

  echo "  last_modified(dir): $(/bin/date -r "$d" '+%Y-%m-%d %H:%M' 2>/dev/null)"
  echo "  newest_file:        $(/usr/bin/find "$d" -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -print0 2>/dev/null | xargs -0 stat -f '%m %N' 2>/dev/null | sort -rn | head -1)"
  echo "  size:               $(du -sh "$d" 2>/dev/null | cut -f1)"

  echo "  --- git ---"
  if [ -d "$d/.git" ]; then
    echo "  .git:    yes"
    echo "  origin:  $(git -C "$d" config --get remote.origin.url 2>/dev/null)"
    echo "  branch:  $(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    echo "  last_commit: $(git -C "$d" log -1 --format='%ci %h %s' 2>/dev/null)"
    echo "  commits: $(git -C "$d" rev-list --count HEAD 2>/dev/null)"
    echo "  uncommitted: $(git -C "$d" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
    echo "  ahead/behind: $(git -C "$d" rev-list --left-right --count @{u}...HEAD 2>/dev/null || echo 'no upstream')"
  else echo "  .git:    no"; fi

  echo "  --- stack markers ---"
  echo "  package.json:  $([ -f "$d/package.json" ] && echo yes || echo no)"
  echo "  Docker:        $( { [ -f "$d/Dockerfile" ] || [ -f "$d/docker-compose.yml" ]; } && echo yes || echo no)"
  echo "  Prisma:        $( /usr/bin/find "$d" -name 'schema.prisma' -not -path '*/node_modules/*' 2>/dev/null | head -1 | grep -q . && echo yes || echo no)"
  echo "  README:        $(ls "$d"/README* >/dev/null 2>&1 && echo yes || echo no)"
  echo "  node_modules:  $([ -d "$d/node_modules" ] && echo "YES ($(du -sh "$d/node_modules" 2>/dev/null|cut -f1))" || echo no)"

  echo "  --- monorepo markers ---"
  for sub in src apps packages services backend frontend mobile api database modules; do
    [ -d "$d/$sub" ] && echo "  has/$sub: $(ls -1 "$d/$sub" 2>/dev/null | head -8 | tr '\n' ',')"
  done

  echo "  --- ERP signal (นับไฟล์โค้ด, ไม่รวม node_modules) ---"
  /usr/bin/find "$d" -type f -not -path '*/node_modules/*' -not -path '*/.git/*' \
    \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.py' -o -name '*.prisma' -o -name '*.sql' \) 2>/dev/null \
    | sed 's/.*\.//' | sort | uniq -c | sort -rn
  echo "  top_level: $(ls -1A "$d" 2>/dev/null | head -25 | tr '\n' ',')"
}

for t in "${TARGETS[@]}"; do heart "$t"; done
echo; echo "# END"
