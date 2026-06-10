#!/usr/bin/env python3
"""Standalone runner — checks all policy sources, detects changes, writes
an alerts log. Designed to run via cron / Streamlit Cloud Scheduled Tasks.

Usage (manual):
    python3 scripts/policy_check.py

Usage (cron, every 24h):
    0 9 * * * cd /path/to/nirva && /path/to/python3 scripts/policy_check.py >> /tmp/nirva_policy.log 2>&1

Output written to data/policy_alerts.jsonl — read by the 🔔 Alerts page."""
from __future__ import annotations
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Make sibling modules importable.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import policy_watcher as pw
import fees as fees_mod


ALERTS_PATH = ROOT / "data" / "policy_alerts.jsonl"
HASHES_PATH = ROOT / "data" / "policy_hashes.json"


def load_hashes() -> dict[str, str]:
    if HASHES_PATH.exists():
        try:
            return json.loads(HASHES_PATH.read_text())
        except Exception:
            pass
    return {}


def save_hashes(h: dict[str, str]):
    HASHES_PATH.write_text(json.dumps(h, indent=2))


def log_alert(record: dict):
    ALERTS_PATH.parent.mkdir(exist_ok=True)
    with ALERTS_PATH.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    hashes = load_hashes()
    sources = pw.load_sources()
    print(f"[{datetime.now().isoformat()}] checking {len(sources)} policy sources…")

    for s in sources:
        platform = s.get("platform")
        url = s.get("url")
        if not platform or not url:
            continue

        result = pw.fetch_source(s)
        if not result.get("ok"):
            reason = result.get("reason", "")
            print(f"  [{platform}] fetch FAIL status={result.get('status')} reason={reason or '-'}")
            log_alert({
                "at": datetime.now().isoformat(),
                "platform": platform,
                "kind": "fetch_failed",
                "status": result.get("status"),
                "reason": reason,
                "url": result.get("url_used", url),
            })
            continue

        new_hash = result["hash"]
        old_hash = hashes.get(platform)

        if old_hash == new_hash:
            print(f"  [{platform}] no change (hash {new_hash[:8]})")
            continue

        print(f"  [{platform}] CHANGED ({old_hash[:8] if old_hash else 'first'} → {new_hash[:8]})")

        # If we have an API key, also try to extract structured fees + diff.
        extracted = None
        diffs: list = []
        if api_key:
            try:
                extracted = pw.extract_fees_with_claude(result["text"], platform, api_key=api_key)
                diffs = pw.compare(platform, extracted or {})
            except Exception as e:
                print(f"    Claude extraction failed: {e}")

        log_alert({
            "at": datetime.now().isoformat(),
            "platform": platform,
            "kind": "content_changed",
            "url": url,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "diffs": diffs,
            "notes": (extracted or {}).get("notes", "") if extracted else "",
            "effective_date": (extracted or {}).get("effective_date", "") if extracted else "",
        })

        # Fan-out to ALL users' notification channels (cron is system-wide,
        # but each user's notify_channels live in their per-user DB).
        try:
            import sys as _sys
            _sys.path.insert(0, str(ROOT))
            import auth, notifier, user_settings, db
            for user in auth.list_users():
                # Point db.conn() at this user's DB for the duration.
                # Cleanest: set session_state via streamlit if available; we
                # bypass with a fake.
                import streamlit as _st
                _st.session_state = {"auth_user": user}
                try:
                    prefs = user_settings.notify_prefs()
                    if not prefs.get("policy_change"):
                        continue
                    body_lines = [f"{platform.upper()} marketplace policy changed."]
                    if diffs:
                        body_lines.append("")
                        for d in diffs[:4]:
                            body_lines.append(
                                f"  • {d['field']}: {d['old']:.2f}% → {d['new']:.2f}% "
                                f"({d['delta']:+.2f}%)"
                            )
                    if extracted and extracted.get("effective_date"):
                        body_lines.append(f"\nEffective: {extracted['effective_date']}")
                    body_lines.append(f"\nGo to 📋 Policies in nirva.sell to review.")
                    notifier.notify(
                        f"📋 {platform.upper()} fee policy updated",
                        "\n".join(body_lines),
                    )
                except Exception:
                    pass
        except Exception as e:
            print(f"    notification fanout failed: {e}")

        hashes[platform] = new_hash

    save_hashes(hashes)
    print(f"[{datetime.now().isoformat()}] done")


if __name__ == "__main__":
    main()
