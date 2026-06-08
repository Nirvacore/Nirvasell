"""Pick & Pack — warehouse operations in one page.

Generate pick lists (grab from shelves) and pack slips (what goes in
each box). Download as text for printing."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import pick_pack as pp
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Pick & Pack",
                   page_icon="📋", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="📋", title=t("pp.title"), subtitle=t("pp.caption"))


# ---- Tabs: Pick List vs Pack Slips -------------------------------------------

tab_pick, tab_pack = st.tabs([
    "📦 " + t("pp.tab_pick"),
    "📋 " + t("pp.tab_pack"),
])

with tab_pick:
    st.markdown("### " + t("pp.pick_title"))
    st.caption(t("pp.pick_help"))

    pick_list = pp.generate_pick_list()

    if not pick_list:
        st.info(t("pp.no_pending"))
    else:
        total_items = sum(i["total_qty"] for i in pick_list)
        k1, k2 = st.columns(2)
        with k1:
            metric_with_hint(
                t("pp.kpi_skus"), str(len(pick_list)),
                hint="", hint_tone="info",
            )
        with k2:
            metric_with_hint(
                t("pp.kpi_items"), str(total_items),
                hint="", hint_tone="info",
            )

        for i, item in enumerate(pick_list, 1):
            order_ids = ", ".join(item["order_ids"][:3])
            if len(item["order_ids"]) > 3:
                order_ids = order_ids + " +" + str(len(item["order_ids"]) - 3)

            st.markdown(
                "<div style='display:flex;justify-content:space-between;align-items:center;"
                "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div style='display:flex;gap:12px;align-items:center'>"
                "<span style='background:rgba(40,30,20,0.06);padding:4px 10px;"
                "border-radius:6px;font-size:13px;font-weight:600;min-width:30px;"
                "text-align:center'>" + str(i) + "</span>"
                "<div><strong>" + item["sku"] + "</strong>"
                " <span style='color:#7a7569;font-size:12px'>" +
                item["name"][:30] + "</span></div></div>"
                "<div style='display:flex;gap:14px;align-items:center'>"
                "<span style='font-size:1.2rem;font-weight:600;color:#4d6c5c'>"
                "×" + str(item["total_qty"]) + "</span>"
                "<span style='color:#9a9485;font-size:11px'>" +
                str(item["order_count"]) + " orders</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )

        # Download pick list
        st.divider()
        pick_text = pp.pick_list_text()
        st.download_button(
            t("pp.download_pick"),
            data=pick_text.encode("utf-8"),
            file_name="pick_list.txt",
            mime="text/plain",
        )

with tab_pack:
    st.markdown("### " + t("pp.pack_title"))
    st.caption(t("pp.pack_help"))

    slips = pp.generate_pack_slips()

    if not slips:
        st.info(t("pp.no_pending"))
    else:
        metric_with_hint(
            t("pp.kpi_orders"), str(len(slips)),
            hint="", hint_tone="info",
        )

        for slip in slips:
            plat = slip.get("platform", "")
            plat_icon = {"shopee": "🛒", "lazada": "🟧", "tiktok": "🎵"}.get(plat, "📦")
            total_str = "{:,.0f}".format(slip["total"])
            items_count = sum(i["qty"] for i in slip["items"])

            with st.expander(
                plat_icon + " " + slip["order_id"] +
                " · " + (slip["buyer_name"] or "—") +
                " · " + str(items_count) + " items · ฿" + total_str,
                expanded=False,
            ):
                if slip["buyer_name"]:
                    st.markdown(
                        "**" + t("pp.buyer") + ":** " + slip["buyer_name"] +
                        (" · 📱 " + slip["buyer_phone"] if slip["buyer_phone"] else "")
                    )

                for item in slip["items"]:
                    st.markdown(
                        "<div style='display:flex;justify-content:space-between;"
                        "padding:6px 0;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                        "<div>☐ " + item["sku"] + " — " + item["name"][:25] + "</div>"
                        "<div>×" + str(item["qty"]) +
                        " · ฿" + "{:,.0f}".format(item["subtotal"]) + "</div>"
                        "</div>",
                        unsafe_allow_html=True,
                    )

                # Per-slip download
                slip_text = pp.pack_slip_text(slip["order_id"])
                st.download_button(
                    "📥 " + t("pp.download_slip"),
                    data=slip_text.encode("utf-8"),
                    file_name="pack_" + slip["order_id"] + ".txt",
                    mime="text/plain",
                    key="_dl_slip_" + slip["order_id"],
                )

        # Download all pack slips
        st.divider()
        all_text = pp.all_pack_slips_text()
        st.download_button(
            t("pp.download_all"),
            data=all_text.encode("utf-8"),
            file_name="all_pack_slips.txt",
            mime="text/plain",
        )
