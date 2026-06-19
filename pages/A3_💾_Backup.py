"""Backup & Restore — protect your data.

Download a full backup of your shop database. Restore from a backup file."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime
import db
import backup_mgr as bk
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Backup",
                   page_icon="💾", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="💾", title=t("bkup.title"), subtitle=t("bkup.caption"))

info = bk.backup_info()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("📦 " + t("bkup.kpi_products"), str(info["products"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("🧾 " + t("bkup.kpi_orders"), str(info["orders"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("📊 " + t("bkup.kpi_tables"), str(info["tables"]),
                     hint="", hint_tone="info")
with k4:
    size_str = "{:,.0f}".format(info["size_kb"]) + " KB"
    metric_with_hint("💿 " + t("bkup.kpi_size"), size_str,
                     hint="", hint_tone="info")


# ---- Download backup --------------------------------------------------------

st.divider()
st.markdown("### 📥 " + t("bkup.download_title"))
st.caption(t("bkup.download_help"))

ts = datetime.now().strftime("%Y%m%d_%H%M")
backup_data = bk.create_backup()
st.download_button(
    t("bkup.download_btn"),
    data=backup_data,
    file_name="nirva_backup_" + ts + ".zip",
    mime="application/zip",
    type="primary",
    key="_bk_dl",
)

st.success(t("bkup.download_ready", fmt={
    "products": str(info["products"]),
    "orders": str(info["orders"]),
}))


# ---- Restore backup ---------------------------------------------------------

st.divider()
st.markdown("### 📤 " + t("bkup.restore_title"))
st.caption(t("bkup.restore_help"))

uploaded = st.file_uploader(
    t("bkup.upload_label"),
    type=["zip"],
    key="_bk_upload",
)

if uploaded:
    data = uploaded.read()
    validation = bk.validate_backup(data)

    if not validation["valid"]:
        st.error("❌ " + validation["error"])
    else:
        st.info(t("bkup.valid_backup", fmt={
            "tables": str(len(validation["tables"])),
            "size": str(validation["size_kb"]),
        }))

        if validation.get("meta"):
            m = validation["meta"]
            st.caption(t("bkup.meta_caption",
                         date=m.get("created_at", "—"),
                         products=str(m.get("products", "?")),
                         orders=str(m.get("orders", "?"))))

        st.warning(t("bkup.restore_warning"))

        if st.button(t("bkup.restore_btn"), type="primary", key="_bk_restore"):
            result = bk.restore_backup(data)
            if result.get("restored"):
                toast(t("bkup.restored"), icon="✅")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ " + result.get("error", "Unknown error"))
