"""Nirva Knowledge Hub — the Source of Truth at the center of the ecosystem.

Everything is a Node; every Node can link to any other Node. Browse the
knowledge graph, capture organizational knowledge (Vision, SOP, decisions,
risks, lessons…), and connect the dots. Master Prompt V3 · Priority 1.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import html

import streamlit as st
import db
import knowledge_hub as kh
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast, empty_state
from i18n import t

st.set_page_config(page_title="nirva.sell · Knowledge Hub",
                   page_icon="🧠", layout="wide")
apply_theme()
require_auth()
db.init()
kh.init()
render_sidebar()

page_header(icon="🧠", title=t("kh.title"), subtitle=t("kh.caption"))


def _type_label(key: str) -> str:
    return t("kh.type." + key)


def _type_options() -> list[str]:
    return list(kh.NODE_TYPES.keys())


def _esc(s: str) -> str:
    return html.escape(s or "")


# ---- KPIs -------------------------------------------------------------------
s = kh.stats()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("🧠 " + t("kh.kpi_nodes"), str(s["nodes"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🔗 " + t("kh.kpi_links"), str(s["links"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("🗂 " + t("kh.kpi_types"), str(s["types_used"]),
                     hint="", hint_tone="info")
with k4:
    metric_with_hint("📌 " + t("kh.kpi_pinned"), str(s["pinned"]),
                     hint="", hint_tone="info")

st.divider()

tab_overview, tab_browse, tab_add = st.tabs(
    ["🌐 " + t("kh.tab_overview"),
     "🔍 " + t("kh.tab_browse"),
     "➕ " + t("kh.tab_add")]
)

# ============================================================================
# OVERVIEW — knowledge graph + recent nodes
# ============================================================================
with tab_overview:
    if s["nodes"] == 0:
        empty_state(
            icon="🧠",
            title=t("kh.empty_title"),
            body=t("kh.empty_body"),
        )
        if st.button("🌱 " + t("kh.seed_btn"), type="primary", key="_kh_seed"):
            n = kh.seed_starter()
            toast(t("kh.seeded", n=n), icon="🌱")
            st.rerun()
    else:
        nodes, edges = kh.graph(limit=120)

        # Knowledge graph — rendered as a Graphviz DOT string (no extra deps;
        # Streamlit ships the client-side renderer). Colour = node group.
        st.markdown("#### " + t("kh.graph_title"))
        node_index = {n["id"]: n for n in nodes}
        dot_lines = [
            "graph kh {",
            "  bgcolor=\"transparent\";",
            "  layout=neato; overlap=false; splines=true; sep=\"+8\";",
            "  node [shape=circle, style=\"filled\", fontname=\"Inter\", "
            "fontsize=10, fontcolor=\"white\", color=\"white\", penwidth=1.4, "
            "fixedsize=false];",
            "  edge [color=\"#cfc8ba\", penwidth=1.0, fontname=\"Inter\", "
            "fontsize=8, fontcolor=\"#9a9485\"];",
        ]
        for n in nodes:
            label = (n["title"] or "")[:22].replace('"', "'")
            dot_lines.append(
                f'  n{n["id"]} [label="{n["type_icon"]} {label}", '
                f'fillcolor="{n["type_color"]}"];'
            )
        for e in edges:
            if e["src_id"] in node_index and e["dst_id"] in node_index:
                rel = kh.RELATIONS and e["relation"]
                dot_lines.append(
                    f'  n{e["src_id"]} -- n{e["dst_id"]} '
                    f'[label="{t("kh.rel." + e["relation"]) if rel else ""}"];'
                )
        dot_lines.append("}")
        dot = "\n".join(dot_lines)

        try:
            st.graphviz_chart(dot, use_container_width=True)
        except Exception:
            st.caption(t("kh.graph_unavailable"))

        # Legend — group → colour.
        legend = " &nbsp; ".join(
            f"<span style='display:inline-block;width:10px;height:10px;"
            f"border-radius:50%;background:{color};margin-right:4px'></span>"
            f"<span style='font-size:12px;color:#7a7569'>{t('kh.group.' + grp)}</span>"
            for grp, color in kh.GROUP_COLORS.items()
        )
        st.markdown(
            f"<div style='margin:4px 0 10px'>{legend}</div>",
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("#### " + t("kh.recent"))
        for n in nodes[:8]:
            st.markdown(
                "<div style='padding:8px 12px;border:0.5px solid rgba(40,30,20,0.07);"
                f"border-left:4px solid {n['type_color']};border-radius:8px;"
                "background:white;margin-bottom:6px'>"
                f"<span>{n['type_icon']} <strong>{_esc(n['title'])}</strong></span>"
                f"<span style='float:right;font-size:11px;color:{n['status_color']}'>"
                f"{_type_label(n['node_type'])}</span></div>",
                unsafe_allow_html=True,
            )

# ============================================================================
# BROWSE & EDIT — filter, select, edit, link
# ============================================================================
with tab_browse:
    fc1, fc2, fc3 = st.columns([2, 1, 1])
    with fc1:
        q = st.text_input(t("kh.search_ph"), key="_kh_q",
                          placeholder=t("kh.search_ph"),
                          label_visibility="collapsed")
    with fc2:
        ftype = st.selectbox(
            t("kh.filter_type"), ["all"] + _type_options(),
            format_func=lambda k: ("🗂 " + t("kh.all_types")) if k == "all"
            else kh.type_meta(k)["icon"] + " " + _type_label(k),
            key="_kh_ftype",
        )
    with fc3:
        fstatus = st.selectbox(
            t("kh.filter_status"), ["all"] + list(kh.STATUSES.keys()),
            format_func=lambda k: t("kh.all_status") if k == "all"
            else t("kh.status." + k),
            key="_kh_fstatus",
        )

    rows = kh.list_nodes(
        node_type=None if ftype == "all" else ftype,
        status=None if fstatus == "all" else fstatus,
        search=q.strip() or None,
    )

    if not rows:
        st.info(t("kh.empty_browse"))
    else:
        sel_id = st.session_state.get("_kh_sel")
        for n in rows:
            cols = st.columns([8, 1])
            with cols[0]:
                pin = "📌 " if n["pinned"] else ""
                tags_html = (
                    f" · <span style='font-size:11px;color:#9a9485'>"
                    f"{_esc(n['tags'])}</span>" if n.get("tags") else ""
                )
                st.markdown(
                    "<div style='padding:9px 13px;border:0.5px solid rgba(40,30,20,0.07);"
                    f"border-left:4px solid {n['type_color']};border-radius:8px;"
                    "background:white;margin-bottom:4px'>"
                    "<div style='display:flex;justify-content:space-between;"
                    "align-items:baseline'>"
                    f"<span>{pin}{n['type_icon']} <strong>{_esc(n['title'])}</strong>"
                    f"{tags_html}</span>"
                    f"<span style='font-size:11px;color:{n['status_color']};"
                    f"font-weight:600'>{_type_label(n['node_type'])} · "
                    f"{t('kh.status.' + n['status'])}</span></div>"
                    + (f"<div style='font-size:12px;color:#3d3530;margin-top:3px;"
                       f"white-space:pre-wrap'>{_esc(n['body'][:160])}</div>"
                       if n.get("body") else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )
            with cols[1]:
                if st.button(t("kh.edit_btn"), key=f"_kh_pick_{n['id']}",
                             type="tertiary"):
                    st.session_state["_kh_sel"] = (
                        None if sel_id == n["id"] else n["id"]
                    )
                    st.rerun()

        # ---- Detail / edit panel for the selected node ------------------
        sel_id = st.session_state.get("_kh_sel")
        if sel_id:
            node = kh.get_node(sel_id)
        if sel_id and node:
            st.divider()
            st.markdown(
                f"### {node['type_icon']} {_esc(node['title'])}"
            )
            with st.form(f"_kh_edit_{sel_id}"):
                e1, e2 = st.columns(2)
                with e1:
                    e_title = st.text_input(t("kh.f_title"), value=node["title"])
                    e_type = st.selectbox(
                        t("kh.f_type"), _type_options(),
                        index=_type_options().index(node["node_type"])
                        if node["node_type"] in _type_options() else 0,
                        format_func=lambda k: kh.type_meta(k)["icon"] + " "
                        + _type_label(k),
                    )
                with e2:
                    e_tags = st.text_input(t("kh.f_tags"), value=node["tags"])
                    e_status = st.selectbox(
                        t("kh.f_status"), list(kh.STATUSES.keys()),
                        index=list(kh.STATUSES.keys()).index(node["status"])
                        if node["status"] in kh.STATUSES else 1,
                        format_func=lambda k: t("kh.status." + k),
                    )
                e_body = st.text_area(t("kh.f_body"), value=node["body"],
                                      height=120)
                e_pin = st.checkbox(t("kh.f_pin"), value=bool(node["pinned"]))
                bc1, bc2 = st.columns(2)
                with bc1:
                    save = st.form_submit_button(t("kh.save_btn"),
                                                 type="primary")
                with bc2:
                    delete = st.form_submit_button(t("kh.delete_btn"))
            if save:
                kh.update_node(sel_id, title=e_title.strip(), body=e_body.strip(),
                               node_type=e_type, tags=e_tags.strip(),
                               status=e_status, pinned=e_pin)
                toast(t("kh.saved"), icon="✓")
                st.rerun()
            if delete:
                kh.delete_node(sel_id)
                st.session_state["_kh_sel"] = None
                toast(t("kh.deleted"), icon="✓")
                st.rerun()

            # ---- Links (the graph edges) -------------------------------
            st.markdown("#### 🔗 " + t("kh.links_title"))
            nbrs = kh.neighbors(sel_id)
            if nbrs:
                for nb in nbrs:
                    arrow = "→" if nb["direction"] == "out" else "←"
                    lc = st.columns([8, 1])
                    with lc[0]:
                        st.markdown(
                            "<div style='font-size:13px;color:#3d3530;"
                            "padding:3px 0'>"
                            f"{arrow} <em style='color:#9a9485'>"
                            f"{t('kh.rel.' + nb['relation'])}</em> &nbsp; "
                            f"{nb['type_icon']} {_esc(nb['title'])}</div>",
                            unsafe_allow_html=True,
                        )
                    with lc[1]:
                        if st.button(t("kh.unlink_btn"),
                                     key=f"_kh_unlink_{nb['edge_id']}",
                                     type="tertiary"):
                            kh.unlink(nb["edge_id"])
                            st.rerun()
            else:
                st.caption(t("kh.no_links"))

            # ---- Add a link --------------------------------------------
            others = [n for n in kh.list_nodes(limit=500) if n["id"] != sel_id]
            if others:
                with st.form(f"_kh_link_{sel_id}"):
                    glc1, glc2 = st.columns([1, 2])
                    with glc1:
                        rel = st.selectbox(
                            t("kh.link_relation"), kh.RELATIONS,
                            format_func=lambda r: t("kh.rel." + r),
                        )
                    with glc2:
                        target = st.selectbox(
                            t("kh.link_target"), others,
                            format_func=lambda n: n["type_icon"] + " " + n["title"],
                        )
                    if st.form_submit_button("🔗 " + t("kh.link_btn")):
                        kh.link(sel_id, target["id"], rel)
                        toast(t("kh.linked"), icon="🔗")
                        st.rerun()
        else:
            st.caption(t("kh.select_hint"))

# ============================================================================
# ADD — capture new knowledge
# ============================================================================
with tab_add:
    with st.form("_kh_add"):
        ac1, ac2 = st.columns(2)
        with ac1:
            a_title = st.text_input(t("kh.f_title"),
                                    placeholder=t("kh.title_ph"))
            a_type = st.selectbox(
                t("kh.f_type"), _type_options(),
                format_func=lambda k: kh.type_meta(k)["icon"] + " "
                + _type_label(k),
            )
        with ac2:
            a_tags = st.text_input(t("kh.f_tags"), placeholder=t("kh.tags_ph"))
            a_status = st.selectbox(
                t("kh.f_status"), list(kh.STATUSES.keys()),
                index=1,
                format_func=lambda k: t("kh.status." + k),
            )
        a_body = st.text_area(t("kh.f_body"), height=140)
        a_pin = st.checkbox(t("kh.f_pin"), value=False)
        if st.form_submit_button(t("kh.add_btn"), type="primary"):
            if a_title.strip():
                kh.add_node(a_title.strip(), body=a_body.strip(),
                            node_type=a_type, tags=a_tags.strip(),
                            status=a_status, pinned=a_pin)
                toast(t("kh.added"), icon="✓")
                st.rerun()
            else:
                st.warning(t("kh.need_title"))
