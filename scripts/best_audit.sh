#!/usr/bin/env bash
# BEST GROUP Back Office — AUDIT (read-only discovery) · รันบน Mac
#   BEST_ROOT=/path/to/backoffice bash best_audit.sh > best_audit_$(date +%Y%m%d).txt
# อ่านอย่างเดียว: ไม่ย้าย ไม่เปลี่ยนชื่อ ไม่ลบ
set -u
ROOT="${BEST_ROOT:-$HOME}"     # ตั้ง BEST_ROOT ให้ชี้โฟลเดอร์ back office จริง
echo "# BEST BACK OFFICE AUDIT — $(date) — root: $ROOT"

echo; echo "## โฟลเดอร์ชั้นบน + หลักฐาน"
for d in "$ROOT"/*/; do
  d="${d%/}"; [ -d "$d" ] || continue
  echo "FOLDER: $d"
  echo "  last_modified: $(/bin/date -r "$d" '+%Y-%m-%d' 2>/dev/null)"
  echo "  size:          $(du -sh "$d" 2>/dev/null | cut -f1)"
  echo "  files:         $(find "$d" -type f 2>/dev/null | wc -l | tr -d ' ')"
  echo "  git:           $([ -d "$d/.git" ] && echo yes || echo no)"
  echo "  doc_types:     $(find "$d" -type f 2>/dev/null | sed 's/.*\.//' | tr 'A-Z' 'a-z' | sort | uniq -c | sort -rn | head -6 | tr '\n' ' ')"
done

echo; echo "## 🚩 UNKNOWN / ชื่อแปลก (flag เท่านั้น — ไม่แตะ)"
find "$ROOT" -maxdepth 1 -type d 2>/dev/null | while read -r d; do
  name="$(basename "$d")"
  case "$name" in
    *[\{\}\|\?\"\:\*\\]*|" "*|".."|"") echo "  ⚠️ UNKNOWN: [$name]  ($d)";;
  esac
done

echo; echo "## 🔐 ไฟล์ที่อาจ sensitive (PDPA) — นับเฉยๆ ไม่เปิดเนื้อหา"
find "$ROOT" -type f \( -iname '*payroll*' -o -iname '*salary*' -o -iname '*id_card*' -o -iname '*บัตรประชาชน*' -o -iname '*เงินเดือน*' -o -iname '*employee*' \) 2>/dev/null | wc -l | sed 's/^/  พบไฟล์ที่ชื่อสื่อถึงข้อมูลส่วนบุคคล: /'

echo; echo "# END — ส่งไฟล์นี้กลับให้ BEST MASTER COMMAND CENTER (อย่าแนบไฟล์ HR/PDPA)"
