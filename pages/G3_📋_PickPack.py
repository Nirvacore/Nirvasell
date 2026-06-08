"""G3 Pick & Pack — generate pick lists and pack slips for pending orders."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pick_pack as pp
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("pp.title"))
st.caption(t("pp.caption"))

pending = pp.pending_orders()
st.metric(t("pp.kpi_pending"), len(pending))

if not pending:
    st.info(t("pp.empty"))
else:
    st.divider()
    tab_pick, tab_pack = st.tabs([t("pp.tab_pick"), t("pp.tab_pack")])

    with tab_pick:
        st.subheader(t("pp.pick_list_title"))
        pick_list = pp.generate_pick_list()
        col1, col2 = st.columns([3,1])
        col1.write(t("pp.total_items") + ": **" + str(len(pick_list)) + "**")
        if col2.button(t("pp.copy_pick")):
            st.session_state["pick_text"] = pp.pick_list_text()

        if "pick_text" in st.session_state:
            st.code(st.session_state["pick_text"], language=None)

        if not pick_list:
            st.info(t("pp.empty_pick"))
        else:
            for item in pick_list:
                row_html = (
                    "<div style='display:flex;align-items:center;gap:8px;margin:3px 0;"
                    "font-size:0.85rem'>"
                    "<div style='width:24px;height:24px;border:2px solid #4d6c5c;"
                    "flex-shrink:0'></div>"
                    "<span style='color:#d4d0c8;width:80px;font-family:monospace'>" +
                    (item.get("sku") or "—") + "</span>"
                    "<span style='color:#9a9485;flex:1'>" +
                    (item.get("name") or item.get("sku") or "?") + "</span>"
                    "<span style='color:#d4d0c8;font-variant-numeric:tabular-nums'>" +
                    str(item.get("total_qty") or item.get("qty", 0)) + " " + t("pp.pcs") +
                    "</span></div>"
                )
                st.html(row_html)

    with tab_pack:
        st.subheader(t("pp.pack_slips_title"))
        pack_slips = pp.generate_pack_slips()
        col1, col2 = st.columns([3,1])
        col1.write(t("pp.total_orders") + ": **" + str(len(pack_slips)) + "**")
        if col2.button(t("pp.copy_all")):
            st.session_state["pack_all_text"] = pp.all_pack_slips_text()

        if "pack_all_text" in st.session_state:
            st.code(st.session_state["pack_all_text"], language=None)

        if not pack_slips:
            st.info(t("pp.empty_pack"))
        for slip in pack_slips:
            oid = slip.get("order_id") or slip.get("id") or "?"
            label = "📦 **" + str(oid) + "**"
            cust  = slip.get("customer_name") or slip.get("customer") or "—"
            label += " · " + cust
            with st.expander(label):
                items = slip.get("items") or []
                for it in items:
                    st.write("• " + (it.get("sku","") or "") + " — " +
                             (it.get("name") or it.get("sku","")) +
                             " × " + str(it.get("qty",1)))
                col_s, _ = st.columns([1,3])
                if col_s.button(t("pp.copy_slip"), key="cps_" + str(oid)):
                    st.session_state["slip_" + str(oid)] = pp.pack_slip_text(oid)
                key_slip = "slip_" + str(oid)
                if key_slip in st.session_state:
                    st.code(st.session_state[key_slip], language=None)
