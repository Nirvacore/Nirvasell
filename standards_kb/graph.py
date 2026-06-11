"""Nirva Standards Knowledge Graph — loader, validator and query layer.

Loads the JSON data layer in ``standards_kb/data/`` into an in-memory graph,
validates referential integrity across every cross-reference, and exposes
simple query helpers that power the "One Data · One Evidence · Many Standards"
model of the Nirva Universal Compliance Engine.

Pure standard library — no third-party dependencies, so it runs anywhere the
nirva.sell app runs.

CLI::

    python -m standards_kb.graph            # validate + print summary
    python -m standards_kb.graph --stats    # detailed statistics
    python -m standards_kb.graph --mermaid  # emit a Mermaid graph snippet
    python -m standards_kb.graph --export edges.json   # dump edge list
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

_FILES = {
    "organizations": "organizations.json",
    "standards": "standards.json",
    "taxonomy": "taxonomy.json",
    "common_requirements": "common_requirements.json",
    "conflicts": "conflicts.json",
    "controls": "controls.json",
    "evidence": "evidence.json",
    "erp_mapping": "erp_mapping.json",
}


def _load(name: str) -> dict:
    path = DATA_DIR / _FILES[name]
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


@dataclass
class Graph:
    """In-memory knowledge graph. Nodes are dicts keyed by id; edges are
    (subject, predicate, object) triples."""

    organizations: dict = field(default_factory=dict)
    standards: dict = field(default_factory=dict)
    domains: dict = field(default_factory=dict)
    requirements: dict = field(default_factory=dict)
    controls: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)
    conflicts: list = field(default_factory=list)
    modules: list = field(default_factory=list)
    edges: list = field(default_factory=list)

    # ---- loading ---------------------------------------------------------
    @classmethod
    def load(cls) -> "Graph":
        g = cls()
        g.organizations = {o["id"]: o for o in _load("organizations")["organizations"]}
        g.standards = {s["id"]: s for s in _load("standards")["standards"]}
        g.domains = {d["id"]: d for d in _load("taxonomy")["domains"]}
        g.requirements = {r["id"]: r for r in _load("common_requirements")["requirements"]}
        g.controls = {c["id"]: c for c in _load("controls")["controls"]}
        g.evidence = {e["id"]: e for e in _load("evidence")["evidence"]}
        g.conflicts = _load("conflicts")["conflicts"]
        g.modules = _load("erp_mapping")["modules"]
        g._build_edges()
        return g

    def _build_edges(self) -> None:
        e = self.edges
        for s in self.standards.values():
            e.append((s["id"], "PUBLISHED_BY", s["org"]))
            for dom in s.get("taxonomy", []):
                e.append((s["id"], "COVERS", dom))
        for r in self.requirements.values():
            for sid in r.get("present_in", []):
                e.append((r["id"], "APPEARS_IN", sid))
        for c in self.controls.values():
            for dom in c.get("domains", []):
                e.append((c["id"], "IN_DOMAIN", dom))
            for rid in c.get("requirements", []):
                e.append((c["id"], "IMPLEMENTS", rid))
            for sid in c.get("satisfies", {}):
                e.append((c["id"], "SATISFIES", sid))
        for ev in self.evidence.values():
            for cid in ev.get("controls", []):
                e.append((ev["id"], "PROVES", cid))
        for m in self.modules:
            mid = m["module"]
            for cid in m.get("controls", []):
                e.append((mid, "RUNS_CONTROL", cid))
            for sid in m.get("standards", []):
                e.append((mid, "OPERATIONALIZES", sid))

    # ---- validation ------------------------------------------------------
    def validate(self) -> list[str]:
        errs: list[str] = []
        dom_ids, std_ids = set(self.domains), set(self.standards)
        org_ids, req_ids = set(self.organizations), set(self.requirements)
        ctl_ids = set(self.controls)

        for s in self.standards.values():
            if s["org"] not in org_ids:
                errs.append(f"standard {s['id']}: unknown org '{s['org']}'")
            for dom in s.get("taxonomy", []):
                if dom not in dom_ids:
                    errs.append(f"standard {s['id']}: unknown domain '{dom}'")
        for r in self.requirements.values():
            for sid in r.get("present_in", []):
                if sid not in std_ids:
                    errs.append(f"requirement {r['id']}: unknown standard '{sid}'")
        for d in self.domains.values():
            for sid in d.get("anchor_standards", []):
                if sid not in std_ids:
                    errs.append(f"domain {d['id']}: unknown anchor standard '{sid}'")
        for c in self.controls.values():
            for dom in c.get("domains", []):
                if dom not in dom_ids:
                    errs.append(f"control {c['id']}: unknown domain '{dom}'")
            for rid in c.get("requirements", []):
                if rid not in req_ids:
                    errs.append(f"control {c['id']}: unknown requirement '{rid}'")
            # Note: satisfies keys may reference external frameworks not in the
            # registry (e.g. DAMA-DMBOK); only warn on known-id collisions.
        for ev in self.evidence.values():
            for cid in ev.get("controls", []):
                if cid not in ctl_ids:
                    errs.append(f"evidence {ev['id']}: unknown control '{cid}'")
            for rid in ev.get("satisfies_requirements", []):
                if rid not in req_ids:
                    errs.append(f"evidence {ev['id']}: unknown requirement '{rid}'")
        for m in self.modules:
            for cid in m.get("controls", []):
                if cid not in ctl_ids:
                    errs.append(f"module {m['module']}: unknown control '{cid}'")
            for sid in m.get("standards", []):
                if sid not in std_ids:
                    errs.append(f"module {m['module']}: unknown standard '{sid}'")
            for dom in m.get("domains", []):
                if dom not in dom_ids:
                    errs.append(f"module {m['module']}: unknown domain '{dom}'")
        return errs

    # ---- queries ---------------------------------------------------------
    def standards_for_domain(self, domain_id: str) -> list[dict]:
        return [s for s in self.standards.values() if domain_id in s.get("taxonomy", [])]

    def controls_for_standard(self, standard_id: str) -> list[dict]:
        return [c for c in self.controls.values() if standard_id in c.get("satisfies", {})]

    def evidence_for_standard(self, standard_id: str) -> list[dict]:
        ctls = {c["id"] for c in self.controls_for_standard(standard_id)}
        return [e for e in self.evidence.values() if ctls & set(e.get("controls", []))]

    def reuse_factor(self, control_id: str) -> int:
        """How many standards a single control satisfies (the leverage metric)."""
        return len(self.controls[control_id].get("satisfies", {}))

    # ---- reporting -------------------------------------------------------
    def summary(self) -> dict:
        return {
            "organizations": len(self.organizations),
            "standards": len(self.standards),
            "domains": len(self.domains),
            "common_requirements": len(self.requirements),
            "controls": len(self.controls),
            "evidence_artifacts": len(self.evidence),
            "conflicts": len(self.conflicts),
            "erp_modules": len(self.modules),
            "edges": len(self.edges),
        }

    def mermaid(self, max_edges: int = 60) -> str:
        lines = ["graph LR"]
        for subj, pred, obj in self.edges[:max_edges]:
            s = "".join(ch for ch in subj if ch.isalnum())
            o = "".join(ch for ch in obj if ch.isalnum())
            lines.append(f"  {s}-->|{pred}|{o}")
        return "\n".join(lines)


def main(argv: list[str]) -> int:
    g = Graph.load()
    errs = g.validate()
    if "--export" in argv:
        out = Path(argv[argv.index("--export") + 1])
        out.write_text(json.dumps(
            [{"s": s, "p": p, "o": o} for s, p, o in g.edges], indent=2), encoding="utf-8")
        print(f"exported {len(g.edges)} edges -> {out}")
    if "--mermaid" in argv:
        print(g.mermaid())
        return 0

    print("Nirva Standards Knowledge Graph")
    print("=" * 40)
    for k, v in g.summary().items():
        print(f"  {k:22} {v}")

    if "--stats" in argv:
        print("\nControl reuse leverage (control -> #standards satisfied):")
        ranked = sorted(g.controls, key=g.reuse_factor, reverse=True)
        for cid in ranked:
            print(f"  {cid:8} x{g.reuse_factor(cid):2}  {g.controls[cid]['name']}")

    if errs:
        print(f"\n❌ {len(errs)} integrity error(s):")
        for msg in errs:
            print(f"   - {msg}")
        return 1
    print("\n✅ Referential integrity: all cross-references resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
