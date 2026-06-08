"""Backup Manager — export and import full SQLite database.

Creates a downloadable copy of the user's entire database.
Restore replaces the current DB with an uploaded backup."""
from __future__ import annotations
import io
import json
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
import db


def create_backup() -> bytes:
    db_path = db._resolve_path()
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, "nirva_backup.db")
        meta = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "db_file": str(db_path.name),
            "version": "v67",
        }
        with db.conn() as c:
            meta["products"] = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            meta["orders"] = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            try:
                meta["expenses"] = c.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
            except Exception:
                meta["expenses"] = 0

        zf.writestr("backup_meta.json", json.dumps(meta, indent=2, ensure_ascii=False))

    return buf.getvalue()


def validate_backup(data: bytes) -> dict:
    try:
        zf = zipfile.ZipFile(io.BytesIO(data), "r")
    except zipfile.BadZipFile:
        return {"valid": False, "error": "ไฟล์ไม่ใช่ ZIP ที่ถูกต้อง"}

    names = zf.namelist()
    if "nirva_backup.db" not in names:
        return {"valid": False, "error": "ไม่พบไฟล์ฐานข้อมูลใน backup"}

    db_data = zf.read("nirva_backup.db")
    try:
        tmp = sqlite3.connect(":memory:")
        tmp.executescript("")
        tmp_path = Path("/tmp/nirva_validate_backup.db")
        tmp_path.write_bytes(db_data)
        tmp = sqlite3.connect(str(tmp_path))
        tables = [r[0] for r in tmp.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        tmp.close()
        tmp_path.unlink(missing_ok=True)
    except Exception as e:
        return {"valid": False, "error": "ฐานข้อมูลเสีย: " + str(e)}

    if "products" not in tables:
        return {"valid": False, "error": "ฐานข้อมูลไม่มีตาราง products"}

    meta = {}
    if "backup_meta.json" in names:
        try:
            meta = json.loads(zf.read("backup_meta.json"))
        except Exception:
            pass

    return {
        "valid": True,
        "tables": tables,
        "meta": meta,
        "size_kb": len(data) // 1024,
    }


def restore_backup(data: bytes) -> dict:
    validation = validate_backup(data)
    if not validation["valid"]:
        return validation

    zf = zipfile.ZipFile(io.BytesIO(data), "r")
    db_data = zf.read("nirva_backup.db")

    db_path = db._resolve_path()

    backup_existing = db_path.with_suffix(".db.bak")
    if db_path.exists():
        import shutil
        shutil.copy2(db_path, backup_existing)

    db_path.write_bytes(db_data)

    with db.conn() as c:
        products = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    return {
        "valid": True,
        "restored": True,
        "products": products,
        "orders": orders,
        "backup_of_previous": str(backup_existing),
    }


def backup_info() -> dict:
    db_path = db._resolve_path()
    size_kb = 0
    if db_path.exists():
        size_kb = db_path.stat().st_size // 1024

    with db.conn() as c:
        products = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        try:
            tables = [r[0] for r in c.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
        except Exception:
            tables = []
        try:
            expenses = c.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        except Exception:
            expenses = 0

    return {
        "db_path": str(db_path),
        "size_kb": size_kb,
        "products": products,
        "orders": orders,
        "expenses": expenses,
        "tables": len(tables),
    }
