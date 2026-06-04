"""Simple operator-grade error log.

Writes a structured JSON line per error to `data/errors.log` so you can
`tail -f` it on the server. Rotates at 5 MB (keeps last 3 files). No
dependency on Sentry/Datadog — keeps deploys simple.

Usage from anywhere:
    import error_log
    try:
        ...
    except Exception as e:
        error_log.log(e, where="page.X", user_id=u.get("id"))
        raise"""
from __future__ import annotations
import json
import os
import time
import traceback
from pathlib import Path


_LOG_DIR = Path(__file__).parent / "data"
_LOG_FILE = _LOG_DIR / "errors.log"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_KEEP = 3


def _rotate_if_needed():
    try:
        if not _LOG_FILE.exists():
            return
        if _LOG_FILE.stat().st_size < _MAX_BYTES:
            return
        # Shift older files (errors.log.2 → .3, .1 → .2, current → .1)
        for i in range(_KEEP, 0, -1):
            older = _LOG_DIR / f"errors.log.{i}"
            newer = _LOG_DIR / f"errors.log.{i+1}"
            if older.exists():
                if i == _KEEP:
                    older.unlink()
                else:
                    older.rename(newer)
        _LOG_FILE.rename(_LOG_DIR / "errors.log.1")
    except Exception:
        # If rotation itself fails, swallow — better to keep logging
        pass


def log(exc: Exception, *, where: str = "", user_id: int | None = None,
        extra: dict | None = None) -> None:
    """Append a JSON line. Never raises — error logging must not crash the
    error path."""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        _rotate_if_needed()
        entry = {
            "ts":      time.time(),
            "iso":     time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "type":    type(exc).__name__,
            "msg":     str(exc)[:500],
            "where":   where,
            "user_id": user_id,
            "trace":   traceback.format_exception(type(exc), exc, exc.__traceback__)[-4:],
        }
        if extra:
            entry["extra"] = {k: str(v)[:200] for k, v in extra.items()}
        with _LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def tail(n: int = 50) -> list[dict]:
    """Read the last N log entries — for admin UI / cron summary."""
    if not _LOG_FILE.exists():
        return []
    try:
        with _LOG_FILE.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
        out = []
        for line in lines[-n:]:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out
    except Exception:
        return []


def clear() -> None:
    try:
        if _LOG_FILE.exists():
            _LOG_FILE.unlink()
    except Exception:
        pass
