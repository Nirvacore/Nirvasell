"""Generate the data-driven matrix documents (Outputs #3, #4, #5) from the
knowledge graph so they stay exactly in sync with the JSON data layer.

Run::  python -m standards_kb.build_reports
"""
from __future__ import annotations

from pathlib import Path

from standards_kb.graph import Graph

DOCS = Path(__file__).resolve().parent / "docs"

# Framework columns used across the comparison matrix.
FRAMEWORKS = ["ISO9001", "ISO27001", "ISO42001", "SOC2", "COBIT", "ITIL",
              "NISTCSF", "GDPR", "ESRS"]


def _check(present: bool) -> str:
    return "✅" if present else "—"


def comparison_matrix(g: Graph) -> str:
    out = ["# Output 3 — Standards Comparison Matrix",
           "",
           "_Auto-generated from `standards_kb/data/`. Do not edit by hand — run "
           "`python -m standards_kb.build_reports`._",
           "",
           "## 3.1 Common-DNA × Framework coverage",
           "",
           "Rows = shared requirement primitives (Phase 4). A ✅ means the framework "
           "explicitly carries that requirement. The density of this matrix is the "
           "mathematical basis for *write-once-certify-many*.",
           "",
           "| Requirement (HS clause) | " + " | ".join(FRAMEWORKS) + " | Σ |",
           "|---|" + "|".join([":-:"] * len(FRAMEWORKS)) + "|:-:|"]
    for r in g.requirements.values():
        present = set(r.get("present_in", []))
        cells = [_check(f in present) for f in FRAMEWORKS]
        total = len(present)
        out.append(f"| **{r['name']}** ({r['hs_clause']}) | " +
                   " | ".join(cells) + f" | {total} |")
    # similarity ranking
    out += ["",
            "## 3.2 Cross-standard similarity (semantic overlap of expression)",
            "",
            "| Requirement | Similarity | Appears in N standards |",
            "|---|:-:|:-:|"]
    for r in sorted(g.requirements.values(), key=lambda x: x["similarity"], reverse=True):
        out.append(f"| {r['name']} | {r['similarity']:.2f} | {len(r['present_in'])} |")
    out += ["",
            "> **Reading:** requirements above ~0.85 (Context, Documented Information, "
            "Competence, Management Review, Policy) are near-identical across ISO "
            "management systems — implement the control once and reuse the evidence "
            "for every certification."]
    return "\n".join(out) + "\n"


def controls_matrix(g: Graph) -> str:
    out = ["# Output 4 — Universal Controls Matrix",
           "",
           "_Auto-generated from `standards_kb/data/`._",
           "",
           "One control, implemented once, satisfies many standards. "
           "`Reuse` = number of standards each control crosswalks to.",
           "",
           "| Control | Domains | Reuse | Standards satisfied (clause refs) |",
           "|---|---|:-:|---|"]
    for cid in sorted(g.controls, key=g.reuse_factor, reverse=True):
        c = g.controls[cid]
        doms = ",".join(c["domains"])
        sats = "; ".join(f"{k} ({v})" for k, v in c["satisfies"].items())
        out.append(f"| **{cid} — {c['name']}** | {doms} | {g.reuse_factor(cid)} | {sats} |")
    total_links = sum(g.reuse_factor(c) for c in g.controls)
    out += ["",
            f"**Leverage:** {len(g.controls)} universal controls collapse into "
            f"{total_links} standard-specific control instances — a "
            f"{total_links / len(g.controls):.1f}× reuse ratio.",
            "",
            "## 4.1 Control → Common Requirement (what each control implements)",
            "",
            "| Control | Implements requirements |",
            "|---|---|"]
    for cid, c in g.controls.items():
        reqs = ", ".join(g.requirements[r]["name"] for r in c["requirements"])
        out.append(f"| {cid} | {reqs} |")
    return "\n".join(out) + "\n"


def evidence_matrix(g: Graph) -> str:
    out = ["# Output 5 — Universal Evidence Matrix",
           "",
           "_Auto-generated from `standards_kb/data/`._",
           "",
           "*One Evidence · Many Standards.* Each artifact is harvested once and "
           "proves multiple controls (and therefore many standards).",
           "",
           "| Evidence | Source | Auto? | Proves controls | Indirect standard reach |",
           "|---|---|:-:|---|:-:|"]
    for ev in g.evidence.values():
        ctls = ev.get("controls", [])
        reach = len({s for cid in ctls for s in g.controls[cid].get("satisfies", {})})
        auto = "🤖" if ev.get("auto_collectable") else "👤"
        out.append(f"| **{ev['id']} — {ev['name']}** | {ev['source']} | {auto} | "
                   f"{', '.join(ctls)} | {reach} |")
    auto_n = sum(1 for e in g.evidence.values() if e.get("auto_collectable"))
    out += ["",
            f"**Automation potential:** {auto_n}/{len(g.evidence)} evidence artifacts "
            "are machine-harvestable (🤖) directly from source systems — the rest "
            "(👤) need human attestation.",
            "",
            "## 5.1 Standard → Evidence pack (collect these to cover the standard)",
            "",
            "| Standard | Evidence artifacts needed |",
            "|---|---|"]
    for sid in ["ISO27001", "SOC2", "ISO42001", "GDPR", "ISO9001", "ESRS"]:
        evs = g.evidence_for_standard(sid)
        names = ", ".join(e["id"] for e in evs)
        out.append(f"| {sid} | {names} |")
    return "\n".join(out) + "\n"


def main() -> None:
    g = Graph.load()
    (DOCS / "03_comparison_matrix.md").write_text(comparison_matrix(g), encoding="utf-8")
    (DOCS / "04_controls_matrix.md").write_text(controls_matrix(g), encoding="utf-8")
    (DOCS / "05_evidence_matrix.md").write_text(evidence_matrix(g), encoding="utf-8")
    print("Generated: 03_comparison_matrix.md, 04_controls_matrix.md, 05_evidence_matrix.md")


if __name__ == "__main__":
    main()
