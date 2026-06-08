"""Batch Operations — update stock/price for 50+ SKUs at once.

Thai resellers get stock updates from distributors and need to update
everything in one go, not clicking product by product."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import batch_ops as bo
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Batch Ops",
                   page_icon="⚡", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="⚡", title=t("batch.title"), subtitle=t("batch.caption"))


# ---- Tab layout ------------------------------------------------------------

tab_csv, tab_price, tab_stock = st.tabs([
    "📄 " + t("batch.tab_csv"),
    "💰 " + t("batch.tab_price"),
    "📦 " + t("batch.tab_stock"),
])


# ---- CSV Batch Update -------------------------------------------------------

with tab_csv:
    st.markdown("### " + t("batch.csv_title"))
    st.caption(t("batch.csv_help"))

    # Template download
    template = "sku,stock,cost_price,sell_price\nSKU-001,50,350,599\nSKU-002,100,200,399\n"
    st.download_button(
        t("batch.download_template"),
        data=template.encode("utf-8-sig"),
        file_name="batch_update_template.csv",
        mime="text/csv",
    )

    up = st.file_uploader(
        t("batch.upload_csv"),
        type=["csv"],
        accept_multiple_files=False,
        key="_batch_csv_upload",
    )

    if up:
        try:
            rows = bo.parse_batch_csv(up.getvalue(), up.name)
        except Exception as e:
            st.error(str(e))
            rows = []

        if rows:
            st.success(t("batch.parsed", n=len(rows)))

            import pandas as pd
            preview = pd.DataFrame(rows)
            st.dataframe(preview, hide_index=True, width="stretch")

            cols_found = set()
            for r in rows:
                cols_found.update(k for k in r if k != "sku")

            st.caption(
                t("batch.will_update") + ": " + ", ".join(sorted(cols_found))
            )

            if st.button(t("batch.apply_btn"), type="primary"):
                result = bo.apply_batch_update(rows)
                if result["updated"]:
                    toast(
                        t("batch.updated", n=result["updated"]),
                        icon="✓",
                    )
                if result["not_found"]:
                    st.warning(
                        t("batch.not_found", n=len(result["not_found"]))
                        + ": " + ", ".join(result["not_found"][:10])
                    )
                if result["skipped"]:
                    st.info(t("batch.skipped", n=result["skipped"]))
                st.rerun()
        elif up:
            st.warning(t("batch.no_valid_rows"))


# ---- Bulk Price Adjust -------------------------------------------------------

with tab_price:
    st.markdown("### " + t("batch.price_title"))
    st.caption(t("batch.price_help"))

    c1, c2 = st.columns([1, 2])
    with c1:
        pct = st.number_input(
            t("batch.adjust_pct"),
            min_value=-50.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
            format="%.1f",
        )
    with c2:
        scope = st.radio(
            t("batch.scope"),
            ["all", "selected"],
            format_func=lambda s: t("batch.scope_" + s),
            horizontal=True,
        )

    selected_skus = []
    if scope == "selected":
        with db.conn() as c:
            all_skus = [r["sku"] for r in c.execute(
                "SELECT sku FROM products WHERE sku IS NOT NULL ORDER BY sku"
            ).fetchall()]
        selected_skus = st.multiselect(
            t("batch.pick_skus"),
            all_skus,
        )

    if pct != 0:
        direction = t("batch.raise") if pct > 0 else t("batch.lower")
        abs_pct = abs(pct)
        target = "all" if scope == "all" else str(len(selected_skus)) + " SKUs"
        st.info(direction + " " + "{:.1f}%".format(abs_pct) + " — " + target)

        if st.button(t("batch.apply_price"), type="primary"):
            skus = selected_skus if scope == "selected" else None
            n = bo.bulk_price_adjust(pct, skus)
            toast(t("batch.price_done", n=n), icon="💰")
            st.rerun()


# ---- Bulk Stock Set ----------------------------------------------------------

with tab_stock:
    st.markdown("### " + t("batch.stock_title"))
    st.caption(t("batch.stock_help"))

    c1, c2 = st.columns([1, 2])
    with c1:
        stock_val = st.number_input(
            t("batch.stock_value"),
            min_value=0,
            value=0,
            step=1,
        )
    with c2:
        stock_scope = st.radio(
            t("batch.scope"),
            ["all", "selected"],
            format_func=lambda s: t("batch.scope_" + s),
            horizontal=True,
            key="_stock_scope",
        )

    stock_skus = []
    if stock_scope == "selected":
        with db.conn() as c:
            all_skus = [r["sku"] for r in c.execute(
                "SELECT sku FROM products WHERE sku IS NOT NULL ORDER BY sku"
            ).fetchall()]
        stock_skus = st.multiselect(
            t("batch.pick_skus"),
            all_skus,
            key="_stock_skus",
        )

    target_stock = "all" if stock_scope == "all" else str(len(stock_skus)) + " SKUs"
    st.info(t("batch.stock_set_to") + " " + str(stock_val) + " — " + target_stock)

    if st.button(t("batch.apply_stock"), type="primary"):
        skus = stock_skus if stock_scope == "selected" else None
        n = bo.bulk_stock_set(stock_val, skus)
        toast(t("batch.stock_done", n=n), icon="📦")
        st.rerun()
