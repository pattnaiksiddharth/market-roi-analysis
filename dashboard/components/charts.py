"""
Reusable component builders.
Every page imports from here so styling is consistent.
"""

from __future__ import annotations

import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as _html_components

from utils.theme import COLORS, CHANNEL_COLORS, get_plotly_layout


def _render_html(html: str, height: int = 0) -> None:
    """Render raw HTML safely using st.components.v1.html.
    height=0 means auto-size (use a sensible minimum)."""
    _html_components.html(
        f"""<!DOCTYPE html><html><head>
<style>
  body {{margin:0;padding:0;background:transparent;font-family:'Inter',sans-serif;}}
  * {{box-sizing:border-box;}}
</style></head><body>{html}</body></html>""",
        height=max(height, 10),
        scrolling=False,
    )


# ─── FORMATTING HELPERS ───────────────────────────────────────────────────────

def fmt(val, style: str = "number", prefix: str = "", suffix: str = "") -> str:
    """
    Universal value formatter.
    style: 'number' | 'currency' | 'percent' | 'compact'
    """
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "–"
    if style == "percent":
        return f"{prefix}{val * 100:.2f}%{suffix}"
    if style == "currency":
        if abs(val) >= 1e9:
            return f"{prefix}₹{val/1e9:.2f}bn{suffix}"
        if abs(val) >= 1e6:
            return f"{prefix}₹{val/1e6:.2f}M{suffix}"
        if abs(val) >= 1e3:
            return f"{prefix}₹{val/1e3:.1f}K{suffix}"
        return f"{prefix}₹{val:.2f}{suffix}"
    if style == "compact":
        if abs(val) >= 1e9:
            return f"{prefix}{val/1e9:.2f}bn{suffix}"
        if abs(val) >= 1e6:
            return f"{prefix}{val/1e6:.2f}M{suffix}"
        if abs(val) >= 1e3:
            return f"{prefix}{val/1e3:.1f}K{suffix}"
        return f"{prefix}{val:.2f}{suffix}"
    return f"{prefix}{val:,.2f}{suffix}"


def fmt_currency(val) -> str:
    return fmt(val, "currency")


def fmt_pct(val) -> str:
    return fmt(val, "percent")


def fmt_compact(val) -> str:
    return fmt(val, "compact")


# ─── KPI CARD ─────────────────────────────────────────────────────────────────

