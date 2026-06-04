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
    with st.expander(f["label"], expanded=True):
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
        {"label": "Electronics / IT", "markup": 15, "round_to": 10},
        {"label": "Accessories",       "markup": 30, "round_to": 10},
        {"label": "Premium / Luxury",  "markup": 20, "round_to": 50},
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
    if st.button(t("common.save") + " presets", type="primary", width='stretch'):
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
                f"{apply_label}: {row['label']}",
                key=f"apply_{i}",
                width='stretch',
            ):
                st.session_state["markup"] = int(row["markup"])
                st.session_state["round_to"] = int(row["round_to"])
                st.success(f"{row['label']} → markup {int(row['markup'])}%, round ฿{int(row['round_to'])}")
                st.rerun()
