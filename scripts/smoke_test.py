#!/usr/bin/env python3
"""Smoke-test every Streamlit page headlessly.

Runs each pages/*.py (plus app.py) via streamlit.testing.v1.AppTest with a
seeded, logged-in demo user, and reports any uncaught exception. This is the
regression gate for the "every page at least renders" invariant.

Each page runs in its own subprocess (a page can segfault the interpreter on
teardown; isolation keeps one bad page from killing the whole sweep).

Usage:  python3 scripts/smoke_test.py [--filter SUBSTR] [--json OUT]
Exit code = number of failing pages (capped at 125).
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402


def seeded_demo_user() -> dict:
    """Create/fetch the demo account and return its user dict."""
    import auth
    auth.init()
    auth.signup("demo@nirva.sell", "demopass123", "Demo User")  # idempotent-ish
    ok, res = auth.login("demo@nirva.sell", "demopass123")
    if not ok or not isinstance(res, dict):
        raise SystemExit(f"could not login demo user: {res}")
    return dict(res)


def run_page(path: Path, user: dict) -> tuple[bool, str]:
    try:
        at = AppTest.from_file(str(path), default_timeout=60)
        at.session_state["auth_user"] = user
        at.session_state["lang"] = "th"
        at.run()
        if at.exception:
            exc = at.exception[0]
            return False, f"{exc.type}: {exc.message}"
        return True, ""
    except Exception as e:  # harness-level failure (import error etc.)
        return False, f"{type(e).__name__}: {e}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", default="", help="only pages containing this substring")
    ap.add_argument("--json", default="", help="write results JSON to this path")
    ap.add_argument("--one", default="", help="internal: run a single page path, print verdict")
    args = ap.parse_args()

    if args.one:
        user = seeded_demo_user()
        ok, err = run_page(Path(args.one), user)
        print("SMOKE_OK" if ok else f"SMOKE_FAIL {err.splitlines()[0][:300]}")
        return 0

    seeded_demo_user()  # ensure demo account exists before fan-out
    pages = sorted(ROOT.glob("pages/*.py")) + [ROOT / "app.py"]
    if args.filter:
        pages = [p for p in pages if args.filter in p.name]

    results: dict[str, str] = {}
    passed = failed = 0
    for p in pages:
        proc = subprocess.run(
            [sys.executable, __file__, "--one", str(p)],
            capture_output=True, text=True, timeout=180, cwd=ROOT,
        )
        verdict = next(
            (l for l in proc.stdout.splitlines() if l.startswith("SMOKE_")), ""
        )
        if verdict == "SMOKE_OK":
            passed += 1
            print(f"  PASS  {p.name}", flush=True)
        else:
            failed += 1
            err = verdict.removeprefix("SMOKE_FAIL ").strip() or (
                f"subprocess died rc={proc.returncode}: "
                + (proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "no output")
            )
            results[p.name] = err
            print(f"! FAIL  {p.name}  {err[:160]}", flush=True)

    print(f"\n{passed} passed, {failed} failed / {len(pages)} pages")
    if args.json:
        Path(args.json).write_text(json.dumps(results, ensure_ascii=False, indent=1))
    return min(failed, 125)


if __name__ == "__main__":
    raise SystemExit(main())
