"""Zen minimal theme — paper background, ink text, single sage accent.

Palette (Japanese stationery inspired):
  bg            #f7f4ec  warm paper
  surface       #ffffff  white card
  border        rgba(40,30,20,0.08)
  text          #1f1f1f  ink
  text-soft     #3d3d3d  body
  muted         #6b6b6b  meta
  accent        #4d6c5c  sage
  accent-bg     rgba(77,108,92,0.08)

Goals:
- High contrast (WCAG AA+)
- Wide breathing room
- One quiet accent, no neon
"""
import streamlit as st


CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Sans+Thai:wght@400;500;600&family=Noto+Sans+SC:wght@400;500;600&family=Noto+Sans+JP:wght@400;500;600&family=Noto+Sans+KR:wght@400;500;600&family=Cormorant+Garamond:wght@500;600&display=swap');

  :root {
    --bg: #f7f4ec;
    --surface: #ffffff;
    --surface-alt: #fbf9f3;
    --border: rgba(40,30,20,0.10);
    --border-strong: rgba(40,30,20,0.18);
    --text: #1f1f1f;
    --text-soft: #3d3d3d;
    --muted: #6b6b6b;
    --accent: #4d6c5c;
    --accent-bg: rgba(77,108,92,0.08);
    --accent-strong: #2d4a3e;
  }

  html, body, .stApp, [class*="css"] {
    font-family: 'Inter', 'IBM Plex Sans Thai', 'Noto Sans SC', 'Noto Sans JP', 'Noto Sans KR', system-ui, sans-serif !important;
    color: var(--text-soft);
  }

  .stApp { background: var(--bg); }

  /* Typography — high contrast for readability */
  .stMarkdown, p, label, [data-testid="stCaptionContainer"] {
    color: var(--text-soft) !important;
    font-size: 0.95rem;
    line-height: 1.6;
  }
  [data-testid="stCaptionContainer"] { color: var(--muted) !important; font-size: 0.88rem; }

  h1, h2, h3, h4 {
    color: var(--text) !important;
    font-weight: 600 !important;
    letter-spacing: -0.012em;
  }
  h1 {
    font-family: 'Cormorant Garamond', 'IBM Plex Sans Thai', serif !important;
    font-size: 2rem !important;
    font-weight: 500 !important;
    margin-bottom: 0.2rem !important;
    letter-spacing: -0.01em !important;
    color: var(--text) !important;
  }
  h2 {
    font-size: 0.78rem !important;
    margin-top: 1.8rem !important;
    font-weight: 600 !important;
    color: var(--muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  h3 { font-size: 1rem !important; font-weight: 600 !important; color: var(--text) !important; }

  /* Metrics — refined */
  div[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 500;
  }
  div[data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-family: 'Cormorant Garamond', Inter, serif !important;
    font-size: 1.6rem !important;
    font-weight: 500 !important;
  }

  /* Buttons — Zen minimal */
  .stButton > button {
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border-strong);
    font-weight: 500;
    padding: 0.55rem 1.1rem;
    border-radius: 6px;
    transition: all .15s;
    font-size: 0.9rem;
    box-shadow: 0 1px 0 rgba(0,0,0,0.02);
  }
  .stButton > button:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-bg);
  }
  .stButton > button[kind="primary"] {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
    font-weight: 600;
  }
  .stButton > button[kind="primary"]:hover {
    background: var(--accent-strong);
    border-color: var(--accent-strong);
    color: #fff;
  }
  .stButton > button:disabled { opacity: 0.4; }

  .stDownloadButton > button {
    background: var(--surface);
    border: 1px solid var(--border-strong);
    color: var(--text);
    font-weight: 500;
    border-radius: 6px;
  }
  .stDownloadButton > button:hover { border-color: var(--accent); color: var(--accent); }

  /* File uploader */
  [data-testid="stFileUploader"] section {
    background: var(--surface);
    border: 1.5px dashed var(--border-strong);
    border-radius: 10px;
    padding: 1.2rem;
    color: var(--muted);
  }
  [data-testid="stFileUploader"] section:hover { border-color: var(--accent); }

  /* Inputs — high contrast */
  input, textarea, select,
  .stSelectbox > div > div,
  .stTextInput input,
  .stNumberInput input {
    background: var(--surface) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
    border: 1px solid var(--border) !important;
    font-size: 0.92rem !important;
  }
  input:focus, textarea:focus, .stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-bg) !important;
  }
  input::placeholder { color: var(--muted) !important; opacity: 0.7; }

  /* Sliders */
  .stSlider [data-baseweb="slider"] > div > div { background: var(--accent) !important; }
  .stSlider [data-baseweb="slider"] [role="slider"] { background: var(--accent) !important; border-color: var(--accent) !important; }

  /* Tables */
  [data-testid="stDataFrame"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }
  [data-testid="stDataFrame"] [role="columnheader"] {
    font-weight: 600 !important;
    color: var(--muted) !important;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  [data-testid="stDataFrame"] [role="row"]:hover { background: var(--accent-bg) !important; }

  /* Sidebar — quiet */
  [data-testid="stSidebar"] {
    background: var(--surface-alt);
    border-right: 1px solid var(--border);
    min-width: 248px !important;
  }
  [data-testid="stSidebar"] > div { padding-top: 0.5rem; }
  [data-testid="stSidebarNav"] { padding-top: 0; margin-bottom: 0.5rem; }
  [data-testid="stSidebarNav"] a {
    border-radius: 6px;
    padding: 7px 10px;
    transition: all .15s;
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--muted);
  }
  [data-testid="stSidebarNav"] a:hover { background: var(--bg); color: var(--text); }
  [data-testid="stSidebarNav"] a[aria-current="page"] {
    background: var(--accent-bg);
    color: var(--accent-strong);
    font-weight: 600;
  }

  /* Alerts — softly tinted */
  [data-testid="stAlert"] {
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-soft);
    padding: 0.8rem 1rem;
    font-size: 0.9rem;
  }

  /* Radio (task picker) — pills */
  .stRadio > div { gap: 6px; flex-wrap: wrap; }
  .stRadio label {
    font-size: 0.9rem !important;
    padding: 7px 14px;
    border-radius: 999px;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-soft);
    cursor: pointer;
    transition: all .15s;
  }
  .stRadio label:hover { color: var(--accent); border-color: var(--accent); }
  .stRadio [data-testid="stMarkdownContainer"] p { margin: 0 !important; font-size: 0.9rem !important; }

  /* Expanders */
  [data-testid="stExpander"] details {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  [data-testid="stExpander"] summary {
    font-weight: 500;
    color: var(--text);
    padding: 0.7rem 1rem !important;
  }
  [data-testid="stExpander"] summary:hover { color: var(--accent); }

  /* Code */
  code {
    background: var(--surface-alt) !important;
    color: var(--accent-strong) !important;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.85em;
    border: 1px solid var(--border);
  }

  /* Hide Streamlit chrome */
  #MainMenu, footer, [data-testid="stToolbar"] button[title="View fullscreen"] { display: none; }
  header[data-testid="stHeader"] { background: transparent; }

  /* Dividers */
  hr { border-color: var(--border) !important; margin: 1.4rem 0 !important; }

  /* Tighter overall */
  .main .block-container { padding-top: 1.8rem; padding-bottom: 2.5rem; max-width: 1140px; }

  /* Product thumbnail cards */
  .nirva-thumb {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px;
    transition: border-color .15s;
  }
  .nirva-thumb:hover { border-color: var(--accent); }

  /* Tag/chip */
  .nirva-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    background: var(--accent-bg);
    color: var(--accent-strong);
    font-size: 0.78rem;
    margin: 2px 4px 2px 0;
    border: 1px solid var(--border);
  }

  /* ─────────────────────────────────────────────────────────
     v35: Auth-screen polish — make Streamlit's stock primitives
     look like Linear/Notion/Stripe (modern, breathing room, soft
     shadows, sage accent on focus, big touch targets).
     ───────────────────────────────────────────────────────── */

  /* Inputs — bigger, softer, focus glow */
  .stTextInput input,
  .stPasswordInput input,
  .stTextArea textarea,
  .stNumberInput input {
    height: 48px;
    border-radius: 10px !important;
    border: 1px solid #e7e2d5 !important;
    padding: 0 16px !important;
    font-size: 15px !important;
    background: #fbf9f3 !important;
    color: #1f1f1f !important;
    transition: border-color .15s ease, background .15s ease, box-shadow .15s ease;
    box-shadow: none !important;
  }
  .stTextArea textarea { height: auto; padding: 12px 16px !important; }
  .stTextInput input::placeholder,
  .stPasswordInput input::placeholder,
  .stTextArea textarea::placeholder {
    color: #b4b0a4 !important;
  }
  .stTextInput input:focus,
  .stPasswordInput input:focus,
  .stTextArea textarea:focus,
  .stNumberInput input:focus {
    background: #ffffff !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(77,108,92,0.12) !important;
    outline: none !important;
  }
  /* Streamlit wraps the input in a div with a default border — kill it */
  .stTextInput > div > div,
  .stPasswordInput > div > div,
  .stTextArea > div > div {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
  }
  /* Label spacing above inputs */
  .stTextInput label,
  .stPasswordInput label,
  .stTextArea label,
  .stNumberInput label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #4a4a4a !important;
    margin-bottom: 6px !important;
    padding: 0 !important;
  }

  /* Buttons — bigger, smoother, hover lift */
  .stButton button,
  .stFormSubmitButton button,
  .stLinkButton a {
    height: 48px;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 15px !important;
    padding: 0 18px !important;
    transition: transform .15s ease, box-shadow .15s ease,
                background .15s ease, color .15s ease;
    border: 1px solid #e7e2d5 !important;
  }
  .stButton button:hover,
  .stFormSubmitButton button:hover,
  .stLinkButton a:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 14px rgba(31,31,31,0.06);
  }
  /* Primary CTA — sage green */
  .stButton button[kind="primary"],
  .stFormSubmitButton button[kind="primary"],
  .stFormSubmitButton button[kind="primaryFormSubmit"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: white !important;
    box-shadow: 0 1px 2px rgba(77,108,92,0.10);
  }
  .stButton button[kind="primary"]:hover,
  .stFormSubmitButton button[kind="primary"]:hover,
  .stFormSubmitButton button[kind="primaryFormSubmit"]:hover {
    background: #3d5749 !important;
    border-color: #3d5749 !important;
    box-shadow: 0 6px 18px rgba(77,108,92,0.25);
  }
  /* Tertiary links — used for mode switching */
  .stButton button[kind="tertiary"] {
    background: transparent !important;
    border-color: transparent !important;
    color: var(--accent) !important;
    height: 36px;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 0 8px !important;
  }
  .stButton button[kind="tertiary"]:hover {
    background: rgba(77,108,92,0.06) !important;
    color: #3d5749 !important;
    transform: none;
    box-shadow: none;
  }

  /* Auth-screen specific layout — class added by _auth_gate.py */
  body.nirva-auth {
    background:
      radial-gradient(ellipse at top, rgba(77,108,92,0.06) 0%, transparent 60%),
      linear-gradient(180deg, #faf7ef 0%, #f4f0e6 100%) !important;
  }
  .nirva-auth-card {
    background: white;
    border-radius: 16px;
    padding: 36px 32px;
    box-shadow:
      0 1px 2px rgba(31,31,31,0.04),
      0 8px 28px rgba(31,31,31,0.06);
    border: 1px solid rgba(40,30,20,0.04);
  }
  .nirva-auth-card h1, .nirva-auth-card h2, .nirva-auth-card h3 {
    margin: 0;
  }
  .nirva-auth-brand {
    text-align: center;
    margin-bottom: 28px;
  }
  .nirva-auth-brand .crescent {
    width: 56px; height: 56px;
    margin: 0 auto 12px;
    display: block;
  }
  .nirva-auth-brand .wordmark {
    font-family: 'Cormorant Garamond', 'EB Garamond', Georgia, serif;
    font-size: 2.2rem;
    font-weight: 500;
    letter-spacing: -0.02em;
    color: #1f1f1f;
    line-height: 1.1;
  }
  .nirva-auth-brand .wordmark .accent { color: var(--accent); }
  .nirva-auth-brand .tagline {
    color: #7a7569;
    font-size: 14px;
    margin-top: 6px;
  }
  .nirva-auth-head {
    font-family: 'Cormorant Garamond', 'EB Garamond', Georgia, serif;
    font-size: 1.7rem;
    font-weight: 500;
    text-align: center;
    color: #1f1f1f;
    letter-spacing: -0.01em;
    line-height: 1.2;
  }
  .nirva-auth-sub {
    color: #7a7569;
    font-size: 14px;
    text-align: center;
    margin: 6px 0 26px;
    line-height: 1.5;
  }
  .nirva-auth-divider {
    display: flex; align-items: center;
    color: #b4b0a4; font-size: 11px;
    letter-spacing: 1.5px; text-transform: uppercase;
    margin: 18px 0 16px;
  }
  .nirva-auth-divider::before,
  .nirva-auth-divider::after {
    content: ''; flex: 1; height: 1px;
    background: rgba(40,30,20,0.10);
  }
  .nirva-auth-divider span { padding: 0 14px; }
  .nirva-auth-switch {
    text-align: center;
    margin-top: 22px;
    padding-top: 18px;
    border-top: 1px solid rgba(40,30,20,0.06);
    color: #7a7569;
    font-size: 14px;
  }
  .nirva-auth-footer {
    max-width: 420px;
    margin: 18px auto 0;
    text-align: center;
    color: #9a9485;
    font-size: 12px;
    line-height: 1.7;
  }
  .nirva-auth-footer a { color: #7a7569; text-decoration: none; }
  .nirva-auth-footer a:hover { color: var(--accent); }

  /* Hide Streamlit's default top toolbar on the auth screen so it
     truly looks like a marketing landing, not a dashboard. */
  body.nirva-auth header[data-testid="stHeader"] {
    background: transparent !important;
  }
  body.nirva-auth [data-testid="stDecoration"] { display: none !important; }

  /* Responsive — tablet */
  @media (max-width: 1024px) {
    h1 { font-size: 1.8rem !important; }
    h2 { font-size: 1.3rem !important; }
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
  }

  /* Responsive — phone */
  @media (max-width: 720px) {
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.15rem !important; }
    h3 { font-size: 1.0rem !important; }
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
    .block-container { padding: 0.5rem !important; }
    /* Stack metric cards */
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.78rem !important; }
    /* Tighter dataframe on small screens */
    .stDataFrame { font-size: 0.85rem; }
    /* Bigger touch targets */
    .stButton button { min-height: 44px; font-size: 0.95rem !important; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        font-size: 16px !important;  /* prevents iOS auto-zoom on focus */
    }
    /* Tabs scroll horizontally instead of wrapping/overflowing */
    [data-testid="stTabs"] [role="tablist"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
        scrollbar-width: thin;
    }
    /* Sidebar full-width when open on mobile */
    section[data-testid="stSidebar"] { width: 80vw !important; }
  }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
