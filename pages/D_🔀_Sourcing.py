"""Sourcing — when the same product is available from multiple suppliers,
this page picks the best one (cheapest / most stock / weighted)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import sourcing
import fees as fees_mod
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import empty_state
from i18n import t

db.init()
st.set_page_config(page_title="nirva.sell · Sourcing", page_icon="🔀", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="🔀", title=t("sourcing.title"), subtitle=t("sourcing.caption"))


# ---- Auto-group button ---------------------------------------------------

c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(t("sourcing.intro"))
with c2:
    if st.button(t("sourcing.run_match"), type="primary", width='stretch'):
        stats = sourcing.auto_group_all()
        st.success(
            t("sourcing.match_done",
              linked=stats["linked"],
              ungrp=stats["ungroupable"],
              groups=stats["total_groups"])
        )

# Stats
with db.conn() as c:
    n_groups = c.execute("SELECT COUNT(*) FROM product_groups").fetchone()[0]
    n_grouped = c.execute("SELECT COUNT(*) FROM products WHERE group_id IS NOT NULL").fetchone()[0]
    n_ungrouped = c.execute("SELECT COUNT(*) FROM products WHERE group_id IS NULL").fetchone()[0]
    n_multi = c.execute(
        "SELECT COUNT(*) FROM (SELECT group_id, COUNT(*) AS n FROM products "
        "WHERE group_id IS NOT NULL GROUP BY group_id HAVING n > 1)"
    ).fetchone()[0]

m1, m2, m3, m4 = st.columns(4)
m1.metric(t("sourcing.stat_groups"), n_groups)
m2.metric(t("sourcing.stat_grouped"), n_grouped)
m3.metric(t("sourcing.stat_multi"), n_multi)
m4.metric(t("sourcing.stat_ungrouped"), n_ungrouped)

if n_groups == 0:
    empty_state(
        icon="🔀",
        title=t("sourcing.empty_title"),
        body=t("sourcing.empty_body"),
        cta_label=t("sourcing.empty_cta"),
        cta_target="pages/2_📦_Catalog.py",
    )
    st.stop()


# ---- Multi-supplier groups (the interesting ones) ------------------------

st.divider()
st.subheader(t("sourcing.multi_title"))

multi_df = sourcing.list_groups(min_offers=2)

if multi_df.empty:
    st.info(t("sourcing.no_multi"))
else:
    # Rank by savings (most $ savings = top of the list)
    multi_df = multi_df.sort_values("savings", ascending=False).reset_index(drop=True)

    # Sourcing criterion picker
    cc1, cc2, cc3 = st.columns([2, 1, 1])
    with cc1:
        criterion = st.radio(
            t("sourcing.criterion"),
            ["price", "stock", "weighted"],
            format_func=lambda c: {
                "price":    "💰 " + t("sourcing.crit_price"),
                "stock":    "📦 " + t("sourcing.crit_stock"),
                "weighted": "⚖️ " + t("sourcing.crit_weighted"),
            }[c],
            horizontal=True,
        )
    with cc2:
        in_stock_only = st.checkbox(t("sourcing.in_stock_only"), value=False)

    st.markdown("")

    for _, g in multi_df.head(30).iterrows():
        savings = g["savings"]
        pct = g["savings_pct"]
        with st.expander(
            f"**{g['canonical_name']}** · "
            f"{int(g['offer_count'])} {t('sourcing.suppliers_word')} · "
            f"{t('sourcing.save_n', savings=int(savings), pct=pct)}",
            expanded=False,
        ):
            offers = sourcing.offers_for_group(int(g["id"]))
            if offers.empty:
                continue

            winner = sourcing.best_offer(int(g["id"]), criterion=criterion, in_stock_only=in_stock_only)

            # Show offers side-by-side
            cols = st.columns(min(len(offers), 4))
            for i, (_, row) in enumerate(offers.iterrows()):
                if i >= len(cols):
                    break
                is_winner = winner and row["id"] == winner["id"]
                with cols[i]:
                    border = "2px solid #4d6c5c" if is_winner else "1px solid rgba(40,30,20,0.10)"
                    bg = "rgba(77,108,92,0.06)" if is_winner else "transparent"
                    badge = "🏆 " + t("sourcing.winner") if is_winner else ""
                    st.markdown(
                        f"<div style='border:{border};background:{bg};border-radius:10px;"
                        f"padding:14px;min-height:130px'>"
                        f"<div style='color:#6b6b6b;font-size:11px;text-transform:uppercase;"
                        f"letter-spacing:0.05em'>{row['supplier']}</div>"
                        f"<div style='font-size:12px;color:#3d3d3d;margin:2px 0 6px;"
                        f"word-break:break-word'>{row['sku']}</div>"
                        f"<div style='font-family:Cormorant Garamond,serif;font-size:1.5rem;"
                        f"font-weight:500;color:#1f1f1f'>"
                        f"฿{int(row['cost_price'] or 0):,}</div>"
                        f"<div style='color:#6b6b6b;font-size:12px;margin-top:4px'>"
                        f"stock: {row.get('stock') or '—'}</div>"
                        f"<div style='color:#4d6c5c;font-size:13px;font-weight:600;"
                        f"margin-top:6px'>{badge}</div>"
                        "</div>",
                        unsafe_allow_html=True,
                    )

            if winner:
                st.caption(
                    t("sourcing.action_buy",
                      supplier=winner.get("supplier", "?"),
                      sku=winner["sku"],
                      price=int(winner["cost_price"] or 0))
                )


# ---- Single-supplier groups (info) ---------------------------------------

st.divider()
with st.expander(t("sourcing.single_title")):
    single_df = sourcing.list_groups(min_offers=1)
    single_only = single_df[single_df["offer_count"] == 1] if not single_df.empty else single_df
    if single_only.empty:
        st.caption(t("sourcing.no_single"))
    else:
        st.caption(t("sourcing.single_explain"))
        st.dataframe(
            single_only[["canonical_name", "brand", "min_cost"]].rename(columns={
                "canonical_name": t("sourcing.product"),
                "brand": t("upload.field.brand"),
                "min_cost": t("common.cost"),
            }),
            width='stretch',
            hide_index=True,
            column_config={
                t("common.cost"): st.column_config.NumberColumn(format="฿%.0f"),
            },
        )


# ---- Ungroupable products ------------------------------------------------

ungrp = sourcing.ungrouped_products()
if not ungrp.empty:
    with st.expander(t("sourcing.ungrouped_title", n=len(ungrp))):
        st.caption(t("sourcing.ungrouped_help"))
        st.dataframe(
            ungrp.rename(columns={
                "sku": "SKU",
                "brand": t("upload.field.brand"),
                "name": t("upload.field.name").rstrip(" *"),
                "cost_price": t("common.cost"),
            }),
            width='stretch',
            hide_index=True,
            column_config={
                t("common.cost"): st.column_config.NumberColumn(format="฿%.0f"),
            },
            height=300,
        )
