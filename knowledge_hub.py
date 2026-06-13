"""Nirva Knowledge Hub — the Source of Truth ("สมองกลาง").

This is the center of the Nirva ecosystem (Master Prompt V3, Priority 1):
*everything is a Node, and every Node can link to any other Node*. It stores
organizational knowledge — Vision, Mission, Values, SOP, ISO, Decisions,
Risks, Lessons Learned, Research, etc. — as a small knowledge graph that any
other module can read from and write to.

Two integration points make it a real "hub", not just another page:

  • ``capture(...)`` — other systems push knowledge IN (idempotent per
    source+ref_key, so re-capturing updates instead of duplicating).
  • ``search(...)`` — other systems read knowledge OUT.

Philosophy (Master Prompt): knowledge first, human first. Nothing is forced
— starter content is only seeded when the user explicitly asks for it.
"""
from __future__ import annotations

import db


# ---- Taxonomy ---------------------------------------------------------------
# Node types mirror the Knowledge Hub contents in the Master Prompt. Labels are
# resolved through i18n (key ``kh.type.<key>``) so the Hub speaks every UI
# language; the icon + group are structural and stay here.
NODE_TYPES: dict[str, dict] = {
    # Direction & culture
    "vision":       {"icon": "🌅", "group": "direction"},
    "mission":      {"icon": "🎯", "group": "direction"},
    "value":        {"icon": "💎", "group": "direction"},
    # Process & quality
    "sop":          {"icon": "📋", "group": "process"},
    "work_instruction": {"icon": "🔧", "group": "process"},
    "iso":          {"icon": "🛡", "group": "process"},
    # Knowledge & learning
    "decision":     {"icon": "⚖", "group": "knowledge"},
    "risk":         {"icon": "⚠", "group": "knowledge"},
    "idea":         {"icon": "💡", "group": "knowledge"},
    "lesson":       {"icon": "🎓", "group": "knowledge"},
    "research":     {"icon": "🔬", "group": "knowledge"},
    # People & relations
    "hr":           {"icon": "👥", "group": "people"},
    "customer":     {"icon": "🤝", "group": "people"},
    "partner":      {"icon": "🔗", "group": "people"},
    # Operations
    "project":      {"icon": "📁", "group": "ops"},
    "contract":     {"icon": "📜", "group": "ops"},
    "meeting":      {"icon": "🗒", "group": "ops"},
    "market":       {"icon": "📈", "group": "ops"},
    # Catch-all
    "general":      {"icon": "📄", "group": "knowledge"},
}

# Per-group accent colour — drives the knowledge-graph node colouring so the
# map reads at a glance (Obsidian-graph inspiration from the Master Prompt).
GROUP_COLORS: dict[str, str] = {
    "direction": "#4d6c5c",   # nirva green — north star
    "process":   "#c5963d",   # amber — how we work
    "knowledge": "#5b7fa6",   # blue — what we learned
    "people":    "#a65b7f",   # rose — who
    "ops":       "#7e7e8c",   # slate — running the business
}

STATUSES: dict[str, dict] = {
    "draft":    {"color": "#9a9485"},
    "active":   {"color": "#4d6c5c"},
    "archived": {"color": "#b0a89a"},
}

# Edge semantics — how one node relates to another.
RELATIONS: list[str] = [
    "relates_to", "depends_on", "derived_from",
    "part_of", "references", "supersedes", "owns",
]


def type_meta(node_type: str) -> dict:
    return NODE_TYPES.get(node_type, NODE_TYPES["general"])


def type_color(node_type: str) -> str:
    return GROUP_COLORS.get(type_meta(node_type)["group"], "#7e7e8c")


# ---- Schema -----------------------------------------------------------------

