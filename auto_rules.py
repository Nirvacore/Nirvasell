"""Automation Rules Engine — if/then without coding.

Sellers define rules like:
  "When stock < 5 → notify LINE"
  "When VIP customer orders → upgrade shipping"
  "When return rate > 5% → flag product"

Rules are checked on each relevant event (order import, stock change, etc.)
and trigger actions automatically."""
from __future__ import annotations

import json
from datetime import datetime

import db


def init():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS auto_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                condition_json TEXT DEFAULT '{}',
                action_type TEXT NOT NULL,
                action_json TEXT DEFAULT '{}',
                enabled INTEGER DEFAULT 1,
                last_fired TEXT,
                fire_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS rule_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                fired_at TEXT DEFAULT (datetime('now','localtime')),
                trigger_data TEXT DEFAULT '',
                action_result TEXT DEFAULT '',
                FOREIGN KEY (rule_id) REFERENCES auto_rules(id)
            )
        """)


# ---- Trigger types ----
TRIGGERS = {
    "low_stock":      {"label": "Stock below threshold",  "icon": "📦"},
    "new_order":      {"label": "New order received",     "icon": "🛒"},
    "vip_order":      {"label": "VIP customer orders",    "icon": "💎"},
    "high_return":    {"label": "Return rate too high",   "icon": "↩️"},
    "price_change":   {"label": "Product price changed",  "icon": "💰"},
    "dormant_cust":   {"label": "Customer goes dormant",  "icon": "😴"},
    "daily_summary":  {"label": "Daily summary time",     "icon": "📊"},
}

# ---- Action types ----
ACTIONS = {
    "line_notify":    {"label": "Send LINE notification", "icon": "💚"},
    "flag_product":   {"label": "Flag product for review","icon": "🚩"},
    "auto_reorder":   {"label": "Create reorder alert",   "icon": "📋"},
    "adjust_price":   {"label": "Suggest price adjustment","icon": "💰"},
    "tag_customer":   {"label": "Tag customer",            "icon": "🏷️"},
    "log_only":       {"label": "Log event only",          "icon": "📝"},
}


def add_rule(name: str, trigger_type: str, condition: dict,
             action_type: str, action_config: dict) -> int:
    with db.conn() as c:
        c.execute(
            "INSERT INTO auto_rules "
            "(name, trigger_type, condition_json, action_type, action_json) "
            "VALUES (?,?,?,?,?)",
            (name, trigger_type, json.dumps(condition),
             action_type, json.dumps(action_config)),
        )
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_rule(rule_id: int, **kwargs):
    sets = []
    vals = []
    for k in ("name", "trigger_type", "action_type", "enabled"):
        if k in kwargs:
            sets.append(k + "=?")
            vals.append(kwargs[k])
    if "condition" in kwargs:
        sets.append("condition_json=?")
        vals.append(json.dumps(kwargs["condition"]))
    if "action_config" in kwargs:
        sets.append("action_json=?")
        vals.append(json.dumps(kwargs["action_config"]))
    if not sets:
        return
    vals.append(rule_id)
    with db.conn() as c:
        c.execute(
            "UPDATE auto_rules SET " + ",".join(sets) + " WHERE id=?",
            vals,
        )


def delete_rule(rule_id: int):
    with db.conn() as c:
        c.execute("DELETE FROM rule_log WHERE rule_id=?", (rule_id,))
        c.execute("DELETE FROM auto_rules WHERE id=?", (rule_id,))


def toggle_rule(rule_id: int, enabled: bool):
    with db.conn() as c:
        c.execute(
            "UPDATE auto_rules SET enabled=? WHERE id=?",
            (1 if enabled else 0, rule_id),
        )


def all_rules() -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM auto_rules ORDER BY created_at DESC"
        ).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        d["condition"] = json.loads(d.get("condition_json") or "{}")
        d["action_config"] = json.loads(d.get("action_json") or "{}")
        d["enabled"] = bool(d.get("enabled", 1))
        results.append(d)
    return results


def get_rule(rule_id: int) -> dict | None:
    with db.conn() as c:
        r = c.execute("SELECT * FROM auto_rules WHERE id=?", (rule_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["condition"] = json.loads(d.get("condition_json") or "{}")
    d["action_config"] = json.loads(d.get("action_json") or "{}")
    return d


# ---- Rule evaluation ----

def evaluate_low_stock() -> list[dict]:
    """Check all low_stock rules against current inventory."""
    rules = [r for r in all_rules()
             if r["trigger_type"] == "low_stock" and r["enabled"]]
    fired = []
    for rule in rules:
        threshold = rule["condition"].get("threshold", 5)
        with db.conn() as c:
            low = c.execute(
                "SELECT sku, name, stock FROM products "
                "WHERE stock <= ? AND stock >= 0",
                (threshold,),
            ).fetchall()

        if low:
            items = [dict(r) for r in low]
            _fire_rule(rule, {"low_stock_items": items})
            fired.append({"rule": rule, "items": items})
    return fired


def evaluate_high_return() -> list[dict]:
    """Check return rate rules."""
    rules = [r for r in all_rules()
             if r["trigger_type"] == "high_return" and r["enabled"]]
    fired = []
    for rule in rules:
        threshold = rule["condition"].get("threshold_pct", 5)
        try:
            import returns as ret
            ret.init()
            s = ret.stats()
            if s["return_rate"] > threshold:
                _fire_rule(rule, {"return_rate": s["return_rate"]})
                fired.append({"rule": rule, "rate": s["return_rate"]})
        except Exception:
            pass
    return fired


def _fire_rule(rule: dict, trigger_data: dict):
    """Execute a rule's action and log it."""
    now = datetime.now().isoformat(timespec="seconds")

    action_type = rule["action_type"]
    action_config = rule.get("action_config", {})
    result = ""

    if action_type == "line_notify":
        try:
            import line_notify
            msg = action_config.get("message", "")
            if not msg:
                msg = "🔔 Rule fired: " + rule["name"]
            # Add trigger data summary
            if "low_stock_items" in trigger_data:
                items = trigger_data["low_stock_items"]
                msg = msg + "\n📦 " + str(len(items)) + " items low stock"
                for item in items[:5]:
                    msg = msg + "\n  - " + (item.get("sku") or "") + ": " + str(item.get("stock", 0))
            line_notify.send(msg)
            result = "LINE sent"
        except Exception as e:
            result = "LINE error: " + str(e)

    elif action_type == "log_only":
        result = "Logged"

    elif action_type == "flag_product":
        result = "Flagged for review"

    else:
        result = "Action: " + action_type

    # Log the firing
    with db.conn() as c:
        c.execute(
            "INSERT INTO rule_log (rule_id, trigger_data, action_result) "
            "VALUES (?,?,?)",
            (rule["id"], json.dumps(trigger_data, default=str), result),
        )
        c.execute(
            "UPDATE auto_rules SET last_fired=?, fire_count=fire_count+1 WHERE id=?",
            (now, rule["id"]),
        )


def rule_history(rule_id: int, limit: int = 20) -> list[dict]:
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM rule_log WHERE rule_id=? "
            "ORDER BY fired_at DESC LIMIT ?",
            (rule_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM auto_rules").fetchone()[0]
        active = c.execute(
            "SELECT COUNT(*) FROM auto_rules WHERE enabled=1"
        ).fetchone()[0]
        total_fires = c.execute(
            "SELECT COALESCE(SUM(fire_count),0) FROM auto_rules"
        ).fetchone()[0]
    return {"total": total, "active": active, "total_fires": int(total_fires)}
