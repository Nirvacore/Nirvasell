"""H3 Data Export — download a full backup of your store data as CSV ZIP."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import data_export as de
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
user = require_auth()
render_sidebar()

st.title(t("exp.title"))
st.caption(t("exp.caption"))

size_bytes = de.export_size_estimate(user["id"] if isinstance(user, dict) else 1)
size_kb    = round(size_bytes / 1024, 1)

st.info("💾 " + t("exp.size_estimate") + ": **" + str(size_kb) + " KB**")

st.divider()
st.subheader(t("exp.what_included"))
tables_html = ""
tables = [
    ("📦", t("exp.t_products")),
    ("🛍", t("exp.t_orders")),
    ("👥", t("exp.t_customers")),
    ("💰", t("exp.t_expenses")),
    ("🏭", t("exp.t_suppliers")),
    ("🚀", t("exp.t_fulfillment")),
    ("🏷", t("exp.t_inventory")),
    ("📊", t("exp.t_campaigns")),
]
for icon, label in tables:
    tables_html += "<div style='margin:2px 0;font-size:0.85rem'>" + icon + " " + label + "</div>"
st.html(tables_html)

st.divider()
st.subheader(t("exp.download_title"))
st.warning(t("exp.warning"))

if st.button("📤 " + t("exp.download_btn"), type="primary"):
    with st.spinner(t("exp.exporting")):
        try:
            zip_bytes = de.export_user(user["id"] if isinstance(user, dict) else 1)
            st.download_button(
                label    = "💾 " + t("exp.save_file"),
                data     = zip_bytes,
                file_name= "nirva_export.zip",
                mime     = "application/zip"
            )
            st.success(t("exp.ready"))
        except Exception as e:
            st.error(t("exp.error") + ": " + str(e))
