"""G4 Fulfillment — mark orders as shipped with tracking numbers."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import fulfillment as ff
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
ff.init()
render_sidebar()

st.title(t("ful.title"))
st.caption(t("ful.caption"))

tab_pending, tab_shipped, tab_bulk = st.tabs([
    t("ful.tab_pending"), t("ful.tab_shipped"), t("ful.tab_bulk")
])

with tab_pending:
    plat_filter = st.segmented_control(t("ful.platform_filter"),
        ["all"] + list(ff.CARRIERS.keys())[:0] + ["shopee","lazada","tiktok_shop","other"],
        format_func=lambda p: t("ful.all") if p=="all" else p,
        default="all")
    orders = ff.pending_orders(platform=None if plat_filter=="all" else plat_filter)
    c1, c2 = st.columns(2)
    c1.metric(t("ful.kpi_pending"), len(orders))
    if not orders:
        st.info(t("ful.empty_pending"))
    for o in orders:
        oid_display = str(o.get("order_id") or o.get("id","?"))
        label = ("📦 **" + oid_display + "**"
                 + " · " + (o.get("platform") or "—")
                 + " · " + (o.get("customer_name") or "—")
                 + " · ฿{:,.0f}".format(o.get("total",0)))
        with st.expander(label):
            with st.form("ship_" + oid_display):
                col1, col2 = st.columns(2)
                tracking = col1.text_input(t("ful.f_tracking"), placeholder="TH12345678")
                carrier  = col2.selectbox(t("ful.f_carrier"),
                    list(ff.CARRIERS.keys()),
                    format_func=lambda c: c)
                notes    = st.text_input(t("ful.f_notes"))
                if st.form_submit_button(t("ful.ship_btn")):
                    if tracking.strip():
                        db_id = o.get("id") or o.get("order_id_db")
                        ff.mark_shipped(db_id, tracking_number=tracking.strip(),
                                        carrier=carrier, notes=notes)
                        st.success(t("ful.shipped"))
                        st.rerun()
                    else:
                        st.error(t("ful.tracking_required"))

with tab_shipped:
    shipped = ff.shipped_orders()
    if not shipped:
        st.info(t("ful.empty_shipped"))
    else:
        st.write(t("ful.shipped_count") + ": **" + str(len(shipped)) + "**")
        for o in shipped:
            oid = str(o.get("order_id") or o.get("id","?"))
            row_html = (
                "<div style='margin:3px 0;font-size:0.84rem'>"
                "<span style='color:#9a9485;width:100px;display:inline-block'>" + oid + "</span>"
                "<span style='color:#d4d0c8;width:120px;display:inline-block'>" +
                (o.get("tracking_number") or "—") + "</span>"
                "<span style='color:#9a9485;width:80px;display:inline-block'>" +
                (o.get("carrier") or "—") + "</span>"
                "<span style='color:#4d6c5c'>" +
                (o.get("shipped_at") or o.get("updated_at") or "—") + "</span>"
                "</div>"
            )
            st.html(row_html)

with tab_bulk:
    st.subheader(t("ful.bulk_title"))
    st.caption(t("ful.bulk_hint"))
    bulk_text = st.text_area(t("ful.bulk_input"),
                              height=200,
                              placeholder="order_id,tracking,carrier\n1001,TH12345,kerry\n1002,TH12346,flash")
    default_carrier = st.selectbox(t("ful.default_carrier"),
                                    list(ff.CARRIERS.keys()))
    if st.button(t("ful.bulk_btn")):
        if bulk_text.strip():
            items = []
            for line in bulk_text.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2 and parts[0] not in ("order_id","#"):
                    items.append({
                        "order_id": parts[0],
                        "tracking_number": parts[1],
                        "carrier": parts[2] if len(parts) > 2 else default_carrier
                    })
            if items:
                ff.mark_shipped_bulk(items)
                st.success(t("ful.bulk_done") + ": " + str(len(items)))
                st.rerun()
