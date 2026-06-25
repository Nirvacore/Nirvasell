"""Settings — fee overrides + markup presets (no JSON editing required)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import streamlit as st
import db
import fees as fees_mod
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from i18n import t
from i18n_inline import marketplace_fee_label, markup_preset_label
from _components import page_header

db.init()
st.set_page_config(page_title="nirva · Settings", page_icon="⚙️", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="⚙️", title=t("settings.title"), subtitle=t("settings.caption"))


# ----- Platform fees ------------------------------------------------------

st.subheader(t("settings.fees_title"))
st.caption(t("settings.fees_help"))

current = fees_mod.load()
edited: dict[str, dict] = {}

for key, f in current.items():
    with st.expander(marketplace_fee_label(key), expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        edited[key] = {
            **f,
            "commission_pct": c1.number_input(
                t("settings.commission"),
                min_value=0.0, max_value=30.0, step=0.1,
                value=float(f.get("commission_pct", 0)),
                key=f"comm_{key}",
            ),
            "payment_pct": c2.number_input(
                t("settings.payment"),
                min_value=0.0, max_value=10.0, step=0.1,
                value=float(f.get("payment_pct", 0)),
                key=f"pay_{key}",
            ),
            "transaction_pct": c3.number_input(
                t("settings.transaction"),
                min_value=0.0, max_value=10.0, step=0.1,
                value=float(f.get("transaction_pct", 0)),
                key=f"txn_{key}",
            ),
            "vat_on_fees": c4.number_input(
                t("settings.vat"),
                min_value=0.0, max_value=20.0, step=0.5,
                value=float(f.get("vat_on_fees", 0)),
                key=f"vat_{key}",
            ),
        }

c_save, c_reset, _ = st.columns([1, 1, 4])
with c_save:
    if st.button(t("common.save"), type="primary", width='stretch'):
        fees_mod.save(edited)
        st.success(t("common.saved"))
with c_reset:
    if st.button(t("settings.reset_default"), width='stretch'):
        if fees_mod.OVERRIDES_PATH.exists():
            fees_mod.OVERRIDES_PATH.unlink()
        st.success(t("common.saved"))
        st.rerun()


# ----- LINE Notify --------------------------------------------------------

st.divider()
st.subheader(f"💚 {t('line.title')}")
st.caption(t("line.caption"))

import user_settings as us
us.init()
import line_notify

token = us.get("line_notify_token", "")
if token:
    status = line_notify.check_token(token)
    if status["ok"]:
        st.success(f"✓ {t('line.connected')} → {status['target']}")
    else:
        st.warning(t("line.not_connected"))

with st.form("line_setup"):
    n_token = st.text_input(
        t("line.token_label"),
        value=token or "",
        type="password",
        help=t("line.token_help"),
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.form_submit_button(t("common.save"), type="primary"):
            us.set("line_notify_token", n_token.strip())
            st.success(t("common.saved"))
            st.rerun()
    with c2:
        if st.form_submit_button(t("line.test_btn")):
            if n_token.strip():
                result = line_notify.send(n_token.strip(), t("line.test_message"))
                if result["ok"]:
                    st.success(t("line.test_ok"))
                else:
                    st.error(f"{t('line.test_fail')} ({result['message']})")
            else:
                st.warning(t("line.token_help"))

with st.expander(t("line.setup_title")):
    st.markdown(t("line.setup_steps"))

st.markdown(f"#### {t('line.alerts_title')}")
alert_cols = st.columns(4)
with alert_cols[0]:
    al_orders = st.checkbox(t("line.alert_orders"),
        value=us.get("line_alert_orders", True) if us.get("line_alert_orders") is not None else True)
    us.set("line_alert_orders", al_orders)
with alert_cols[1]:
    al_stock = st.checkbox(t("line.alert_stock"),
        value=us.get("line_alert_stock", True) if us.get("line_alert_stock") is not None else True)
    us.set("line_alert_stock", al_stock)
with alert_cols[2]:
    al_daily = st.checkbox(t("line.alert_daily"),
        value=us.get("line_alert_daily", False) if us.get("line_alert_daily") is not None else False)
    us.set("line_alert_daily", al_daily)
with alert_cols[3]:
    al_slips = st.checkbox(t("line.alert_slips"),
        value=us.get("line_alert_slips", False) if us.get("line_alert_slips") is not None else False)
    us.set("line_alert_slips", al_slips)


# ----- Markup presets ----------------------------------------------------

st.divider()
st.subheader(t("settings.presets_title"))
st.caption(t("settings.presets_help"))

PRESETS_PATH = fees_mod.OVERRIDES_PATH.parent / "markup_presets.json"

def load_presets() -> list[dict]:
    if PRESETS_PATH.exists():
        try:
            return json.loads(PRESETS_PATH.read_text())
        except Exception:
            pass
    return [
        {"preset_key": "electronics", "markup": 15, "round_to": 10},
        {"preset_key": "accessories", "markup": 30, "round_to": 10},
        {"preset_key": "premium", "markup": 20, "round_to": 50},
    ]

presets = load_presets()
import pandas as pd
df = pd.DataFrame(presets)
edited_df = st.data_editor(
    df,
    width='stretch',
    num_rows="dynamic",
    column_config={
        "label": st.column_config.TextColumn(t("settings.preset_name"), width="medium"),
        "markup": st.column_config.NumberColumn(t("sidebar.markup"), format="%d%%", width="small"),
        "round_to": st.column_config.NumberColumn(t("sidebar.round_to"), format="฿%d", width="small"),
    },
    hide_index=True,
    key="presets_editor",
)

c1, c2 = st.columns([1, 4])
with c1:
    if st.button(t("settings.save_presets_btn"), type="primary", width='stretch'):
        PRESETS_PATH.write_text(json.dumps(edited_df.to_dict("records"), indent=2, ensure_ascii=False))
        st.success(t("common.saved"))

with c2:
    apply_label = t("settings.apply_preset")
    cols = st.columns(min(len(edited_df), 4) or 1)
    for i, (_, row) in enumerate(edited_df.iterrows()):
        if i >= len(cols):
            break
        with cols[i]:
            if st.button(
                f"{apply_label}: {markup_preset_label(row.to_dict())}",
                key=f"apply_{i}",
                width='stretch',
            ):
                st.session_state["markup"] = int(row["markup"])
                st.session_state["round_to"] = int(row["round_to"])
                st.success(t("settings.preset_applied",
                             label=markup_preset_label(row.to_dict()),
                             markup=int(row["markup"]),
                             round_to=int(row["round_to"])))
                st.rerun()
