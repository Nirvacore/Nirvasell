"""Fulfillment — pending orders, bulk-assign tracking, generate shipping
labels + per-platform tracking-update CSVs."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

import db
import fulfillment as ff
import user_settings as us
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import empty_state, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Fulfillment", page_icon="📦", layout="wide")
apply_theme()
require_auth()
db.init()
ff.init()
us.init()
render_sidebar()

page_header(icon="📦", title=t("fulfill.title"), subtitle=t("fulfill.caption"))


# ---- Stats overview -----------------------------------------------------

stats = ff.stats()
c1, c2, c3 = st.columns(3)
c1.metric(t("fulfill.stat_pending"), stats["pending"])
c2.metric(t("fulfill.stat_shipped"), stats["shipped"])
if stats["pending_by_platform"]:
    mix = " · ".join(f"{p}: {n}" for p, n in stats["pending_by_platform"].items())
    c3.caption(f"{t('fulfill.by_platform')}: {mix}")


# ---- Tab: pending vs history -------------------------------------------

tab_pending, tab_history = st.tabs([
    f"⏳ {t('fulfill.tab_pending')} ({stats['pending']})",
    f"✅ {t('fulfill.tab_history')} ({stats['shipped']})",
])


# ---- Pending tab --------------------------------------------------------

with tab_pending:
    pending = ff.pending_orders()

    if not pending:
        empty_state(
            icon="🎉",
            title=t("fulfill.no_pending"),
            body=t("fulfill.empty_body"),
            cta_label=t("fulfill.empty_cta"),
            cta_target="pages/5_🔌_Import.py",
        )
    else:
        # Platform filter
        platforms = ff.platforms_with_pending()
        plat_filter = st.selectbox(
            t("fulfill.platform_filter"),
            ["all"] + platforms,
            format_func=lambda p: t("fulfill.all_platforms") if p == "all" else p.title(),
        )
        if plat_filter != "all":
            pending = [o for o in pending if o["platform"] == plat_filter]

        st.caption(t("fulfill.bulk_help"))

        # Default carrier (saved per user)
        default_carrier = us.get("fulfill.default_carrier", "kerry") or "kerry"

        # ---- Bulk assign form -----------------------------------------
        with st.form("bulk_assign"):
            cF1, cF2 = st.columns([1, 3])
            with cF1:
                carrier_key = st.selectbox(
                    t("fulfill.carrier"),
                    [k for k, _ in ff.carrier_options()],
                    index=[k for k, _ in ff.carrier_options()].index(default_carrier)
                          if default_carrier in dict(ff.carrier_options()) else 0,
                    format_func=lambda k: dict(ff.carrier_options())[k],
                )
            with cF2:
                st.caption(t("fulfill.assign_hint"))

            # Build editable dataframe — user pastes tracking numbers
            df_rows = []
            for o in pending:
                df_rows.append({
                    "✓": False,
                    "platform": o.get("platform") or "",
                    "order_id": o.get("order_id") or "",
                    "sku": o.get("sku") or "",
                    "qty": o.get("qty") or 1,
                    "product": (o.get("product_name") or "")[:50],
                    "tracking_number": "",
                    "_db_id": o["id"],
                })
            df = pd.DataFrame(df_rows)

            edited = st.data_editor(
                df,
                key="pending_edit",
                width='stretch',
                hide_index=True,
                column_config={
                    "✓": st.column_config.CheckboxColumn(t("fulfill.col_pick"), width="small"),
                    "platform": st.column_config.TextColumn(disabled=True, width="small"),
                    "order_id": st.column_config.TextColumn(disabled=True),
                    "sku": st.column_config.TextColumn(disabled=True, width="small"),
                    "qty": st.column_config.NumberColumn(disabled=True, width="small"),
                    "product": st.column_config.TextColumn(disabled=True),
                    "tracking_number": st.column_config.TextColumn(
                        t("fulfill.col_tracking"), help=t("fulfill.col_tracking_help"),
                    ),
                    "_db_id": None,  # hidden
                },
            )

            submitted = st.form_submit_button(
                t("fulfill.mark_shipped"), type="primary",
            )
            if submitted:
                # Remember carrier for next time
                us.set("fulfill.default_carrier", carrier_key)
                # Build update list — only rows that are picked AND have tracking
                items = []
                for _, r in edited.iterrows():
                    if r["✓"] and str(r["tracking_number"]).strip():
                        items.append({
                            "id": int(r["_db_id"]),
                            "tracking_number": str(r["tracking_number"]).strip(),
                            "carrier": carrier_key,
                        })
                if not items:
                    st.warning(t("fulfill.nothing_picked"))
                else:
                    n = ff.mark_shipped_bulk(items)
                    st.success(t("fulfill.shipped_n", n=n))
                    st.rerun()


# ---- History tab --------------------------------------------------------

with tab_history:
    shipped = ff.shipped_orders(limit=200)
    if not shipped:
        st.caption(t("fulfill.no_history"))
    else:
        # Group by platform for downloadable CSVs
        st.markdown(f"### {t('fulfill.download_csvs')}")
        st.caption(t("fulfill.csv_hint"))

        by_platform: dict[str, list[dict]] = {}
        for o in shipped:
            by_platform.setdefault(o.get("platform") or "other", []).append(o)

        cols = st.columns(max(1, min(4, len(by_platform))))
        for i, (plat, rows) in enumerate(by_platform.items()):
            with cols[i % len(cols)]:
                st.metric(plat.title(), f"{len(rows)} orders")
                csv_bytes = ff.shipment_csv_for(plat, rows)
                st.download_button(
                    f"⬇ {plat}_shipments.csv",
                    data=csv_bytes,
                    file_name=f"nirva_shipments_{plat}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key=f"dl_{plat}",
                    width='stretch',
                )

        # Print labels
        st.divider()
        st.markdown(f"### {t('fulfill.print_labels')}")
        st.caption(t("fulfill.print_hint"))

        seller_name = us.get("fulfill.seller_name", "")
        seller_addr = us.get("fulfill.seller_address", "")
        with st.expander(t("fulfill.seller_info")):
            with st.form("seller_info"):
                seller_name = st.text_input(t("fulfill.seller_name"), value=seller_name or "")
                seller_addr = st.text_area(t("fulfill.seller_address"), value=seller_addr or "", height=80)
                if st.form_submit_button(t("common.save")):
                    us.set("fulfill.seller_name", seller_name)
                    us.set("fulfill.seller_address", seller_addr)
                    st.rerun()

        # Pick how many recent to print
        n_to_print = st.slider(t("fulfill.recent_n"), 1, min(50, len(shipped)),
                               min(10, len(shipped)))
        labels_html = ff.label_html(
            shipped[:n_to_print],
            seller_name=seller_name, seller_address=seller_addr,
        )
        st.download_button(
            f"🖨 {t('fulfill.download_labels')}",
            data=labels_html.encode("utf-8"),
            file_name=f"nirva_labels_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            type="primary",
        )
        with st.expander(t("fulfill.preview_labels")):
            st.components.v1.html(labels_html, height=600, scrolling=True)

        # Full history table
        st.divider()
        st.markdown(f"### {t('fulfill.recent_shipped')}")
        df_hist = pd.DataFrame(shipped)
        show_cols = [c for c in
                     ["shipped_at", "platform", "order_id", "sku", "qty",
                      "carrier", "tracking_number", "product_name"]
                     if c in df_hist.columns]
        st.dataframe(df_hist[show_cols], hide_index=True, width='stretch')
