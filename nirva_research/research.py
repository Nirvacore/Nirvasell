"""NIRVA RESEARCH — operational knowledge loader, validator & decision-ready
reporter.

Loads the operational knowledge layer (domains, SOPs, business rules, automation
opportunities, compliance risks) and validates that every reference into the
standards knowledge graph (`standards_kb`) and the NIRVA OS blueprint
(`nirva_os`) resolves — so operational rules stay anchored to the controls,
standards and products they implement.

Pure standard library. CLI::

    python -m nirva_research.research            # validate + summary
    python -m nirva_research.research --brief     # decision-ready domain briefs
    python -m nirva_research.research --risks      # risk register (sorted)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from standards_kb.graph import Graph
from nirva_os.blueprint import load_all as load_nirva_os

DATA_DIR = Path(__file__).resolve().parent / "data"
_FILES = ["domains", "business_rules", "sops", "automation", "compliance_risks"]

_SEV_ORDER = {"high": 0, "medium": 1, "low": 2}


def _load(name: str) -> dict:
    with (DATA_DIR / f"{name}.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def load_all() -> dict:
    return {name: _load(name) for name in _FILES}


def validate(data: dict, g: Graph, nos: dict) -> list[str]:
    errs: list[str] = []
    ctl_ids, std_ids = set(g.controls), set(g.standards)
    domain_ids = {d["id"] for d in data["domains"]["domains"]}
    rule_ids = {r["id"] for r in data["business_rules"]["rules"]}
    blueprint_ids = {b["id"] for b in nos["blueprints"]["blueprints"]}
    product_ids = {p["id"] for p in nos["products"]["products"]}
    # Valid product/module references: GTM products + group pillars + NIRVA modules.
    valid_products = set(product_ids)
    for pillar in nos["group_structure"]["pillars"]:
        valid_products.add(pillar["id"])
        valid_products.update(pillar.get("modules", {}).keys())

    def check_std_ctl(tag: str, obj: dict) -> None:
        for c in obj.get("controls", []):
            if c not in ctl_ids:
                errs.append(f"{tag}: unknown control '{c}'")
        for s in obj.get("standards", []):
            if s not in std_ids:
                errs.append(f"{tag}: unknown standard '{s}'")

    for d in data["domains"]["domains"]:
        check_std_ctl(f"domain {d['id']}", d)
        if d.get("blueprint") and d["blueprint"] not in blueprint_ids:
            errs.append(f"domain {d['id']}: unknown blueprint '{d['blueprint']}'")
    for r in data["business_rules"]["rules"]:
        check_std_ctl(f"rule {r['id']}", r)
        if r["domain"] not in domain_ids:
            errs.append(f"rule {r['id']}: unknown domain '{r['domain']}'")
    for s in data["sops"]["sops"]:
        check_std_ctl(f"sop {s['id']}", s)
        if s["domain"] not in domain_ids:
            errs.append(f"sop {s['id']}: unknown domain '{s['domain']}'")
        for rid in s.get("rules", []):
            if rid not in rule_ids:
                errs.append(f"sop {s['id']}: unknown rule '{rid}'")
    for a in data["automation"]["opportunities"]:
        if a["domain"] not in domain_ids:
            errs.append(f"automation {a['id']}: unknown domain '{a['domain']}'")
        prod = a.get("product", "")
        base = prod.split(".")[0]  # allow dotted sub-module refs e.g. NirvaCore.Payroll
        if prod and prod not in valid_products and base not in valid_products:
            errs.append(f"automation {a['id']}: unknown product '{prod}'")
        for rid in a.get("rules", []):
            if rid not in rule_ids:
                errs.append(f"automation {a['id']}: unknown rule '{rid}'")
    for rk in data["compliance_risks"]["risks"]:
        check_std_ctl(f"risk {rk['id']}", rk)
        if rk["domain"] not in domain_ids:
            errs.append(f"risk {rk['id']}: unknown domain '{rk['domain']}'")
        for rid in rk.get("rules", []):
            if rid not in rule_ids:
                errs.append(f"risk {rk['id']}: unknown rule '{rid}'")
    return errs


def domain_briefs(data: dict) -> str:
    rules_by_dom: dict[str, int] = {}
    sops_by_dom: dict[str, int] = {}
    aut_by_dom: dict[str, int] = {}
    risk_by_dom: dict[str, int] = {}
    for r in data["business_rules"]["rules"]:
        rules_by_dom[r["domain"]] = rules_by_dom.get(r["domain"], 0) + 1
    for s in data["sops"]["sops"]:
        sops_by_dom[s["domain"]] = sops_by_dom.get(s["domain"], 0) + 1
    for a in data["automation"]["opportunities"]:
        aut_by_dom[a["domain"]] = aut_by_dom.get(a["domain"], 0) + 1
    for rk in data["compliance_risks"]["risks"]:
        risk_by_dom[rk["domain"]] = risk_by_dom.get(rk["domain"], 0) + 1
    out = ["Decision-ready domain briefs", "=" * 60,
           f"{'Domain':28} {'Pri':5} {'Rules':>5} {'SOPs':>5} {'Auto':>5} {'Risk':>5}"]
    for d in data["domains"]["domains"]:
        out.append(f"{d['name']:28} {d['priority']:5} "
                   f"{rules_by_dom.get(d['id'],0):>5} {sops_by_dom.get(d['id'],0):>5} "
                   f"{aut_by_dom.get(d['id'],0):>5} {risk_by_dom.get(d['id'],0):>5}")
    return "\n".join(out)


def risk_report(data: dict) -> str:
    out = ["Compliance risk register (by likelihood×impact)", "=" * 60]
    risks = sorted(data["compliance_risks"]["risks"],
                   key=lambda r: (_SEV_ORDER[r["likelihood"]] + _SEV_ORDER[r["impact"]]))
    for r in risks:
        out.append(f"  [{r['likelihood'][:1].upper()}×{r['impact'][:1].upper()}] "
                   f"{r['id']} {r['name']}  → rules {','.join(r.get('rules', [])) or '-'}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    g = Graph.load()
    nos = load_nirva_os()
    data = load_all()
    errs = validate(data, g, nos)

    print("NIRVA RESEARCH — Operational Knowledge System")
    print("=" * 50)
    print(f"  domains              {len(data['domains']['domains'])}")
    print(f"  business rules       {len(data['business_rules']['rules'])}")
    print(f"  SOPs                 {len(data['sops']['sops'])}")
    print(f"  automation opps      {len(data['automation']['opportunities'])}")
    print(f"  compliance risks     {len(data['compliance_risks']['risks'])}")
    print(f"  linked to            {len(g.standards)} standards / {len(g.controls)} controls / "
          f"{len(nos['products']['products'])} products")

    if "--brief" in argv:
        print("\n" + domain_briefs(data))
    if "--risks" in argv:
        print("\n" + risk_report(data))

    if errs:
        print(f"\n❌ {len(errs)} cross-link error(s):")
        for e in errs:
            print(f"   - {e}")
        return 1
    print("\n✅ All operational knowledge → standards_kb / nirva_os links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
