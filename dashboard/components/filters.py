"""
Global sidebar filters – rendered once, stored in st.session_state.
Every page reads from session_state; it never re-renders the filters itself.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from utils.theme import COLORS


import base64
from pathlib import Path


def render_sidebar_brand() -> None:
    """Render brand logo and title at the very top of the sidebar with zero dead space."""
    logo_file = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
    logo_img_html = ""
    if logo_file.exists():
        with open(logo_file, "rb") as lf:
            b64_data = base64.b64encode(lf.read()).decode("utf-8")
            logo_img_html = (
                f'<img src="data:image/png;base64,{b64_data}" '
                f'style="width:56px;height:56px;border-radius:50%;border:2px solid #4f6cf780;'
                f'box-shadow:0 0 12px rgba(79,108,247,0.4);margin-bottom:6px;'
                f'background:rgba(255,255,255,0.08);padding:3px;display:inline-block;" />'
            )

    sidebar_brand_html = (
        f'<div style="text-align:center;padding:4px 0 10px;margin-top:0;">{logo_img_html}'
        f'<div style="font-size:1.2rem;font-weight:800;background:linear-gradient(90deg,#4f6cf7,#a78bfa);'
        f'-webkit-background-clip:text;-webkit-text-fill-color:transparent">Marketing ROI</div>'
        f'<div style="font-size:0.68rem;color:#94a3b8;margin-top:2px">Where to invest, what to stop</div></div>'
    )
    st.sidebar.markdown(sidebar_brand_html, unsafe_allow_html=True)


def render_sidebar_filter_controls(df: pd.DataFrame) -> dict:
    """Render global filter controls in the sidebar."""
    c_blue = COLORS["accent_blue"]
    st.sidebar.markdown(
        f'<div style="font-size:0.7rem;font-weight:700;color:{c_blue};'
        f'letter-spacing:0.1em;text-transform:uppercase;margin:12px 0 6px">🎛️ Global Filters</div>',
        unsafe_allow_html=True,
    )

    # ── All unique values ─────────────────────────────────────────────────────
    all_channels      = sorted(df["channel"].unique().tolist())
    all_types         = sorted(df["campaign_type"].unique().tolist())
    all_locations     = sorted(df["location"].unique().tolist())
    min_date          = df["date"].min().date()
    max_date          = df["date"].max().date()

    # ── Initialise session_state defaults ────────────────────────────────────
    if "filters" not in st.session_state:
        st.session_state["filters"] = {
            "channels":          all_channels,
            "date_start":        min_date,
            "date_end":          max_date,
            "campaign_types":    all_types,
            "locations":         all_locations,
            "granularity":       "monthly",
            "new_customer_share": 0.7,
        }

    f = st.session_state["filters"]

    # ── Channel multiselect ───────────────────────────────────────────────────
    channels = st.sidebar.multiselect(
        "📡 Channels",
        options=all_channels,
        default=f.get("channels", all_channels),
        key="sb_channels",
    )

    # ── Date range ────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        '<div style="font-size:0.72rem;color:#94a3b8;margin-top:10px">📅 Date Range</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.sidebar.columns(2)
    date_start = col1.date_input(
        "From", value=f.get("date_start", min_date),
        min_value=min_date, max_value=max_date, key="sb_date_start", label_visibility="collapsed"
    )
    date_end = col2.date_input(
        "To", value=f.get("date_end", max_date),
        min_value=min_date, max_value=max_date, key="sb_date_end", label_visibility="collapsed"
    )

    # ── Campaign type ─────────────────────────────────────────────────────────
    campaign_types = st.sidebar.multiselect(
        "🎯 Campaign Types",
        options=all_types,
        default=f.get("campaign_types", all_types),
        key="sb_campaign_types",
    )

    # ── Location ──────────────────────────────────────────────────────────────
    locations = st.sidebar.multiselect(
        "📍 Locations",
        options=all_locations,
        default=f.get("locations", all_locations),
        key="sb_locations",
    )

    # ── Chart granularity ─────────────────────────────────────────────────────
    st.sidebar.markdown(
        '<div style="font-size:0.72rem;color:#94a3b8;margin-top:10px">📆 Time Granularity</div>',
        unsafe_allow_html=True,
    )
    granularity = st.sidebar.radio(
        "Time Granularity",
        options=["daily", "weekly", "monthly"],
        index=["daily", "weekly", "monthly"].index(f.get("granularity", "monthly")),
        horizontal=True,
        key="sb_granularity",
        label_visibility="collapsed",
    )

    # ── New-customer share assumption ─────────────────────────────────────────
    st.sidebar.markdown(
        '<div style="font-size:0.72rem;color:#94a3b8;margin-top:10px">👤 New-customer share (assumption)</div>',
        unsafe_allow_html=True,
    )
    new_customer_share = st.sidebar.number_input(
        "New-customer share",
        min_value=0.0, max_value=1.0,
        value=float(f.get("new_customer_share", 0.7)),
        step=0.05, format="%.2f",
        key="sb_new_customer_share",
        label_visibility="collapsed",
        help="Fraction of total conversions assumed to be new (first-time) customers. Affects CAC.",
    )

    # ── Reset button ──────────────────────────────────────────────────────────
    st.sidebar.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    reset = st.sidebar.button("🔄 Reset Filters", width='stretch', key="sb_reset")

    if reset:
        st.session_state["filters"] = {
            "channels":          all_channels,
            "date_start":        min_date,
            "date_end":          max_date,
            "campaign_types":    all_types,
            "locations":         all_locations,
            "granularity":       "monthly",
            "new_customer_share": 0.7,
        }
        st.rerun()

    # Update session state
    st.session_state["filters"] = {
        "channels":          channels if channels else all_channels,
        "date_start":        date_start,
        "date_end":          date_end,
        "campaign_types":    campaign_types if campaign_types else all_types,
        "locations":         locations if locations else all_locations,
        "granularity":       granularity,
        "new_customer_share": new_customer_share,
    }

    # ── Footer ────────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        f'<div style="position:fixed;bottom:10px;font-size:0.6rem;color:#4f6cf750;width:200px">'
        f'Marketing ROI Dashboard • Streamlit</div>',
        unsafe_allow_html=True,
    )

    return st.session_state["filters"]


def render_sidebar_filters(df: pd.DataFrame) -> dict:
    """Render full sidebar: brand header + global filter controls."""
    render_sidebar_brand()
    return render_sidebar_filter_controls(df)
