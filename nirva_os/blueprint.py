"""NIRVA OS blueprint loader + cross-link validator.

Loads the NIRVA OS data layer (products, problems, layers, blueprints,
revenue, group structure) and validates that every reference into the
standards knowledge graph (control IDs ``UC-*`` and standard IDs) resolves —
so the strategy layer stays wired to the compliance foundation.

Pure standard library. CLI::

    python -m nirva_os.blueprint            # validate + summary
    python -m nirva_os.blueprint --coverage # problem/product coverage report
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from standards_kb.graph import Graph

DATA_DIR = Path(__file__).resolve().parent / "data"

_FILES = ["group_structure", "layers", "products", "problems",
          "blueprints", "competitors", "revenue"]


def _load(name: str) -> dict:
    with (DATA_DIR / f"{name}.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def load_all() -> dict:
    return {name: _load(name) for name in _FILES}


def validate(data: dict, g: Graph) -> list[str]:
    errs: list[str] = []
    ctl_ids, std_ids, dom_ids = set(g.controls), set(g.standards), set(g.domains)

    def check_refs(obj_id: str, obj: dict) -> None:
        for cid in obj.get("controls", []):
            if cid not in ctl_ids:
                errs.append(f"{obj_id}: unknown control '{cid}'")
        for sid in obj.get("standards", []):
            # blueprints may reference standards flagged for future addition
            if sid not in std_ids:
                errs.append(f"{obj_id}: unknown standard '{sid}'")

    for p in data["products"]["products"]:
        check_refs(f"product {p['id']}", p)
        if p["layer"] not in {l["id"] for l in data["layers"]["layers"]}:
            errs.append(f"product {p['id']}: unknown layer '{p['layer']}'")
    for pr in data["problems"]["problems"]:
        check_refs(f"problem {pr['id']}", pr)
    for ly in data["layers"]["layers"]:
        for cid in ly.get("controls", []):
            if cid not in ctl_ids:
                errs.append(f"layer {ly['id']}: unknown control '{cid}'")
        for dom in ly.get("domains", []):
            if dom not in dom_ids:
                errs.append(f"layer {ly['id']}: unknown domain '{dom}'")
    return errs


def cross_check_problem_product(data: dict) -> list[str]:
    """Every problem must be solved by >=1 product, and every product's
    `solves` must reference real problems."""
    warns: list[str] = []
    problem_ids = {p["id"] for p in data["problems"]["problems"]}
    solved = set()
    for p in data["products"]["products"]:
        for pid in p.get("solves", []):
            if pid not in problem_ids:
                warns.append(f"product {p['id']}: solves unknown problem '{pid}'")
            solved.add(pid)
    for pid in problem_ids - solved:
        warns.append(f"problem {pid}: not mapped to any product")
    return warns


def coverage_report(data: dict, g: Graph) -> str:
    out = ["Problem → Product coverage", "=" * 40]
    prod_by_problem: dict[str, list[str]] = {}
    for p in data["products"]["products"]:
        for pid in p.get("solves", []):
            prod_by_problem.setdefault(pid, []).append(p["id"])
    for pr in data["problems"]["problems"]:
        prods = ", ".join(prod_by_problem.get(pr["id"], ["—"]))
        std_reach = len({s for c in pr.get("controls", []) for s in
                         g.controls.get(c, {}).get("satisfies", {})})
        out.append(f"  {pr['name']:32} → {prods}  (std reach via controls: {std_reach})")
    out.append("")
    out.append("MVP launch order (by priority):")
    for p in sorted(data["products"]["products"], key=lambda x: x["mvp_priority"]):
        out.append(f"  {p['mvp_priority']}. {p['name']:18} ttr={p['ttr']}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    g = Graph.load()
    data = load_all()
    errs = validate(data, g)
    warns = cross_check_problem_product(data)

    print("NIRVA OS Blueprint")
    print("=" * 40)
    print(f"  group pillars        {len(data['group_structure']['pillars'])}")
    print(f"  layers               {len(data['layers']['layers'])}")
    print(f"  products             {len(data['products']['products'])}")
    print(f"  problems (atlas)     {len(data['problems']['problems'])}")
    print(f"  industry blueprints  {len(data['blueprints']['blueprints'])}")
    print(f"  competitor categories{len(data['competitors']['categories']):>4}")
    print(f"  revenue streams      {len(data['revenue']['streams'])}")
    print(f"  standards_kb nodes    {g.summary()['standards']} standards / "
          f"{g.summary()['controls']} controls (linked)")

    if "--coverage" in argv:
        print()
        print(coverage_report(data, g))

    if warns:
        print(f"\n⚠️  {len(warns)} coverage warning(s):")
        for w in warns:
            print(f"   - {w}")
    if errs:
        print(f"\n❌ {len(errs)} cross-link error(s):")
        for e in errs:
            print(f"   - {e}")
        return 1
    print("\n✅ All NIRVA OS → standards_kb cross-links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
