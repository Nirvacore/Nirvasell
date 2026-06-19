"""Customer Segments — RFM-lite ranking + tags for every buyer."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import customer_segments as cs
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Segments",
                   page_icon="👥", layout="wide")
apply_theme()
require_auth()
db.init()
cs.init()
render_sidebar()

page_header(icon="👥", title=t("seg.title"), subtitle=t("seg.caption"))

s = cs.stats()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("👥 " + t("seg.kpi_total"), str(s["total"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🏆 " + t("seg.kpi_champions"),
                     str(s["champions"]),
                     hint=t("seg.champions_hint"), hint_tone="ok")
with k3:
    metric_with_hint("⚠️ " + t("seg.kpi_risk"), str(s["at_risk"]),
                     hint=t("seg.risk_hint") if s["at_risk"] > 0 else "",
                     hint_tone="warn" if s["at_risk"] > 0 else "ok")
with k4:
    seg_counts = s.get("by_segment", {})
    metric_with_hint("💤 " + t("seg.kpi_dormant"),
                     str(seg_counts.get("dormant", 0)),
                     hint="", hint_tone="info")

st.divider()

# ---- Segment legends --------------------------------------------------------
st.markdown("### 🗂 " + t("seg.segments_title"))
legend_cols = st.columns(len(cs.RFM_SEGMENTS))
for i, (seg_key, seg_info) in enumerate(cs.RFM_SEGMENTS.items()):
    count = seg_counts.get(seg_key, 0)
    with legend_cols[i]:
        st.markdown(
            "<div style='text-align:center;padding:8px;border-radius:8px;"
            "border:0.5px solid rgba(40,30,20,0.08)'>"
            "<div style='font-size:1.3rem'>" +
            seg_info["label"].split(" ")[-1] + "</div>"
            "<div style='font-weight:600;font-size:1.1rem;color:" +
            seg_info["color"] + "'>" + str(count) + "</div>"
            "<div style='font-size:11px;color:#9a9485'>" +
            seg_info["label"].split(" ")[0] + "</div>"
            "<div style='font-size:10px;color:#9a9485'>" +
            seg_info["desc"] + "</div></div>",
            unsafe_allow_html=True,
        )

st.divider()

# ---- Filter -----------------------------------------------------------------
filter_seg = st.selectbox(
    t("seg.f_segment"),
    ["all"] + list(cs.RFM_SEGMENTS.keys()),
    format_func=lambda k: ("🔍 " + t("seg.all")) if k == "all"
    else cs.RFM_SEGMENTS[k]["label"],
    key="_seg_filter",
)

customers = cs.all_customers_rfm(300)
if filter_seg != "all":
    customers = [c for c in customers if c["segment"] == filter_seg]

if not customers:
    st.info(t("seg.empty"))
    st.stop()

# ---- Customer list ----------------------------------------------------------
for cust in customers:
    seg_info = cust["segment_info"]
    tags_html = "".join(
        "<span style='font-size:10px;padding:2px 6px;"
        "background:rgba(40,30,20,0.06);border-radius:10px;margin-right:3px'>"
        + tag + "</span>"
        for tag in cust["tags"]
    )
    st.markdown(
        "<div style='padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
        "<div style='display:flex;justify-content:space-between;align-items:center'>"
        "<div><strong>" + (cust["customer_key"] or "—") + "</strong>"
        + (" · " + (cust.get("phone") or "") if cust.get("phone") else "") +
        " " + tags_html + "</div>"
        "<div style='display:flex;gap:14px;font-size:13px'>"
        "<span style='color:#9a9485'>" + str(cust["frequency"]) + " " + t("common.times") + "</span>"
        "<span>฿{:,.0f}".format(cust["monetary"] or 0) + "</span>"
        "<span style='color:#9a9485;font-size:11px'>" +
        str(cust["recency_days"] or 0) + "d ago</span>"
        "<span style='font-size:11px;font-weight:600;color:" +
        seg_info["color"] + "'>" + seg_info["label"] + "</span>"
        "</div></div></div>",
        unsafe_allow_html=True,
    )

    with st.expander(t("seg.manage_title") + " — " + (cust["customer_key"] or ""), expanded=False):
        tag_c1, tag_c2 = st.columns(2)
        with tag_c1:
            add_tag = st.selectbox(
                t("seg.f_add_tag"),
                [t("seg.select_tag")] + cs.DEFAULT_TAGS,
                key="_addtag_" + (cust["customer_key"] or str(id(cust))),
            )
            if add_tag != t("seg.select_tag") and st.button(
                t("seg.add_tag_btn"),
                key="_dotag_" + (cust["customer_key"] or str(id(cust))),
                type="tertiary",
            ):
                cs.add_tag(cust["customer_key"], add_tag)
                toast(t("seg.tag_added"), icon="✓")
                st.rerun()
        with tag_c2:
            if cust["tags"]:
                rm_tag = st.selectbox(
                    t("seg.f_rm_tag"),
                    cust["tags"],
                    key="_rmtag_" + (cust["customer_key"] or str(id(cust))),
                )
                if st.button(
                    t("seg.rm_tag_btn"),
                    key="_dormtag_" + (cust["customer_key"] or str(id(cust))),
                    type="tertiary",
                ):
                    cs.remove_tag(cust["customer_key"], rm_tag)
                    st.rerun()

        notes = cs.get_notes(cust["customer_key"])
        if notes:
            for n in notes:
                st.markdown(
                    "<div style='font-size:12px;color:#7a7569;padding:2px 0'>"
                    "📝 " + n["note"][:100] +
                    " <span style='color:#9a9485'>" +
                    n["created_at"][:10] + "</span></div>",
                    unsafe_allow_html=True,
                )
        new_note = st.text_input(t("seg.f_note"),
                                  key="_note_" + (cust["customer_key"] or str(id(cust))))
        if new_note and st.button(
            t("seg.save_note_btn"),
            key="_savenote_" + (cust["customer_key"] or str(id(cust))),
            type="tertiary",
        ):
            cs.add_note(cust["customer_key"], new_note)
            toast(t("seg.note_saved"), icon="✓")
            st.rerun()
