"""Policies — keep marketplace fees + rules current.

User adds / edits source URLs per platform. Click 'Fetch' to pull latest text,
let Claude extract fee structure, see diff, click 'Apply' to update fees.

If fetch fails (Cloudflare / JS-only pages), user pastes the policy text
directly — Claude parses either way."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import fees as fees_mod
import policy_watcher as pw
import knowledge_hub as kh
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import friendly_error
from i18n import t

db.init()
kh.init()
st.set_page_config(page_title="nirva.sell · Policies", page_icon="📋", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="📋", title=t("policy.title"), subtitle=t("policy.caption"))


# ---- Sources registry ----------------------------------------------------

st.markdown(f"## {t('policy.sources_title')}")
st.caption(t("policy.sources_help"))

sources = pw.load_sources()
df = pd.DataFrame(sources)

edited = st.data_editor(
    df,
    width='stretch',
    num_rows="dynamic",
    column_config={
        "platform": st.column_config.TextColumn(t("policy.col_platform"), width="small"),
        "label": st.column_config.TextColumn(t("policy.col_label"), width="medium"),
        "url": st.column_config.LinkColumn(t("policy.col_url")),
        "language": st.column_config.SelectboxColumn(
            t("policy.col_language"),
            options=["th", "en", "zh", "ja", "ko", "vi", "id"],
            width="small",
        ),
    },
    hide_index=True,
    key="sources_editor",
)

c_save, _ = st.columns([1, 4])
with c_save:
    if st.button(t("common.save"), type="primary", width='stretch'):
        pw.save_sources(edited.to_dict("records"))
        st.success(t("common.saved"))


# ---- Check each policy ---------------------------------------------------

st.divider()
st.markdown(f"## {t('policy.check_title')}")

api_key = st.session_state.get("api_key", "")

for s in sources:
    platform = s.get("platform")
    label = s.get("label", platform)
    url = s.get("url")
    if not platform or not url:
        continue

    with st.expander(f"**{label}** · `{platform}`"):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.caption(url)
        with c2:
            fetch_btn = st.button(
                t("policy.fetch_btn"),
                key=f"fetch_{platform}",
                width='stretch',
                disabled=not api_key,
            )
        with c3:
            paste_btn = st.button(
                t("policy.paste_btn"),
                key=f"paste_{platform}",
                width='stretch',
            )

        if paste_btn:
            st.session_state[f"paste_mode_{platform}"] = True

        if st.session_state.get(f"paste_mode_{platform}"):
            text = st.text_area(
                t("policy.paste_label"),
                placeholder=t("policy.paste_placeholder"),
                height=200,
                key=f"paste_text_{platform}",
            )
            do_parse = st.button(t("policy.parse_btn"), key=f"parse_{platform}", disabled=not (api_key and text))
            if do_parse:
                with st.spinner(t("policy.extracting")):
                    try:
                        new_data = pw.extract_fees_with_claude(text, platform, api_key=api_key)
                        st.session_state[f"new_data_{platform}"] = new_data
                    except Exception as e:
                        friendly_error(e)

        if fetch_btn:
            with st.spinner(t("policy.fetching")):
                fetch_result = pw.fetch_source(s)
            if not fetch_result.get("ok"):
                st.warning(t("policy.fetch_failed", status=fetch_result.get("status")))
                st.caption(t("policy.fetch_failed_hint"))
            else:
                with st.spinner(t("policy.extracting")):
                    try:
                        new_data = pw.extract_fees_with_claude(
                            fetch_result["text"], platform, api_key=api_key,
                        )
                        st.session_state[f"new_data_{platform}"] = new_data
                    except Exception as e:
                        friendly_error(e)

        # Show extracted data + diff
        nd = st.session_state.get(f"new_data_{platform}")
        if nd:
            st.markdown(f"**{t('policy.extracted')}**")
            current = fees_mod.load().get(platform, {})
            row = {
                t("policy.field"): ["Commission %", "Payment %", "Transaction %", "VAT on fees %"],
                t("policy.current"): [
                    current.get("commission_pct", 0),
                    current.get("payment_pct", 0),
                    current.get("transaction_pct", 0),
                    current.get("vat_on_fees", 0),
                ],
                t("policy.new"): [
                    nd.get("commission_pct", 0),
                    nd.get("payment_pct", 0),
                    nd.get("transaction_pct", 0),
                    nd.get("vat_on_fees", 0),
                ],
            }
            cmp_df = pd.DataFrame(row)
            cmp_df["Δ"] = cmp_df[t("policy.new")].astype(float) - cmp_df[t("policy.current")].astype(float)
            st.dataframe(
                cmp_df,
                width='stretch',
                hide_index=True,
                column_config={
                    t("policy.current"): st.column_config.NumberColumn(format="%.2f%%"),
                    t("policy.new"): st.column_config.NumberColumn(format="%.2f%%"),
                    "Δ": st.column_config.NumberColumn(format="%+.2f%%"),
                },
            )

            diffs = pw.compare(platform, nd)
            if diffs:
                st.warning(t("policy.changes_detected", n=len(diffs)))
                ca, cb = st.columns([1, 4])
                with ca:
                    if st.button(
                        t("policy.apply_btn"),
                        type="primary",
                        key=f"apply_{platform}",
                        width='stretch',
                    ):
                        pw.apply_update(platform, nd)
                        try:
                            kh.capture_policy_change(
                                platform,
                                diffs=pw.compare(platform, nd),
                                notes=nd.get("notes", ""),
                                effective_date=nd.get("effective_date", ""),
                                ref_key=f"{platform}:applied",
                                node_type="decision",
                            )
                        except Exception:
                            pass
                        st.session_state.pop(f"new_data_{platform}", None)
                        st.session_state.pop(f"paste_mode_{platform}", None)
                        st.success(t("policy.applied") + " · " + t("policy.hub_saved"))
                        st.rerun()
                with cb:
                    st.caption(t("policy.apply_hint"))
            else:
                st.success(t("policy.no_change"))

            if nd.get("notes"):
                st.markdown(f"**{t('policy.notes_label')}**")
                st.markdown(nd["notes"])

            if nd.get("effective_date"):
                st.caption(f"📅 {t('policy.effective_date')}: {nd['effective_date']}")


# ---- Audit log -----------------------------------------------------------

st.divider()
with st.expander(t("policy.history_title")):
    hist = pw.history()
    if not hist:
        st.caption(t("policy.no_history"))
    else:
        for h in hist[:15]:
            st.markdown(
                f"**{h.get('at','')[:16]}** · `{h.get('platform','')}` — "
                f"commission {h['applied'].get('commission_pct','?')}% · "
                f"payment {h['applied'].get('payment_pct','?')}%"
            )
            if h.get("notes"):
                st.caption(h["notes"][:200])
