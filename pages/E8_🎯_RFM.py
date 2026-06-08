"""E8 RFM Segmentation — rank customers by Recency × Frequency × Monetary."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import rfm as rfm_mod
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("rfm.title"))
st.caption(t("rfm.caption"))

tab_overview, tab_segment, tab_all = st.tabs([
    t("rfm.tab_overview"), t("rfm.tab_segment"), t("rfm.tab_all")
])

with tab_overview:
    st.subheader(t("rfm.overview_title"))
    summary = rfm_mod.segment_summary()
    if not summary:
        st.info(t("rfm.empty"))
        st.write(t("rfm.empty_hint"))
    else:
        total_custs = sum(s["count"] for s in summary)
        for seg in summary:
            si = rfm_mod.SEGMENTS.get(seg["segment"], {})
            icon  = si.get("icon","")
            label = si.get("label", seg["segment"])
            color = si.get("color","#9a9485")
            action = si.get("action","")
            pct   = round(seg["count"] / total_custs * 100, 1) if total_custs else 0
            bar_w = int(pct * 3)

            seg_html = (
                "<div style='margin:4px 0'>"
                "<span style='width:180px;display:inline-block;font-size:0.85rem;color:" +
                color + "'>" + icon + " " + label + "</span>"
                "<div style='display:inline-block;background:" + color +
                ";width:" + str(bar_w) + "px;height:12px;vertical-align:middle;opacity:0.6'></div>"
                " <span style='font-size:0.83rem;color:#9a9485'>" +
                str(seg["count"]) + t("rfm.custs_unit") + " (" + str(pct) + "%)"
                " · ฿{:,.0f}".format(seg["avg_spent"]) + " avg · " + action + "</span>"
                "</div>"
            )
            st.html(seg_html)

        st.divider()
        priority_action_html = (
            "<div style='font-size:0.83rem;color:#9a9485'>"
            "<b style='color:#c54c4c'>at_risk</b> → win-back campaign<br>"
            "<b style='color:#d4832f'>about_to_sleep</b> → activation offer<br>"
            "<b style='color:#4d6c5c'>champions</b> → VIP rewards, referral ask<br>"
            "<b style='color:#3a7ca5'>loyal</b> → upsell bundles<br>"
            "</div>"
        )
        st.html(priority_action_html)

with tab_segment:
    st.subheader(t("rfm.segment_title"))
    segments_list = list(rfm_mod.SEGMENTS.keys())
    sel_seg = st.selectbox(
        t("rfm.sel_segment"),
        segments_list,
        format_func=lambda s: rfm_mod.SEGMENTS[s]["icon"] + " " +
                               rfm_mod.SEGMENTS[s]["label"],
    )
    custs_in_seg = rfm_mod.customers_in_segment(sel_seg)
    si = rfm_mod.SEGMENTS[sel_seg]
    st.write(si["icon"] + " **" + si["label"] + "** — " +
             t("rfm.action") + ": *" + si["action"] + "*")
    if not custs_in_seg:
        st.info(t("rfm.seg_empty"))
    else:
        st.write(str(len(custs_in_seg)) + t("rfm.custs_unit"))
        table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.83rem'>"
        table_html += "<tr style='color:#9a9485'>"
        for col in [t("rfm.col_name"), t("rfm.col_phone"), t("rfm.col_orders"),
                    t("rfm.col_spent"), t("rfm.col_last"), "R/F/M"]:
            table_html += "<th style='text-align:left;padding:4px 8px'>" + col + "</th>"
        table_html += "</tr>"
        for c in custs_in_seg[:50]:
            table_html += "<tr style='border-top:1px solid #2a2a2a'>"
            table_html += "<td style='padding:4px 8px'>" + (c["name"] or "—") + "</td>"
            table_html += "<td style='padding:4px 8px;color:#9a9485'>" + (c["phone"] or "—") + "</td>"
            table_html += "<td style='padding:4px 8px'>" + str(c.get("order_count",0)) + "</td>"
            table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(c.get("total_spent",0)) + "</td>"
            table_html += "<td style='padding:4px 8px;color:#9a9485'>" + (c.get("last_order","")[:10] or "—") + "</td>"
            rfm_str = str(c.get("r_score",0)) + "/" + str(c.get("f_score",0)) + "/" + str(c.get("m_score",0))
            table_html += "<td style='padding:4px 8px;color:#9a9485'>" + rfm_str + "</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.html(table_html)

with tab_all:
    st.subheader(t("rfm.all_title"))
    with st.spinner(t("rfm.calculating")):
        all_rfm = rfm_mod.calculate_rfm()
    if not all_rfm:
        st.info(t("rfm.empty"))
    else:
        seg_filter = st.selectbox(
            t("rfm.seg_filter"),
            ["all"] + list(rfm_mod.SEGMENTS.keys()),
            format_func=lambda s: t("rfm.all_segs") if s=="all" else
                                   rfm_mod.SEGMENTS[s]["icon"] + " " + rfm_mod.SEGMENTS[s]["label"],
        )
        rows = all_rfm if seg_filter == "all" else \
               [r for r in all_rfm if r.get("segment") == seg_filter]
        st.write(str(len(rows)) + t("rfm.custs_unit"))
        for c in rows[:60]:
            seg_key = c.get("segment","")
            seg_info = rfm_mod.SEGMENTS.get(seg_key, {})
            icon  = seg_info.get("icon","")
            color = seg_info.get("color","#9a9485")
            rfm_str = str(c.get("r_score",0)) + "/" + str(c.get("f_score",0)) + "/" + str(c.get("m_score",0))
            row_html = (
                "<div style='margin:2px 0;font-size:0.83rem'>"
                "<span style='width:160px;display:inline-block'>" +
                (c["name"] or "—") + "</span>"
                "<span style='color:" + color + ";width:140px;display:inline-block'>" +
                icon + " " + seg_info.get("label","") + "</span>"
                "<span style='color:#9a9485'>R/F/M " + rfm_str +
                " · ฿{:,.0f}".format(c.get("total_spent",0)) +
                " · " + (c.get("last_order","")[:10] or "—") + "</span>"
                "</div>"
            )
            st.html(row_html)
