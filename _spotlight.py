"""Cmd+K spotlight search — the world-class pattern from Stripe, Linear,
Notion, GitHub. Press ⌘K (or Ctrl+K) anywhere to open a centered dialog
that fuzzy-searches across:

  • All 23 pages (jump to nav targets)
  • Recent products in your catalog (jump to product detail)
  • All AI tasks (jump to Generate page with task pre-selected)
  • Quick actions ("Add product", "Try demo", "Logout")

Implementation notes:
  Streamlit's `st.dialog` is the cleanest container. We expose a visible
  "🔍 Search" button in the sidebar that opens the dialog AND inject a
  tiny JS listener that programmatically clicks that button on ⌘K.
  Search is client-side substring filtering — fast enough for ~50 items."""
from __future__ import annotations
import streamlit as st


# Page roster — keep in sync with pages/*.py. Format: (path, icon, label_key,
# blurb_key). label_key looks up the SHORT page name in i18n.
PAGES = [
    ("app.py",                            "✨", "qa.start",          "ws.subtitle"),
    ("pages/0_🚀_Start.py",              "🚀", "onboard.title",     "onboard.caption"),
    ("pages/2_📦_Catalog.py",            "📦", "catalog.title",     "catalog.caption"),
    ("pages/3_🤖_Generate.py",           "🤖", "generate.title",    "generate.caption"),
    ("pages/4_📜_History.py",            "📜", "history.title",     "history.caption"),
    ("pages/5_🔌_Import.py",             "🔌", "import.title",      "import.caption"),
    ("pages/8_📸_Vision.py",             "📸", "vision.title",      "vision.caption"),
    ("pages/9_🌍_Global.py",             "🌍", "global.title",      "global.caption"),
    ("pages/F_📈_Dashboard.py",          "📈", "dashboard.title",   "dashboard.caption"),
    ("pages/D_🔀_Sourcing.py",           "🔀", "sourcing.title",    "sourcing.caption"),
    ("pages/B_📊_Live.py",               "📊", "live.title",        "live.caption"),
    ("pages/K_📦_Fulfillment.py",        "📦", "fulfill.title",     "fulfill.caption"),
    ("pages/N_📥_Today.py",              "📥", "today.title",       "today.caption"),
    ("pages/E_📋_Policies.py",           "📋", "policy.title",      "policy.caption"),
    ("pages/J_✏_Custom_Tasks.py",       "✏", "custom_task.title", "custom_task.caption"),
    ("pages/C_🔔_Alerts.py",             "🔔", "alerts.title",      "alerts.caption"),
    ("pages/I_🔔_Notifications.py",      "🔔", "notif.title",       "notif.caption"),
    ("pages/A_💝_Support.py",            "💝", "support.title",     "support.caption"),
    ("pages/H_⚙_Account.py",             "⚙", "account.title",     "account.caption"),
    ("pages/G_👑_Admin.py",              "👑", "admin.title",       "admin.caption"),
    ("pages/7_💰_Pricing.py",            "💰", "pricing.title",     "pricing.caption"),
    ("pages/6_⚙️_Settings.py",           "⚙", "settings.title",    "settings.caption"),
    ("pages/M_⚖_Compare.py",             "⚖", "compare.title",     "compare.caption"),
    ("pages/L_📄_Legal.py",              "📄", "legal.title",       "legal.caption"),
]


def render_button():
    """Sidebar entry point. Renders a small search button + the JS that
    binds ⌘K / Ctrl+K to it."""
    from i18n import t

    # Visible button — labelled with the hotkey for discoverability
    if st.button(
        f"🔍 {t('spotlight.search')}  ⌘K",
        key="_spotlight_open_btn",
        type="tertiary",
        width="stretch",
        help=t("spotlight.help"),
    ):
        _open_dialog()

    # JS — clicks the button above when ⌘K (Mac) / Ctrl+K (PC) is pressed.
    # We find the button by its title text (Streamlit doesn't give stable IDs
    # but the text content is unique). Re-attaches per rerun, but de-dup'd
    # with a window-level flag.
    st.components.v1.html(
        """
<script>
(function(){
  if (window.__nirva_spotlight_bound) return;
  window.__nirva_spotlight_bound = true;
  window.parent.addEventListener('keydown', function(e){
    var isK = e.key === 'k' || e.key === 'K';
    var mod = e.metaKey || e.ctrlKey;
    if (mod && isK) {
      e.preventDefault();
      var doc = window.parent.document;
      var btns = doc.querySelectorAll('button');
      for (var i=0;i<btns.length;i++) {
        if (btns[i].innerText && btns[i].innerText.indexOf('⌘K') >= 0) {
          btns[i].click();
          break;
        }
      }
    }
  }, true);
})();
</script>
""",
        height=0,
    )


def _open_dialog():
    """Trigger the dialog via session_state — Streamlit's @st.dialog
    decorator needs to be called from the page's main script body. We set
    a flag here, and the page-level renderer (called from _sidebar.render)
    actually opens it."""
    st.session_state["_spotlight_open"] = True


