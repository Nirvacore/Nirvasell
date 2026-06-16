"""Standards Knowledge Graph — browse the Nirva Universal Compliance Engine.

One Data · One Evidence · Many Standards. Explore controls, evidence reuse,
and which standards each universal control satisfies."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, empty_state
from i18n import t

st.set_page_config(page_title="nirva.sell · Standards",
                   page_icon="📚", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="📚", title=t("skb.title"), subtitle=t("skb.caption"))

try:
    from standards_kb.graph import Graph
    g = Graph.load()
    errs = g.validate()
    graph_ok = not errs
except Exception as e:
    graph_ok = False
    g = None
    load_err = str(e)

if not graph_ok:
    empty_state(
        icon="📚",
        title=t("skb.missing_title"),
        body=t("skb.missing_body"),
    )
    st.code("python3 -m standards_kb.seed_data", language="bash")
    if not g:
        st.caption(load_err)
    st.stop()

summary = g.summary()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("📜 " + t("skb.kpi_standards"), str(summary["standards"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🛡 " + t("skb.kpi_controls"), str(summary["controls"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("📎 " + t("skb.kpi_evidence"), str(summary["evidence_artifacts"]),
                     hint="", hint_tone="info")
with k4:
    metric_with_hint("🔗 " + t("skb.kpi_edges"), str(summary["edges"]),
                     hint="", hint_tone="info")

st.divider()

tab_ctrl, tab_std, tab_ev, tab_erp = st.tabs([
    "🛡 " + t("skb.tab_controls"),
    "📜 " + t("skb.tab_standards"),
    "📎 " + t("skb.tab_evidence"),
    "🏭 " + t("skb.tab_erp"),
])

with tab_ctrl:
    st.markdown("#### " + t("skb.controls_title"))
    st.caption(t("skb.controls_caption"))
    rows = []
    for cid in sorted(g.controls, key=g.reuse_factor, reverse=True):
        c = g.controls[cid]
        rows.append({
            t("skb.col_control"): f"{cid} — {c['name']}",
            t("skb.col_reuse"): g.reuse_factor(cid),
            t("skb.col_domains"): ", ".join(c.get("domains", [])),
            t("skb.col_standards"): len(c.get("satisfies", {})),
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    pick = st.selectbox(
        t("skb.pick_control"),
        sorted(g.controls.keys()),
        format_func=lambda k: f"{k} — {g.controls[k]['name']}",
        key="_skb_ctrl",
    )
    if pick:
        c = g.controls[pick]
        st.markdown(f"**{c['name']}** · reuse ×{g.reuse_factor(pick)}")
        sat_rows = [
            {"Standard": sid, "Clause / ref": ref}
            for sid, ref in sorted(c.get("satisfies", {}).items())
        ]
        st.dataframe(pd.DataFrame(sat_rows), width="stretch", hide_index=True)
        ev = [e for e in g.evidence.values()
              if pick in e.get("controls", [])]
        if ev:
            st.markdown("**" + t("skb.proves_evidence") + "**")
            for e in ev:
                auto = "🤖" if e.get("auto_collectable") else "👤"
                st.markdown(f"- {auto} **{e['id']}** — {e['name']}")

with tab_std:
    q = st.text_input(t("skb.search_std"), key="_skb_q",
                      placeholder=t("skb.search_std_ph"),
                      label_visibility="collapsed")
    std_rows = []
    for s in g.standards.values():
        if q and q.lower() not in s["id"].lower() and q.lower() not in s.get("name", "").lower():
            continue
        std_rows.append({
            t("skb.col_id"): s["id"],
            t("skb.col_org"): s.get("org", ""),
            t("skb.col_domains"): ", ".join(s.get("taxonomy", [])),
            t("skb.col_controls"): len(g.controls_for_standard(s["id"])),
            t("skb.col_evidence"): len(g.evidence_for_standard(s["id"])),
        })
    if not std_rows:
        st.info(t("skb.no_match"))
    else:
        st.dataframe(pd.DataFrame(std_rows), width="stretch", hide_index=True)

with tab_ev:
    st.markdown("#### " + t("skb.evidence_title"))
    st.caption(t("skb.evidence_caption"))
    ev_rows = []
    for e in g.evidence.values():
        reach = set()
        for cid in e.get("controls", []):
            reach.update(g.controls.get(cid, {}).get("satisfies", {}))
        ev_rows.append({
            t("skb.col_evidence"): e["id"],
            t("skb.col_name"): e["name"],
            t("skb.col_auto"): "🤖" if e.get("auto_collectable") else "👤",
            t("skb.col_controls"): len(e.get("controls", [])),
            t("skb.col_reach"): len(reach),
        })
    st.dataframe(pd.DataFrame(ev_rows), width="stretch", hide_index=True)

with tab_erp:
    st.markdown("#### " + t("skb.erp_title"))
    st.caption(t("skb.erp_caption"))
    erp_rows = []
    for m in g.modules:
        erp_rows.append({
            t("skb.col_module"): m["module"],
            t("skb.col_domains"): ", ".join(m.get("domains", [])),
            t("skb.col_standards"): len(m.get("standards", [])),
            t("skb.col_controls"): len(m.get("controls", [])),
        })
    st.dataframe(pd.DataFrame(erp_rows), width="stretch", hide_index=True)

st.divider()
st.caption(t("skb.footer"))
