"""GDPR-grade data export — ZIP everything nirva.sell holds about one user.

Contents of the ZIP:
  • account.json         — display name, email, role, created_at
  • db/listo.db          — copy of the user's SQLite DB (raw)
  • csv/products.csv
  • csv/content.csv
  • csv/orders.csv       (if exists)
  • csv/translations.csv (if exists)
  • images/              — any locally-stored product photos
  • README.txt           — manifest + restore instructions
"""
from __future__ import annotations
import io
import json
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd

import auth


ROOT = Path(__file__).parent
DATA = ROOT / "data"


def _table_to_csv(c: sqlite3.Connection, table: str) -> bytes | None:
    """Dump a table to CSV bytes, or None if table doesn't exist / is empty."""
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table}", c)
        if df.empty:
            return None
        return df.to_csv(index=False).encode("utf-8-sig")
    except Exception:
        return None


def export_user(user: dict) -> bytes:
    """Build a ZIP archive of everything we hold for `user`. Returns raw bytes."""
    user_id = user["id"]
    user_db = DATA / "users" / f"{user_id}.db"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. account profile
        profile = {
            "id":           user_id,
            "email":        user.get("email"),
            "display_name": user.get("display_name"),
            "role":         user.get("role"),
            "exported_at":  datetime.now().isoformat(),
        }
        zf.writestr("account.json", json.dumps(profile, indent=2, ensure_ascii=False))

        # 2. raw DB
        if user_db.exists():
            zf.write(user_db, "db/listo.db")

            # 3. CSV dumps for each table
            try:
                conn = sqlite3.connect(str(user_db))
                conn.row_factory = sqlite3.Row
                tables = [r["name"] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )]
                for t in tables:
                    data = _table_to_csv(conn, t)
                    if data:
                        zf.writestr(f"csv/{t}.csv", data)
                conn.close()
            except Exception:
                pass

        # 4. locally-stored images (Vision intake puts files here)
        images_dir = DATA / "uploaded_images"
        if images_dir.exists():
            for img in images_dir.iterdir():
                if not img.is_file():
                    continue
                # Filter to images owned by this user by checking the DB ref
                # (best-effort — if DB is gone, we include nothing)
                try:
                    if user_db.exists():
                        conn = sqlite3.connect(str(user_db))
                        owned = conn.execute(
                            "SELECT 1 FROM products WHERE image_url LIKE ?",
                            (f"%{img.name}%",),
                        ).fetchone()
                        conn.close()
                        if owned:
                            zf.write(img, f"images/{img.name}")
                except Exception:
                    continue

        # 5. README / manifest
        readme = f"""nirva.sell — Data Export
========================
User:        {user.get('email')} (id={user_id})
Exported at: {datetime.now().isoformat()}

Contents:
  account.json          — profile metadata
  db/listo.db           — your private SQLite database
  csv/*.csv             — table-by-table CSV dumps
  images/               — uploaded product photos

Restore:
  • Place db/listo.db at data/users/{user_id}.db on a fresh install,
    then login with the same email.
  • Or load the CSVs in any spreadsheet / database tool.

License of your data:
  100% yours. You exported it. Do anything with it.
"""
        zf.writestr("README.txt", readme)

    return buf.getvalue()


def export_size_estimate(user_id: int) -> int:
    """Quick estimate of export size in bytes."""
    user_db = DATA / "users" / f"{user_id}.db"
    return user_db.stat().st_size if user_db.exists() else 0
