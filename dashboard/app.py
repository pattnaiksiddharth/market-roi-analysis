"""
app.py – Entry point for the Marketing ROI Streamlit dashboard.

Run with:
    streamlit run app.py

Navigation uses st.navigation / st.Page (Streamlit ≥ 1.36).
Global CSS and sidebar filters are loaded here so every page inherits them.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# ── Make project root importable ───────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Page config ────────────────────────────────────────────────────────────────
_LOGO_PATH = ROOT / "assets" / "logo.png"
st.set_page_config(
    page_title="Marketing ROI Dashboard",
    page_icon=str(_LOGO_PATH) if _LOGO_PATH.exists() else "📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Marketing ROI Dashboard · Built with Streamlit",
    },
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
_CSS_PATH = ROOT / "assets" / "style.css"
if _CSS_PATH.exists():
    with open(_CSS_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Additional inline CSS tweaks ───────────────────────────────────────────────
st.markdown("""
<style>
/* Hide default Streamlit header and remove space */
#MainMenu, footer, header, [data-testid="stHeader"], .stHeader {
    display: none !important;
    height: 0px !important;
    visibility: hidden !important;
}
[data-testid="stSidebarNav"] { display: none; }
[data-testid="stSidebarHeader"], [data-testid="stSidebarCollapseButton"] { display: none !important; }
section[data-testid="stSidebar"], [data-testid="stSidebarUserContent"], [data-testid="stSidebarContent"], [data-testid="stSidebar"] > div {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
}
.main .block-container, [data-testid="stMainBlockContainer"], .stMainBlockContainer, .block-container {
    padding-top: 0.15rem !important;
    margin-top: 0rem !important;
}
/* Active page highlight */
.nav-btn-active button {
    background: linear-gradient(135deg, #4f6cf7, #8b5cf6) !important;
    color: white !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Data loading (shared) ─────────────────────────────────────────────────────
from utils.data_loader import load_fact
df_raw = load_fact()

# ── Sidebar Brand Header (starts right at top of sidebar) ─────────────────────
from components.filters import render_sidebar_brand, render_sidebar_filter_controls
render_sidebar_brand()

# ── Navigation ─────────────────────────────────────────────────────────────────
PAGES = {
    "📊 Overview":            "page_overview",
    "🔻 Funnel & Acquisition": "page_funnel",
    "📡 Channel Performance": "page_channel",
    "💰 Budget Scenario":     "page_budget",
}

st.sidebar.markdown(
    '<div style="margin: 4px 0 6px;font-size:0.68rem;font-weight:800;'
    'color:#4f6cf7;letter-spacing:0.1em;text-transform:uppercase">Navigation</div>',
    unsafe_allow_html=True,
)

if "active_page" not in st.session_state:
    st.session_state["active_page"] = list(PAGES.keys())[0]

for label in PAGES:
    is_active = st.session_state["active_page"] == label
    btn_style = "nav-btn-active" if is_active else ""
    with st.sidebar:
        col = st.container()
        with col:
            st.markdown(f'<div class="{btn_style}">', unsafe_allow_html=True)
            if st.button(label, width='stretch', key=f"nav_{label}"):
                st.session_state["active_page"] = label
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ── Sidebar Global Filters ─────────────────────────────────────────────────────
render_sidebar_filter_controls(df_raw)

# ── Render active page ─────────────────────────────────────────────────────────
active_label  = st.session_state["active_page"]
active_module = PAGES[active_label]

import importlib
page_mod = importlib.import_module(f"pages.{active_module}")
page_mod.show()
