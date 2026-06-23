"""Smart business alerts — aggregates signals from all modules."""
from __future__ import annotations
import db
from i18n import t
from i18n_inline import alert_kind_name

ALERT_TYPES = {
    "low_stock": {
        "icon": "📦",
        "color": "#c54c4c", "default_threshold": 5,
    },
    "overdue_po": {
        "icon": "📋",
        "color": "#c54c4c", "default_threshold": 0,
    },
    "unread_reviews": {
        "icon": "⭐",
        "color": "#c5963d", "default_threshold": 3,
    },
    "pending_commissions": {
        "icon": "💰",
        "color": "#c5963d", "default_threshold": 500,
    },
    "restock_urgent": {
        "icon": "⚠️",
        "color": "#c54c4c", "default_threshold": 0,
    },
    "content_overdue": {
        "icon": "📅",
        "color": "#9a7dc5", "default_threshold": 0,
    },
}


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS alert_config (
                alert_type  TEXT PRIMARY KEY,
                threshold   REAL DEFAULT 0,
                enabled     INTEGER DEFAULT 1,
                updated_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS alert_dismissals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_key   TEXT NOT NULL UNIQUE,
                dismissed_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        for atype, info in ALERT_TYPES.items():
            c.execute(
                "INSERT OR IGNORE INTO alert_config (alert_type,threshold,enabled) "
                "VALUES (?,?,1)",
                (atype, info["default_threshold"]),
            )


def configure(alert_type: str, threshold: float = None,
              enabled: bool = None) -> None:
    with db.conn() as c:
        if threshold is not None:
            c.execute("UPDATE alert_config SET threshold=?,updated_at=datetime('now','localtime') "
                      "WHERE alert_type=?", (threshold, alert_type))
        if enabled is not None:
            c.execute("UPDATE alert_config SET enabled=?,updated_at=datetime('now','localtime') "
                      "WHERE alert_type=?", (int(enabled), alert_type))


def get_config() -> dict:
    with db.conn() as c:
        rows = c.execute("SELECT * FROM alert_config").fetchall()
        return {r["alert_type"]: dict(r) for r in rows}


def dismiss(alert_key: str) -> None:
    with db.conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO alert_dismissals (alert_key,dismissed_at) "
            "VALUES (?,datetime('now','localtime'))",
            (alert_key,),
        )


def _dismissed_keys() -> set:
    with db.conn() as c:
        rows = c.execute(
            "SELECT alert_key FROM alert_dismissals "
            "WHERE date(dismissed_at)=date('now','localtime')"
        ).fetchall()
        return {r["alert_key"] for r in rows}


def check_all() -> list[dict]:
    cfg = get_config()
    dismissed = _dismissed_keys()
    alerts = []

    def push(alert_type: str, key: str, message: str,
             count: int = 0, action: str = "") -> None:
        if key in dismissed:
            return
        info = ALERT_TYPES.get(alert_type, {})
        alerts.append({
            "type": alert_type,
            "key": key,
            "icon": info.get("icon", "⚠️"),
            "label": alert_kind_name(alert_type),
            "color": info.get("color", "#c5963d"),
            "message": message,
            "count": count,
            "action": action,
        })

    with db.conn() as c:
        # low_stock
        if cfg.get("low_stock", {}).get("enabled", 1):
            threshold = cfg.get("low_stock", {}).get("threshold", 5)
            rows = c.execute(
                "SELECT COUNT(*) cnt FROM products WHERE stock<=? AND active=1",
                (threshold,),
            ).fetchone()
            count = rows["cnt"] if rows else 0
            if count > 0:
                push("low_stock", "low_stock_daily",
                     t("alrt.msg_low_stock", count=count,
                       threshold=int(threshold)),
                     count, "B7_🏅_ProductScore")

        # overdue_po
        if cfg.get("overdue_po", {}).get("enabled", 1):
            try:
                rows = c.execute(
                    "SELECT COUNT(*) cnt FROM purchase_orders "
                    "WHERE status IN ('sent','partial') "
                    "AND expected_date < date('now','localtime')"
                ).fetchone()
                count = rows["cnt"] if rows else 0
                if count > 0:
                    push("overdue_po", "overdue_po_daily",
                         t("alrt.msg_overdue_po", count=count),
                         count, "B3_🛒_PurchaseOrders")
            except Exception:
                pass

        # unread_reviews
        if cfg.get("unread_reviews", {}).get("enabled", 1):
            threshold = cfg.get("unread_reviews", {}).get("threshold", 3)
            try:
                rows = c.execute(
                    "SELECT COUNT(*) cnt FROM reviews WHERE response IS NULL OR response=''"
                ).fetchone()
                count = rows["cnt"] if rows else 0
                if count >= threshold:
                    push("unread_reviews", "unread_reviews_daily",
                         t("alrt.msg_unread_reviews", count=count),
                         count, "B1_⭐_Reviews")
            except Exception:
                pass

        # pending_commissions
        if cfg.get("pending_commissions", {}).get("enabled", 1):
            threshold = cfg.get("pending_commissions", {}).get("threshold", 500)
            try:
                rows = c.execute(
                    "SELECT COALESCE(SUM(commission_amount),0) total "
                    "FROM commission_records WHERE paid=0"
                ).fetchone()
                total = rows["total"] if rows else 0
                if total >= threshold:
                    push("pending_commissions", "pending_comm_daily",
                         t("alrt.msg_pending_commissions",
                           total="{:,.0f}".format(total)),
                         0, "B5_👤_Commissions")
            except Exception:
                pass

        # restock_urgent
        if cfg.get("restock_urgent", {}).get("enabled", 1):
            try:
                rows = c.execute(
                    "SELECT COUNT(DISTINCT r.sku) cnt "
                    "FROM restock_config r "
                    "JOIN products p ON r.sku=p.sku "
                    "WHERE p.stock=0"
                ).fetchone()
                count = rows["cnt"] if rows else 0
                if count > 0:
                    push("restock_urgent", "restock_urgent_daily",
                         t("alrt.msg_restock_urgent", count=count),
                         count, "A6_📦_Restock")
            except Exception:
                pass

        # content_overdue
        if cfg.get("content_overdue", {}).get("enabled", 1):
            try:
                rows = c.execute(
                    "SELECT COUNT(*) cnt FROM content_calendar "
                    "WHERE status='planned' AND scheduled_date < date('now','localtime')"
                ).fetchone()
                count = rows["cnt"] if rows else 0
                if count > 0:
                    push("content_overdue", "content_overdue_daily",
                         t("alrt.msg_content_overdue", count=count),
                         count, "B0_📅_ContentCal")
            except Exception:
                pass

    alerts.sort(key=lambda a: a["color"], reverse=True)
    return alerts


def stats() -> dict:
    all_alerts = check_all()
    return {
        "active_count": len(all_alerts),
        "critical": sum(1 for a in all_alerts if a["color"] == "#c54c4c"),
        "warnings": sum(1 for a in all_alerts if a["color"] == "#c5963d"),
    }
