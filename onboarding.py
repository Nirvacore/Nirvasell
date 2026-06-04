"""Two things in one module:

1. `tip(key)` — dismissible info box (per-session). Drop at top of any page
    for contextual hints.

2. Onboarding wizard state machine — tracks which steps a user completed
    (persisted in user_settings, survives login). Used by the Start Here
    wizard page and the first-run banner on app.py.

Steps:
    1  api_key          — user pasted Anthropic API key
    2  first_product    — added at least one product (manual or Vision)
    3  first_generate   — ran any AI task at least once
    4  first_export     — downloaded a marketplace CSV
    5  done             — wizard explicitly dismissed
"""
from __future__ import annotations
import streamlit as st

import db
from i18n import t


WIZARD_STEPS = ["api_key", "first_product", "first_generate", "first_export", "done"]
_SETTING_KEY = "onboarding.completed_steps"


# ---- Dismissible tip (per-session) -------------------------------------

def tip(key: str, body_key: str | None = None):
    """Show a dismissible info box once per session for `key`."""
    state_key = f"_tip_dismissed_{key}"
    if st.session_state.get(state_key):
        return

    body = t(body_key) if body_key else t(f"tip.{key}")
    c1, c2 = st.columns([10, 1])
    with c1:
        st.info(f"💡 {body}")
    with c2:
        if st.button("✕", key=f"close_tip_{key}", help=t("tip.dismiss")):
            st.session_state[state_key] = True
            st.rerun()


# ---- Wizard state (per-user, persisted) --------------------------------

def _us():
    """Lazy import to avoid circular import at module load."""
    import user_settings
    return user_settings


def completed_steps() -> list[str]:
    """Steps the user has finished."""
    try:
        val = _us().get(_SETTING_KEY, default=[])
        return val if isinstance(val, list) else []
    except Exception:
        return []


def mark_step(step: str) -> None:
    """Idempotent — call freely from any flow when a milestone happens."""
    if step not in WIZARD_STEPS:
        return
    try:
        done = set(completed_steps())
        if step in done:
            return
        done.add(step)
        _us().set(_SETTING_KEY, sorted(done, key=WIZARD_STEPS.index))
    except Exception:
        pass


def current_step() -> str | None:
    """First step that's not yet completed, or None if all done."""
    done = set(completed_steps())
    for s in WIZARD_STEPS:
        if s not in done:
            return s
    return None


def is_complete() -> bool:
    return "done" in completed_steps()


def progress() -> tuple[int, int]:
    """(completed_count, total) — for progress bars."""
    done = [s for s in completed_steps() if s in WIZARD_STEPS]
    return (len(done), len(WIZARD_STEPS))


def reset() -> None:
    """Restart the wizard from scratch (used in Account → debug)."""
    try:
        _us().set(_SETTING_KEY, [])
    except Exception:
        pass


# ---- Auto-detect milestones --------------------------------------------

def autodetect_progress() -> None:
    """Call from app.py / Start page to update state based on actual DB
    contents. So if a user creates a product via the API or imports CSV,
    we still credit them for `first_product` without having to instrument
    every code path."""
    try:
        # api_key
        if st.session_state.get("api_key"):
            mark_step("api_key")

        with db.conn() as c:
            # first_product
            n_products = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if n_products > 0:
                mark_step("first_product")
            # first_generate
            try:
                n_gen = c.execute("SELECT COUNT(*) FROM history").fetchone()[0]
                if n_gen > 0:
                    mark_step("first_generate")
            except Exception:
                pass
    except Exception:
        pass


# ---- First-run banner --------------------------------------------------

def first_run_banner():
    """Show a polite CTA at the top of any page if onboarding isn't done.
    Auto-detects progress before deciding."""
    autodetect_progress()
    if is_complete():
        return
    done, total = progress()
    if done >= total - 1:  # only "done" step left → auto-mark complete
        mark_step("done")
        return

    c1, c2 = st.columns([8, 2])
    with c1:
        st.info(
            f"👋 {t('onboard.banner_title')} — "
            f"{t('onboard.banner_progress', n=done, total=total - 1)}"
        )
    with c2:
        st.page_link("pages/0_🚀_Start.py", label=f"▶ {t('onboard.banner_cta')}")
