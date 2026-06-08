"""Export Center — download your data as CSV for Excel/accounting.

Products, orders, customers, expenses, inventory snapshot — all exportable."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime
import db
import export_center as ec
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Export",
                   page_icon="📤", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="📤", title=t("exp.title"), subtitle=t("exp.caption"))

s = ec.stats()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(t("exp.kpi_products"), str(s["products"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint(t("exp.kpi_orders"), str(s["orders"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint(t("exp.kpi_expenses"), str(s["expenses"]),
                     hint="", hint_tone="info")
with k4:
    metric_with_hint("📁 " + t("exp.kpi_types"), str(s["export_types"]),
                     hint="", hint_tone="ok")

st.divider()

EXPORTS = [
    {
        "key": "products", "icon": "📦", "title": t("exp.type_products"),
        "desc": t("exp.desc_products"), "fn": ec.export_products,
        "filename": "nirva_products.csv",
    },
    {
        "key": "orders", "icon": "🧾", "title": t("exp.type_orders"),
        "desc": t("exp.desc_orders"), "fn": lambda: ec.export_orders(90),
        "filename": "nirva_orders_90d.csv",
    },
    {
        "key": "customers", "icon": "👥", "title": t("exp.type_customers"),
        "desc": t("exp.desc_customers"), "fn": lambda: ec.export_customers(180),
        "filename": "nirva_customers.csv",
    },
    {
        "key": "expenses", "icon": "💸", "title": t("exp.type_expenses"),
        "desc": t("exp.desc_expenses"), "fn": lambda: ec.export_expenses(3),
        "filename": "nirva_expenses_3m.csv",
    },
    {
        "key": "inventory", "icon": "📊", "title": t("exp.type_inventory"),
        "desc": t("exp.desc_inventory"), "fn": ec.export_inventory_snapshot,
        "filename": "nirva_inventory_snapshot.csv",
    },
]

for ex in EXPORTS:
    ec1, ec2 = st.columns([4, 1])
    with ec1:
        st.markdown(
            "<div style='padding:12px 16px;background:white;"
            "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px;"
            "margin-bottom:6px'>"
            "<div style='font-size:1.05rem;font-weight:600'>"
            + ex["icon"] + " " + ex["title"] + "</div>"
            "<div style='font-size:12px;color:#7a7569;margin-top:2px'>"
            + ex["desc"] + "</div></div>",
            unsafe_allow_html=True,
        )
    with ec2:
        try:
            csv_data = ex["fn"]()
            ts = datetime.now().strftime("%Y%m%d")
            fname = ex["filename"].replace(".csv", "_" + ts + ".csv")
            st.download_button(
                t("exp.download_btn"),
                data=csv_data,
                file_name=fname,
                mime="text/csv",
                key="_exp_" + ex["key"],
                type="primary",
            )
        except Exception:
            st.button(t("exp.no_data"), key="_exp_" + ex["key"],
                      disabled=True, type="tertiary")

st.divider()
st.caption(t("exp.csv_hint"))