def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS kh_nodes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type   TEXT DEFAULT 'general',
                title       TEXT NOT NULL,
                body        TEXT DEFAULT '',
                tags        TEXT DEFAULT '',
                status      TEXT DEFAULT 'active',
                source      TEXT DEFAULT 'manual',
                ref_key     TEXT DEFAULT '',
                pinned      INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                updated_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS kh_edges (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                src_id      INTEGER REFERENCES kh_nodes(id) ON DELETE CASCADE,
                dst_id      INTEGER REFERENCES kh_nodes(id) ON DELETE CASCADE,
                relation    TEXT DEFAULT 'relates_to',
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(src_id, dst_id, relation)
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_kh_nodes_type ON kh_nodes(node_type)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_kh_nodes_status ON kh_nodes(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_kh_edges_src ON kh_edges(src_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_kh_edges_dst ON kh_edges(dst_id)")


# ---- Nodes: CRUD ------------------------------------------------------------

def add_node(title: str, *, body: str = "", node_type: str = "general",
             tags: str = "", status: str = "active",
             source: str = "manual", ref_key: str = "",
             pinned: bool = False) -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO kh_nodes (title, body, node_type, tags, status, "
            "source, ref_key, pinned) VALUES (?,?,?,?,?,?,?,?)",
            (title, body, node_type, tags, status, source, ref_key, int(pinned)),
        )
        return cur.lastrowid


def update_node(node_id: int, *, title: str | None = None, body: str | None = None,
                node_type: str | None = None, tags: str | None = None,
                status: str | None = None, pinned: bool | None = None) -> None:
    sets, params = [], []
    for col, val in (
        ("title", title), ("body", body), ("node_type", node_type),
        ("tags", tags), ("status", status),
    ):
        if val is not None:
            sets.append(f"{col}=?")
            params.append(val)
    if pinned is not None:
        sets.append("pinned=?")
        params.append(int(pinned))
    if not sets:
        return
    sets.append("updated_at=datetime('now','localtime')")
    params.append(node_id)
    with db.conn() as c:
        c.execute(f"UPDATE kh_nodes SET {', '.join(sets)} WHERE id=?", params)


def delete_node(node_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM kh_nodes WHERE id=?", (node_id,))


def get_node(node_id: int) -> dict | None:
    with db.conn() as c:
        r = c.execute("SELECT * FROM kh_nodes WHERE id=?", (node_id,)).fetchone()
    return _decorate(dict(r)) if r else None


def list_nodes(*, node_type: str | None = None, status: str | None = None,
               search: str | None = None, tag: str | None = None,
               limit: int = 200) -> list[dict]:
    conditions, params = [], []
    if node_type:
        conditions.append("node_type=?")
        params.append(node_type)
    if status:
        conditions.append("status=?")
        params.append(status)
    if search:
        conditions.append("(title LIKE ? OR body LIKE ? OR tags LIKE ?)")
        like = f"%{search}%"
        params += [like, like, like]
    if tag:
        conditions.append("tags LIKE ?")
        params.append(f"%{tag}%")
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM kh_nodes " + where +
            " ORDER BY pinned DESC, updated_at DESC LIMIT ?",
            params + [limit],
        ).fetchall()
    return [_decorate(dict(r)) for r in rows]


def _decorate(d: dict) -> dict:
    """Attach presentation helpers so pages don't repeat lookups."""
    meta = type_meta(d.get("node_type", "general"))
    d["type_icon"] = meta["icon"]
    d["type_color"] = type_color(d.get("node_type", "general"))
    d["status_color"] = STATUSES.get(d.get("status", "active"),
                                     STATUSES["active"])["color"]
    return d


# ---- Edges: the graph -------------------------------------------------------

def link(src_id: int, dst_id: int, relation: str = "relates_to") -> int | None:
    """Connect two nodes. No self-loops; duplicates are ignored."""
    if src_id == dst_id:
        return None
    with db.conn() as c:
        cur = c.execute(
            "INSERT OR IGNORE INTO kh_edges (src_id, dst_id, relation) "
            "VALUES (?,?,?)", (src_id, dst_id, relation),
        )
        return cur.lastrowid


def unlink(edge_id: int) -> None:
    with db.conn() as c:
        c.execute("DELETE FROM kh_edges WHERE id=?", (edge_id,))


def neighbors(node_id: int) -> list[dict]:
    """Every node directly connected to ``node_id`` (either direction).

    Each item: edge_id, relation, direction ('out'|'in'), and the linked
    node's id / title / type for rendering.
    """
    with db.conn() as c:
        rows = c.execute(
            """
            SELECT e.id AS edge_id, e.relation, 'out' AS direction,
                   n.id, n.title, n.node_type
              FROM kh_edges e JOIN kh_nodes n ON n.id = e.dst_id
             WHERE e.src_id = ?
            UNION ALL
            SELECT e.id AS edge_id, e.relation, 'in' AS direction,
                   n.id, n.title, n.node_type
              FROM kh_edges e JOIN kh_nodes n ON n.id = e.src_id
             WHERE e.dst_id = ?
            ORDER BY relation
            """,
            (node_id, node_id),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["type_icon"] = type_meta(d["node_type"])["icon"]
        out.append(d)
    return out


def graph(limit: int = 120) -> tuple[list[dict], list[dict]]:
    """Return (nodes, edges) for visualization. Nodes capped for readability."""
    with db.conn() as c:
        nrows = c.execute(
            "SELECT id, title, node_type, status FROM kh_nodes "
            "ORDER BY pinned DESC, updated_at DESC LIMIT ?", (limit,),
        ).fetchall()
        ids = tuple(r["id"] for r in nrows)
        edges: list[dict] = []
        if ids:
            qs = ",".join("?" * len(ids))
            erows = c.execute(
                f"SELECT src_id, dst_id, relation FROM kh_edges "
                f"WHERE src_id IN ({qs}) AND dst_id IN ({qs})",
                ids + ids,
            ).fetchall()
            edges = [dict(r) for r in erows]
    nodes = [_decorate(dict(r)) for r in nrows]
    return nodes, edges


# ---- Integration API (for other Nirva modules) -----------------------------

def capture(node_type: str, title: str, *, body: str = "", tags: str = "",
            source: str, ref_key: str = "", status: str = "active") -> int:
    """Push knowledge INTO the Hub from another system.

    Idempotent per (source, ref_key, node_type) when ``ref_key`` is given —
    re-capturing the same thing updates it instead of creating a duplicate, so
    a module can safely sync on every change. Returns the node id.
    """
    if ref_key:
        with db.conn() as c:
            existing = c.execute(
                "SELECT id FROM kh_nodes WHERE source=? AND ref_key=? "
                "AND node_type=?", (source, ref_key, node_type),
            ).fetchone()
        if existing:
            update_node(existing["id"], title=title, body=body,
                        tags=tags, status=status)
            return existing["id"]
    return add_node(title, body=body, node_type=node_type, tags=tags,
                    status=status, source=source, ref_key=ref_key)


def capture_policy_change(
    platform: str,
    *,
    url: str = "",
    diffs: list | None = None,
    notes: str = "",
    effective_date: str = "",
    ref_key: str,
    node_type: str = "market",
) -> int:
    """Record a marketplace fee/policy event in the Knowledge Hub.

    Idempotent per ``ref_key`` — safe to call from cron on every policy check
    or when the user applies fee updates on the Policies page.
    """
    init()
    lines = [f"Platform: {platform.upper()}"]
    if url:
        lines.append(f"Source: {url}")
    if effective_date:
        lines.append(f"Effective: {effective_date}")
    if diffs:
        lines.append("\nFee changes:")
        for d in diffs:
            lines.append(
                f"  • {d['field']}: {d['old']:.2f}% → {d['new']:.2f}% "
                f"({d['delta']:+.2f}%)"
            )
    if notes:
        lines.append(f"\n{notes}")

    applied = ref_key.endswith(":applied")
    title = (
        f"{platform.upper()} fee config applied"
        if applied
        else f"{platform.upper()} marketplace policy changed"
    )
    return capture(
        node_type,
        title,
        body="\n".join(lines),
        tags=f"policy,{platform},fees,marketplace",
        source="policy_watcher",
        ref_key=ref_key,
        status="active",
    )


def search(query: str, *, limit: int = 20) -> list[dict]:
    """Read knowledge OUT of the Hub. Other modules / global search call this."""
    return list_nodes(search=query, limit=limit)


# ---- Stats ------------------------------------------------------------------

def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM kh_nodes").fetchone()[0]
        links = c.execute("SELECT COUNT(*) FROM kh_edges").fetchone()[0]
        pinned = c.execute(
            "SELECT COUNT(*) FROM kh_nodes WHERE pinned=1").fetchone()[0]
        by_type_rows = c.execute(
            "SELECT node_type, COUNT(*) AS n FROM kh_nodes "
            "GROUP BY node_type ORDER BY n DESC").fetchall()
    by_type = {r["node_type"]: r["n"] for r in by_type_rows}
    return {
        "nodes": total,
        "links": links,
        "pinned": pinned,
        "types_used": len(by_type),
        "by_type": by_type,
    }


# ---- Starter content (opt-in) ----------------------------------------------
# Seeded only when the user explicitly asks — Nirva invites, never forces.
def seed_starter() -> int:
    """Create a small starter graph (Vision → Mission → Values + a few SOP /
    decision stubs, all linked). Skips anything already present. Returns the
    number of nodes created."""
    starters = [
        ("vision", "Vision", "ทำไมองค์กรนี้ถึงมีอยู่ — ภาพอนาคตที่เราอยากไปให้ถึง",
         "north-star", True),
        ("mission", "Mission", "เราทำอะไรในทุก ๆ วันเพื่อไปสู่ Vision",
         "north-star", True),
        ("value", "Core Values", "หลักการที่เรายึดถือเวลาตัดสินใจ", "culture", True),
        ("sop", "SOP: ตัวอย่างขั้นตอนการทำงาน",
         "อธิบายขั้นตอนงานหลักทีละขั้น เพื่อให้ความรู้ไม่หายไปกับคน", "process", False),
        ("decision", "Decision Log: ตัวอย่างการตัดสินใจ",
         "บันทึกว่าตัดสินใจอะไร เพราะอะไร ใครเกี่ยวข้อง", "log", False),
    ]
    created: dict[str, int] = {}
    n = 0
    for node_type, title, body, tags, pinned in starters:
        existing = list_nodes(node_type=node_type, limit=1)
        if existing:
            created[node_type] = existing[0]["id"]
            continue
        nid = add_node(title, body=body, node_type=node_type, tags=tags,
                       status="draft", source="seed", pinned=pinned)
        created[node_type] = nid
        n += 1
    # Wire the starter relationships into a tiny graph.
    if "vision" in created and "mission" in created:
        link(created["mission"], created["vision"], "derived_from")
    if "value" in created and "vision" in created:
        link(created["value"], created["vision"], "relates_to")
    if "sop" in created and "mission" in created:
        link(created["sop"], created["mission"], "part_of")
    if "decision" in created and "vision" in created:
        link(created["decision"], created["vision"], "references")
    return n