def maybe_render_dialog():
    """Called from _sidebar after render_button so the dialog actually
    appears. Pattern: set flag → trigger decorated function."""
    if not st.session_state.get("_spotlight_open"):
        return

    @st.dialog(_dialog_title(), width="large")
    def _dlg():
        from i18n import t
        import db

        query = st.text_input(
            label="spotlight",
            label_visibility="collapsed",
            placeholder=t("spotlight.placeholder"),
            key="_spotlight_query",
            autocomplete="off",
        )
        q = (query or "").strip().lower()

        # ---- Section: pages ----
        st.markdown(
            f"<div style='font-size:11px;text-transform:uppercase;"
            f"letter-spacing:1px;color:#9a9485;margin:8px 0 4px'>"
            f"{t('spotlight.section_pages')}</div>",
            unsafe_allow_html=True,
        )
        page_hits = _filter_pages(q)
        if not page_hits:
            st.caption(t("spotlight.no_match"))
        for path, icon, label, blurb in page_hits[:8]:
            _row(icon, label, blurb, path, key=f"sp_pg_{path}")

        # ---- Section: products ----
        products = _recent_products(limit=40)
        prod_hits = _filter_products(q, products)
        if prod_hits:
            st.markdown(
                f"<div style='font-size:11px;text-transform:uppercase;"
                f"letter-spacing:1px;color:#9a9485;margin:18px 0 4px'>"
                f"{t('spotlight.section_products')}</div>",
                unsafe_allow_html=True,
            )
            for p in prod_hits[:6]:
                _row(
                    "📦",
                    f"{p.get('name') or '(no name)'}",
                    f"SKU {p['sku']} · ฿{int(p.get('sell_price') or 0):,}",
                    target="pages/2_📦_Catalog.py",
                    key=f"sp_pr_{p['id']}",
                )

        # ---- Section: AI tasks ----
        try:
            import tasks as task_registry
            from i18n import t as _t
            tasks_all = task_registry.BUILTIN
        except Exception:
            tasks_all = {}
        task_hits = _filter_tasks(q, tasks_all)
        if task_hits:
            st.markdown(
                f"<div style='font-size:11px;text-transform:uppercase;"
                f"letter-spacing:1px;color:#9a9485;margin:18px 0 4px'>"
                f"{t('spotlight.section_tasks')}</div>",
                unsafe_allow_html=True,
            )
            for key, mod in task_hits[:6]:
                _row(
                    mod.TASK.get("icon", "🤖"),
                    mod.TASK.get("label", key),
                    mod.TASK.get("blurb", ""),
                    target="pages/3_🤖_Generate.py",
                    key=f"sp_tk_{key}",
                )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.caption("Esc / click outside to close")

    _dlg()
    # Reset the flag after rendering so it doesn't reopen on rerun
    st.session_state["_spotlight_open"] = False


# ---- Helpers -----------------------------------------------------------

def _dialog_title() -> str:
    from i18n import t
    return f"🔍 {t('spotlight.title')}"


def _row(icon: str, label: str, blurb: str, target: str, *, key: str):
    """One result line — clickable, navigates to target page."""
    c1, c2 = st.columns([1, 9])
    with c1:
        st.markdown(
            f"<div style='font-size:22px;line-height:36px;text-align:center'>"
            f"{icon}</div>",
            unsafe_allow_html=True,
        )
    with c2:
        # We can't use page_link inside a dialog reliably — use a button that
        # rewrites the URL via st.switch_page.
        if st.button(
            f"**{label}**  \n*{blurb}*" if blurb else f"**{label}**",
            key=key,
            width="stretch",
            type="tertiary",
        ):
            try:
                st.switch_page(target)
            except Exception:
                # Fall back to closing dialog — user can click sidebar
                st.session_state["_spotlight_open"] = False
                st.rerun()


def _filter_pages(q: str):
    """Substring match against label + blurb (translated)."""
    from i18n import t
    out = []
    for path, icon, label_key, blurb_key in PAGES:
        label = t(label_key)
        blurb = t(blurb_key)
        hay = (label + " " + blurb + " " + path).lower()
        if not q or q in hay:
            out.append((path, icon, label, blurb))
    return out


def _filter_tasks(q: str, tasks_all: dict):
    out = []
    for key, mod in tasks_all.items():
        T = mod.TASK
        hay = (T.get("label", "") + " " + T.get("blurb", "") + " " + key).lower()
        if not q or q in hay:
            out.append((key, mod))
    return out


def _filter_products(q: str, products: list[dict]):
    if not q:
        # No query → show most recent
        return products[:10]
    out = []
    for p in products:
        hay = ((p.get("name") or "") + " " + (p.get("sku") or "")
               + " " + (p.get("brand") or "")).lower()
        if q in hay:
            out.append(p)
    return out


def _recent_products(limit: int = 40):
    """Pull a small recent-products list for the spotlight."""
    try:
        import db
        with db.conn() as c:
            rows = c.execute(
                "SELECT id, sku, name, brand, sell_price FROM products "
                "ORDER BY id DESC LIMIT ?", (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
