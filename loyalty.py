"""Loyalty Program — points, tiers, and rewards for repeat customers.

Points earned per baht spent. Tiers unlock discounts and perks.
Tracks redemption history."""
from __future__ import annotations
from datetime import datetime
import db
from i18n import t
from i18n_inline import loyalty_reward_name, loyalty_tier

TIERS = {
    "bronze": {"min_points": 0, "discount_pct": 0, "icon": "🥉"},
    "silver": {"min_points": 500, "discount_pct": 3, "icon": "🥈"},
    "gold": {"min_points": 2000, "discount_pct": 5, "icon": "🥇"},
    "platinum": {"min_points": 5000, "discount_pct": 8, "icon": "💎"},
    "diamond": {"min_points": 15000, "discount_pct": 12, "icon": "👑"},
}

REWARDS = [
    {"id": "free_ship", "points": 100, "icon": "🚚"},
    {"id": "discount_5", "points": 200, "icon": "🏷"},
    {"id": "discount_10", "points": 500, "icon": "🎫"},
    {"id": "free_gift", "points": 300, "icon": "🎁"},
    {"id": "priority_ship", "points": 150, "icon": "⚡"},
]

POINTS_PER_BAHT = 1


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS loyalty_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_key TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                lifetime_points INTEGER DEFAULT 0,
                tier TEXT DEFAULT 'bronze',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(customer_key)
            );
            CREATE TABLE IF NOT EXISTS loyalty_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_key TEXT NOT NULL,
                action TEXT NOT NULL,
                points INTEGER NOT NULL,
                balance_after INTEGER,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_loyalty_cust
                ON loyalty_history(customer_key);
        """)


def _determine_tier(lifetime_points: int) -> str:
    tier = "bronze"
    for t_name, t_info in TIERS.items():
        if lifetime_points >= t_info["min_points"]:
            tier = t_name
    return tier


def earn_points(customer_key: str, amount: float,
                description: str = "") -> dict:
    pts = int(amount * POINTS_PER_BAHT)
    if pts <= 0:
        return {"earned": 0}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db.conn() as c:
        existing = c.execute(
            "SELECT points, lifetime_points FROM loyalty_points WHERE customer_key = ?",
            (customer_key,)
        ).fetchone()

        if existing:
            new_bal = existing["points"] + pts
            new_life = existing["lifetime_points"] + pts
            new_tier = _determine_tier(new_life)
            c.execute("""
                UPDATE loyalty_points
                SET points = ?, lifetime_points = ?, tier = ?, updated_at = ?
                WHERE customer_key = ?
            """, (new_bal, new_life, new_tier, now, customer_key))
        else:
            new_bal = pts
            new_life = pts
            new_tier = _determine_tier(new_life)
            c.execute("""
                INSERT INTO loyalty_points (customer_key, points, lifetime_points, tier)
                VALUES (?, ?, ?, ?)
            """, (customer_key, new_bal, new_life, new_tier))

        c.execute("""
            INSERT INTO loyalty_history (customer_key, action, points,
                                         balance_after, description)
            VALUES (?, 'earn', ?, ?, ?)
        """, (customer_key, pts, new_bal, description or t("loy.earn_default_desc")))

    return {"earned": pts, "balance": new_bal, "tier": new_tier}


def redeem_points(customer_key: str, reward_id: str) -> dict:
    reward = next((r for r in REWARDS if r["id"] == reward_id), None)
    if not reward:
        return {"success": False, "error_key": "loy.err_reward_not_found"}

    with db.conn() as c:
        existing = c.execute(
            "SELECT points FROM loyalty_points WHERE customer_key = ?",
            (customer_key,)
        ).fetchone()

        if not existing or existing["points"] < reward["points"]:
            return {"success": False, "error_key": "loy.err_insufficient_points"}

        new_bal = existing["points"] - reward["points"]
        c.execute(
            "UPDATE loyalty_points SET points = ? WHERE customer_key = ?",
            (new_bal, customer_key)
        )
        c.execute("""
            INSERT INTO loyalty_history (customer_key, action, points,
                                         balance_after, description)
            VALUES (?, 'redeem', ?, ?, ?)
        """, (customer_key, -reward["points"], new_bal, loyalty_reward_name(reward_id)))

    return {
        "success": True,
        "balance": new_bal,
        "reward": loyalty_reward_name(reward_id),
    }


def customer_loyalty(customer_key: str) -> dict:
    with db.conn() as c:
        row = c.execute(
            "SELECT * FROM loyalty_points WHERE customer_key = ?",
            (customer_key,)
        ).fetchone()

        if not row:
            return {"enrolled": False, "customer_key": customer_key}

        tier = row["tier"]
        tier_info = TIERS.get(tier, TIERS["bronze"])

        history = c.execute("""
            SELECT action, points, balance_after, description, created_at
            FROM loyalty_history WHERE customer_key = ?
            ORDER BY created_at DESC LIMIT 20
        """, (customer_key,)).fetchall()

        next_tier = None
        for t_name, t_info in TIERS.items():
            if t_info["min_points"] > row["lifetime_points"]:
                next_tier = {
                    "name": t_name,
                    "icon": t_info["icon"],
                    "points_needed": t_info["min_points"] - row["lifetime_points"],
                }
                break

    return {
        "enrolled": True,
        "customer_key": customer_key,
        "points": row["points"],
        "lifetime_points": row["lifetime_points"],
        "tier": tier,
        "tier_icon": tier_info["icon"],
        "tier_label": loyalty_tier(tier),
        "discount_pct": tier_info["discount_pct"],
        "next_tier": next_tier,
        "history": [dict(h) for h in history],
    }


def leaderboard(limit: int = 20) -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT customer_key, points, lifetime_points, tier
            FROM loyalty_points
            ORDER BY lifetime_points DESC
            LIMIT ?
        """, (limit,)).fetchall()
    result = []
    for i, r in enumerate(rows):
        tier_info = TIERS.get(r["tier"], TIERS["bronze"])
        result.append({
            "rank": i + 1,
            "customer_key": r["customer_key"],
            "points": r["points"],
            "lifetime_points": r["lifetime_points"],
            "tier": r["tier"],
            "tier_icon": tier_info["icon"],
        })
    return result


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM loyalty_points").fetchone()[0]
        tiers = {}
        for t_name in TIERS:
            cnt = c.execute(
                "SELECT COUNT(*) FROM loyalty_points WHERE tier = ?",
                (t_name,)
            ).fetchone()[0]
            tiers[t_name] = cnt
        total_points = c.execute(
            "SELECT COALESCE(SUM(points), 0) FROM loyalty_points"
        ).fetchone()[0]
        total_redeemed = c.execute(
            "SELECT COALESCE(SUM(ABS(points)), 0) FROM loyalty_history WHERE action = 'redeem'"
        ).fetchone()[0]
    return {
        "members": total,
        "tiers": tiers,
        "total_points_outstanding": total_points,
        "total_redeemed": total_redeemed,
    }
