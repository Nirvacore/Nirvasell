#!/usr/bin/env bash
# Simple external healthcheck — probes the public URL and exits non-zero on
# any failure. Hook into uptime monitoring (UptimeRobot, BetterUptime, cron).
#
#   ./scripts/healthcheck.sh https://nirva.example.com
#
# Returns 0 if the app is up + responds within 10s, else 1.

set -u

URL="${1:-${NIRVA_URL:-http://127.0.0.1:8501}}"
HEALTH="${URL%/}/_stcore/health"
MAX_TIME="${HEALTH_MAX_TIME:-10}"

code="$(curl -o /dev/null -s --max-time "${MAX_TIME}" \
        -w '%{http_code}' "${HEALTH}" || echo 000)"

if [[ "${code}" == "200" ]]; then
    echo "OK ${URL} -> ${code}"
    exit 0
fi

echo "DOWN ${URL} -> ${code}" >&2
exit 1