def kpi_card(
    title: str,
    value: str,
    delta: str | None = None,
    delta_positive: bool | None = None,
    subtitle: str | None = None,
    tooltip: str | None = None,
    icon: str | None = None,
    accent_color: str | None = None,
    height: int = 110,
) -> None:
    """
    Render a single KPI card with optional delta badge as a distinct partition card.
    Rendered via st.markdown on a single non-indented string to avoid raw markdown escaping.
    """
    accent = accent_color or COLORS["accent_blue"]
    delta_color = ""
    delta_arrow = ""
    if delta is not None and delta_positive is not None:
        delta_color = COLORS["positive"] if delta_positive else COLORS["negative"]
        delta_arrow = "&#9650;" if delta_positive else "&#9660;"

    tooltip_attr = f'title="{tooltip}"' if tooltip else ""
    icon_html = f'<span style="font-size:1.15rem;margin-right:6px">{icon}</span>' if icon else ""

    delta_html = (
        f'<div style="margin-top:4px;font-size:0.75rem;color:{delta_color};font-weight:700">'
        f'{delta_arrow}&nbsp;{delta}</div>'
    ) if delta else ""
    c_sec = COLORS["text_secondary"]
    subtitle_html = (
        f'<div style="font-size:0.7rem;color:{c_sec};margin-top:2px">{subtitle}</div>'
    ) if subtitle else ""

    html = (
        f'<div {tooltip_attr} style="background:#0c1033;'
        f'border:1.5px solid rgba(255,255,255,0.22);border-left:4px solid {accent};border-radius:10px;'
        f'padding:12px 16px;box-shadow:0 4px 16px rgba(0,0,0,0.35);cursor:default;width:100%;'
        f'font-family:Inter,sans-serif;">'
        f'<div style="font-size:0.72rem;color:{c_sec};font-weight:700;'
        f'letter-spacing:0.07em;text-transform:uppercase;margin-bottom:4px">'
        f'{icon_html}{title}</div>'
        f'<div style="font-size:1.5rem;font-weight:800;color:#ffffff;line-height:1.1">{value}</div>'
        f'{delta_html}{subtitle_html}</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def kpi_row(cards: list[dict]) -> None:
    """Render a row of KPI cards from a list of dicts (args to kpi_card)."""
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            kpi_card(**card)


# ─── INSIGHT BLOCK ────────────────────────────────────────────────────────────

def insight_block(insights: list[str], title: str = "💡 Key Executive Insights & Recommendations") -> None:
    """Render auto-generated insight text in a styled partition card."""
    c_blue = COLORS["accent_blue"]
    c_pri = COLORS["text_primary"]
    items = "".join(f"<li style='margin-bottom:6px'>{i}</li>" for i in insights)
    html = (
        f'<div style="background:#0c1033;border:1.5px solid rgba(255,255,255,0.28);border-radius:12px;'
        f'padding:16px 22px;box-shadow:0 4px 18px rgba(0,0,0,0.35);font-family:Inter,sans-serif;">'
        f'<div style="font-size:0.88rem;font-weight:700;color:{c_blue};margin-bottom:8px;'
        f'letter-spacing:0.05em;text-transform:uppercase;">{title}</div>'
        f'<ul style="margin:0;padding-left:20px;color:{c_pri};font-size:0.84rem;line-height:1.7">'
        f'{items}</ul></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


import base64
from pathlib import Path

_LOGO_B64_CACHE = None

def _get_logo_b64() -> str:
    global _LOGO_B64_CACHE
    if _LOGO_B64_CACHE is None:
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                _LOGO_B64_CACHE = base64.b64encode(f.read()).decode("utf-8")
        else:
            _LOGO_B64_CACHE = ""
    return _LOGO_B64_CACHE


# ─── PAGE HEADER ──────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str | None = None) -> None:
    """Render a styled page title with brand logo in a top partition card starting with zero space."""
    c_sec = COLORS["text_secondary"]
    c_blue = COLORS["accent_blue"]
    sub_html = (
        f'<div style="margin-top:2px;font-size:0.82rem;color:{c_sec};line-height:1.3;">'
        f'{subtitle}</div>'
    ) if subtitle else ""
    logo_b64 = _get_logo_b64()
    logo_img_html = ""
    if logo_b64:
        logo_img_html = (
            f'<img src="data:image/png;base64,{logo_b64}" '
            f'style="width:44px;height:44px;border-radius:50%;border:1.5px solid {c_blue};'
            f'box-shadow:0 0 10px rgba(79,108,247,0.35);background:rgba(255,255,255,0.08);'
            f'padding:2px;flex-shrink:0;" />'
        )
    html = (
        f'<div style="background:#0c1033;border:1.5px solid rgba(255,255,255,0.28);border-radius:12px;'
        f'padding:10px 18px;margin:0 0 10px 0;display:flex;align-items:center;gap:14px;'
        f'box-shadow:0 4px 18px rgba(0,0,0,0.35);font-family:Inter,sans-serif;">'
        f'{logo_img_html}'
        f'<div style="flex-grow:1;">'
        f'<h1 style="margin:0;padding:0;font-size:1.5rem;font-weight:800;color:#ffffff;line-height:1.2;">{title}</h1>'
        f'{sub_html}'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─── SECTION HEADER ───────────────────────────────────────────────────────────

def section_header(title: str, section_num: str | None = None) -> None:
    """Render a visible, partitioned section header divider."""
    tag_html = f'<span class="section-tag">{section_num}</span>' if section_num else ""
    html = (
        f'<div class="section-header">'
        f'{tag_html}'
        f'<span class="section-title">{title}</span>'
        f'<div class="section-divider-line"></div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─── ACTIVE FILTER CHIP ───────────────────────────────────────────────────────

def active_filter_chip(label: str) -> None:
    """Show a small chip indicating an active cross-filter is applied."""
    c_blue = COLORS["accent_blue"]
    html = (
        f'<div style="display:inline-flex;align-items:center;gap:6px;'
        f'background:#0c1033;border:1.5px solid {c_blue};'
        f'border-radius:20px;padding:4px 12px;font-size:0.75rem;color:{c_blue};'
        f'font-weight:700;font-family:Inter,sans-serif;margin-bottom:8px;'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.3);">'
        f'&#128269; Filtered: <strong>{label}</strong></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─── EMPTY STATE ─────────────────────────────────────────────────────────────

def empty_state(message: str = "No data matches the current filters.") -> None:
    st.markdown(
        f'<div style="text-align:center;padding:60px 20px;color:{COLORS["text_secondary"]};font-size:1rem">'
        f'&#128270; {message}</div>',
        unsafe_allow_html=True,
    )


# ─── SECTION DIVIDER ─────────────────────────────────────────────────────────

def section_divider(label: str | None = None) -> None:
    if label:
        st.markdown(
            f'<div style="font-size:0.78rem;font-weight:700;color:{COLORS["accent_blue"]};'
            f'letter-spacing:0.1em;text-transform:uppercase;margin:16px 0 4px">{label}</div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<hr style="border:none;border-top:1px solid {COLORS["accent_blue"]}30;margin:4px 0 8px">',
        unsafe_allow_html=True,
    )


# ─── CHART HELPERS ────────────────────────────────────────────────────────────

def apply_layout(fig: go.Figure, title: str | None = None) -> go.Figure:
    """Apply the standard Power BI-matching layout to any Plotly figure."""
    layout = get_plotly_layout()
    if title:
        layout["title"] = dict(text=title, font=dict(color=COLORS["white"], size=13, family="Inter, sans-serif"))
    fig.update_layout(**layout)
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str | None = None,
    orientation: str = "h",
    color_map: dict | None = None,
    show_labels: bool = True,
) -> go.Figure:
    """Horizontal / vertical bar chart."""
    if color_map:
        colors = [color_map.get(v, COLORS["accent_blue"]) for v in df[x if orientation == "v" else y]]
    else:
        colors = color or COLORS["accent_blue"]

    if orientation == "h":
        trace = go.Bar(
            x=df[y], y=df[x], orientation="h",
            marker_color=colors,
            text=[f"{v:,.2f}" for v in df[y]] if show_labels else None,
            textposition="outside",
            textfont=dict(color=COLORS["text_secondary"], size=10),
            hovertemplate=f"<b>%{{y}}</b><br>{y}: %{{x:,.2f}}<extra></extra>",
        )
    else:
        trace = go.Bar(
            x=df[x], y=df[y], orientation="v",
            marker_color=colors,
            text=[f"{v:,.2f}" for v in df[y]] if show_labels else None,
            textposition="outside",
            textfont=dict(color=COLORS["text_secondary"], size=10),
            hovertemplate=f"<b>%{{x}}</b><br>{y}: %{{y:,.2f}}<extra></extra>",
        )

    fig = go.Figure(trace)
    apply_layout(fig, title)
    return fig


def line_area_chart(
    df: pd.DataFrame,
    x: str,
    ys: list[str],
    title: str = "",
    colors: list[str] | None = None,
    fill: bool = True,
) -> go.Figure:
    """Multi-series line/area chart."""
    fig = go.Figure()
    palette = colors or [COLORS["accent_blue"], COLORS["accent_cyan"], COLORS["accent_purple"]]

    for i, y in enumerate(ys):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[y],
            name=y,
            mode="lines",
            line=dict(color=palette[i % len(palette)], width=2.5),
            fill="tozeroy" if fill else "none",
            fillcolor=f"{palette[i % len(palette)]}18",
            hovertemplate=f"<b>%{{x}}</b><br>{y}: %{{y:,.0f}}<extra></extra>",
        ))

    apply_layout(fig, title)
    return fig


def donut_chart(
    labels: list[str],
    values: list[float],
    title: str = "",
    hole: float = 0.55,
    colors: list[str] | None = None,
) -> go.Figure:
    """Donut chart matching Power BI style."""
    palette = colors or list(CHANNEL_COLORS.values())
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=hole,
        marker=dict(colors=palette[:len(labels)], line=dict(color=COLORS["bg_primary"], width=2)),
        textinfo="label+percent",
        textfont=dict(color=COLORS["white"], size=11),
        hovertemplate="<b>%{label}</b><br>Value: %{value:,.0f}<br>Share: %{percent}<extra></extra>",
    ))
    apply_layout(fig, title)
    return fig
