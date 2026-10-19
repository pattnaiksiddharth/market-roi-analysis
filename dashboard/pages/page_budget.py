"""
Page 4: Budget Scenario
Replicates the Power BI Budget Scenario page exactly:

Layout (top → bottom):
  ROW 0: Page header (starts right at top with zero dead space)
  SECTION 1: Scenario Controls & Budget Allocation (Sliders & channel roles in card partition)
  SECTION 2: Projected Impact & Portfolio KPIs (6 KPI cards + ROI change badge)
  SECTION 3: Scenario Comparison & Channel Allocation (Scenario bar chart + Channel scenario table)
  SECTION 4: Budget Reallocation Flow & ROI Gauge (Waterfall chart + Gauge & detail breakdown)
  SECTION 5: Strategic Recommendations & Insights (Recommendation banner + Dynamic insights)
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_echarts import st_echarts

from components.charts import (
    apply_layout,
    fmt, fmt_compact, fmt_currency, fmt_pct,
    insight_block, kpi_row, page_header, empty_state, section_divider,
    section_header,
)
from utils.data_loader import apply_filters, apply_filters_no_channel, load_fact
from utils.measures import compute_measures, compute_scenario_measures
from utils.theme import CHANNEL_COLORS, COLORS, SCENARIOS


def show():
    # ── Load & filter ─────────────────────────────────────────────────────────
    df_raw = load_fact()
    f = st.session_state.get("filters", {})

    channels       = f.get("channels")
    date_start     = f.get("date_start")
    date_end       = f.get("date_end")
    campaign_types = f.get("campaign_types")
    locations      = f.get("locations")
    nc_share       = float(f.get("new_customer_share", 0.7))

    # For scenario measures we always use df_no_channel (REMOVEFILTERS(dim_channel))
    df_no_ch = apply_filters_no_channel(df_raw, date_start, date_end, campaign_types, locations)

    if df_no_ch.empty:
        empty_state()
        return

    # ── Page header (starts directly at top of canvas) ────────────────────────
    page_header(
        "BUDGET SCENARIO",
        "What-if analysis: reallocate budget from Cut channels to Scale channels",
    )

    # ── SECTION 1: Scenario Controls & Budget Allocation ──────────────────────
    section_header("Scenario Controls & Budget Allocation", "SECTION 1")

    with st.container(border=True):
        col_s1, col_s2, col_s3 = st.columns([1, 1, 1.8], gap="medium")
        with col_s1:
            budget_shift_pct = st.slider(
                "Budget Shift %",
                min_value=0.0, max_value=0.50, value=0.20, step=0.05,
                format="%.0f%%",
                key="budget_shift",
                help="Fraction of Cut-channel spend (YouTube + Facebook) to move to Scale channels.",
            )
            st.caption(f"→ Moving **{budget_shift_pct:.0%}** of Cut spend to Scale")

        with col_s2:
            efficiency_factor = st.slider(
                "Efficiency Factor",
                min_value=0.50, max_value=1.0, value=0.75, step=0.05,
                format="%.2f",
                key="efficiency_factor",
                help="Conversion efficiency on Scale channels vs Cut channels. 1.0 = full ROAS transfer.",
            )
            st.caption(f"→ Scale channels capture **{efficiency_factor:.0%}** of potential")

        with col_s3:
            c_card_alt = COLORS["bg_card_alt"]
            c_sec = COLORS["text_secondary"]
            c_cut = COLORS["negative"]
            c_scale = COLORS["positive"]
            c_hold = COLORS["neutral"]
            legend_html = (
                f'<div style="background:{c_card_alt};border:1.5px solid rgba(255,255,255,0.15);'
                f'border-radius:8px;padding:12px 14px;font-size:0.78rem;color:{c_sec};line-height:1.6">'
                f'<b style="color:{c_cut}">● Cut channels:</b> YouTube, Facebook (reduce budget)<br>'
                f'<b style="color:{c_scale}">● Scale channels:</b> Instagram, Google Ads (increase budget)<br>'
                f'<b style="color:{c_hold}">● Hold channels:</b> Email, Website (unchanged)<br>'
                f'<span style="font-size:0.7rem;color:{c_sec}">Default: 20% Shift · 0.75 Efficiency Factor</span>'
                f'</div>'
            )
            st.markdown(legend_html, unsafe_allow_html=True)

    # ── Compute scenario measures ──────────────────────────────────────────────
    sc = compute_scenario_measures(df_no_ch, budget_shift_pct, efficiency_factor, nc_share)

    # ── SECTION 2: Projected Impact & Portfolio KPIs ──────────────────────────
    section_header("Projected Impact & Portfolio KPIs", "SECTION 2")

    # ── KPI Row 1: Baseline Revenue · Projected Revenue · Revenue Change % ────
    kpi_row([
        {
            "title":   "Baseline Revenue",
            "value":   fmt_currency(sc["baseline_revenue"]),
            "tooltip": "Total Revenue with no changes (REMOVEFILTERS semantics)",
            "icon":    "📊",
            "accent_color": COLORS["accent_blue"],
        },
        {
            "title":   "Projected Revenue",
            "value":   fmt_currency(sc["projected_revenue"]),
            "tooltip": "Projected Revenue = Baseline Revenue − Revenue Lost + Revenue Gained",
            "icon":    "🚀",
            "accent_color": COLORS["positive"] if sc["revenue_change"] >= 0 else COLORS["negative"],
        },
        {
            "title":   "Revenue Change %",
            "value":   fmt_pct(sc["revenue_change_pct"]),
            "delta":   fmt_pct(abs(sc["revenue_change_pct"])),
            "delta_positive": sc["revenue_change"] >= 0,
            "tooltip": "Revenue Change % = (Projected − Baseline) / Baseline",
            "icon":    "📈" if sc["revenue_change"] >= 0 else "📉",
            "accent_color": COLORS["positive"] if sc["revenue_change"] >= 0 else COLORS["negative"],
        },
    ])

    # ── KPI Row 2: Revenue Change · Projected ROI · Baseline ROI ─────────────
    kpi_row([
        {
            "title":   "Revenue Change",
            "value":   fmt_currency(sc["revenue_change"]),
            "tooltip": "Revenue Change = Projected Revenue − Baseline Revenue",
            "icon":    "💹",
            "accent_color": COLORS["positive"] if sc["revenue_change"] >= 0 else COLORS["negative"],
        },
        {
            "title":   "Projected ROI",
            "value":   fmt_pct(sc["projected_roi"]),
            "tooltip": "Projected ROI = (Projected Revenue − Baseline Spend) / Baseline Spend",
            "icon":    "🎯",
            "accent_color": COLORS["positive"] if sc["projected_roi"] >= 0 else COLORS["negative"],
        },
        {
            "title":   "Baseline ROI",
            "value":   fmt_pct(sc["baseline_roi"]),
            "tooltip": "Baseline ROI = (Baseline Revenue − Baseline Spend) / Baseline Spend",
            "icon":    "📐",
            "accent_color": COLORS["accent_purple"],
        },
    ])

    # ROI Change in pp badge inside a container partition
    roi_pp = sc["roi_change_pp"]
    if not (isinstance(roi_pp, float) and math.isnan(roi_pp)):
        direction = "▲" if roi_pp >= 0 else "▼"
        badge_color = COLORS["positive"] if roi_pp >= 0 else COLORS["negative"]
        c_sec = COLORS["text_secondary"]
        b_roi = sc["baseline_roi"]
        p_roi = sc["projected_roi"]
        badge_html = (
            f'<div style="margin-top:6px;margin-bottom:8px;display:inline-flex;align-items:center;gap:8px;'
            f'background:#0c1033;border:1.5px solid {badge_color};border-radius:20px;'
            f'padding:6px 18px;font-size:0.82rem;font-weight:700;color:{badge_color};'
            f'box-shadow:0 2px 10px rgba(0,0,0,0.3)">'
            f'{direction} ROI Change: <b>{roi_pp:+.2f} pp</b> '
            f'<span style="font-weight:400;color:{c_sec}">'
            f'(from {b_roi:.2%} → {p_roi:.2%})</span></div>'
        )
        st.markdown(badge_html, unsafe_allow_html=True)

    # ── SECTION 3: Scenario Comparison & Channel Allocation ───────────────────
    section_header("Scenario Comparison & Channel Allocation", "SECTION 3")

    col_chart, col_tbl = st.columns([1.1, 0.9], gap="medium")

    with col_chart:
        with st.container(border=True):
            _render_scenario_bar(sc)

    with col_tbl:
        with st.container(border=True):
            _render_channel_scenario_table(sc, budget_shift_pct)

    # ── SECTION 4: Budget Reallocation Flow & Performance Gauge ───────────────
    section_header("Budget Reallocation Flow & Performance Gauge", "SECTION 4")

    with st.container(border=True):
        _render_waterfall(sc)

    col_gauge, col_detail = st.columns([1, 1.2], gap="medium")
    with col_gauge:
        with st.container(border=True):
            _render_roi_gauge(sc)

    with col_detail:
        with st.container(border=True):
            _render_moved_budget_detail(sc)

    # ── SECTION 5: Strategic Recommendations & Insights ───────────────────────
    section_header("Strategic Recommendations & Insights", "SECTION 5")

    _render_recommendation(sc, budget_shift_pct, efficiency_factor)
    insight_block(_generate_insights(sc, budget_shift_pct, efficiency_factor))


# ─── CHART RENDERERS ──────────────────────────────────────────────────────────

def _render_scenario_bar(sc: dict):
    """Bar chart: Revenue Change by Scenario (Conservative / Base / Optimistic)."""
    df = sc.get("scenario_df", pd.DataFrame())
    if df.empty:
        empty_state("No scenario data.")
        return

    colors = []
    for v in df["Revenue Change"]:
        colors.append(COLORS["positive"] if v >= 0 else COLORS["negative"])

    fig = go.Figure(go.Bar(
        x=df["Scenario"],
        y=df["Revenue Change"],
        marker_color=colors,
        text=[fmt_currency(v) for v in df["Revenue Change"]],
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"], size=11),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue Change: ₹%{y:,.0f}<br>"
            "<extra></extra>"
        ),
        width=0.5,
    ))
    fig.add_hline(y=0, line_color=COLORS["text_secondary"], line_width=1, line_dash="dot")
    apply_layout(fig, "Revenue Change by Scenario")
    fig.update_layout(height=280)
    st.plotly_chart(fig, width='stretch', key="budget_scenario_bar")

    # Scenario table below the bar
    df_show = df.copy()
    df_show["Revenue Change"] = df_show["Revenue Change"].apply(fmt_currency)
    df_show["Factor"] = df_show["Factor"].apply(lambda f: f"{f:.0%}")
    st.dataframe(df_show, width='stretch', hide_index=True)


def _render_channel_scenario_table(sc: dict, budget_shift_pct: float):
    """Table: channel, Total Spend, ROAS, Role, Scenario Spend — matching Power BI layout."""
    ch_df = sc.get("channel_scenario_df", pd.DataFrame())
    if ch_df.empty:
        empty_state("No channel data.")
        return

    # Ensure 'role' column always exists (guard against missing mapping)
    if "role" not in ch_df.columns:
        ch_df = ch_df.copy()
        ch_df["role"] = "Hold"
    if "roas" not in ch_df.columns:
        ch_df = ch_df.copy() if "role" in ch_df.columns else ch_df
        ch_df["roas"] = ch_df.apply(
            lambda r: r["revenue"] / r["spend"] if r["spend"] and r["spend"] != 0 else float("nan"),
            axis=1,
        )
    if "scenario_spend" not in ch_df.columns:
        ch_df = ch_df.copy()
        ch_df["scenario_spend"] = ch_df["spend"]

    tbl = ch_df[["channel", "spend", "roas", "role", "scenario_spend"]].copy()

    # Role colours
    role_colors = {"Cut": COLORS["negative"], "Scale": COLORS["positive"], "Hold": COLORS["neutral"]}

    tbl_display = pd.DataFrame()
    tbl_display["Channel"]        = tbl["channel"]
    tbl_display["Total Spend"]    = tbl["spend"].apply(lambda v: f"₹{v:,.0f}" if isinstance(v, (int, float)) and not math.isnan(v) else "–")
    tbl_display["ROAS"]           = tbl["roas"].apply(lambda v: f"{v:.2f}" if isinstance(v, (int, float)) and not math.isnan(v) else "–")
    tbl_display["Role"]           = tbl["role"].fillna("Hold")
    tbl_display["Scenario Spend"] = tbl["scenario_spend"].apply(lambda v: f"₹{v:,.0f}" if isinstance(v, (int, float)) and not math.isnan(v) else "–")

    def _color_role(val):
        c = role_colors.get(val, COLORS["neutral"])
        return f"color: {c}; font-weight: 700"

    styled = (
        tbl_display.style
        .map(_color_role, subset=["Role"])
        .set_properties(**{
            "background-color": COLORS["bg_card"],
            "color": COLORS["text_primary"],
            "border": f"1px solid {COLORS['accent_blue']}20",
            "font-size": "0.78rem",
        })
    )
    st.dataframe(styled, width='stretch', height=280, hide_index=True)

    # Add total row summary
    total_baseline = ch_df["spend"].sum()
    total_scenario = ch_df["scenario_spend"].sum()
    delta = total_scenario - total_baseline
    sign  = "+" if delta >= 0 else ""
    c_sec = COLORS["text_secondary"]
    c_white = COLORS["white"]
    c_cyan = COLORS["accent_cyan"]
    c_delta = COLORS["positive"] if delta >= 0 else COLORS["negative"]
    st.markdown(
        f'<div style="font-size:0.72rem;color:{c_sec};margin-top:6px">'
        f'Total baseline spend: <b style="color:{c_white}">{fmt_currency(total_baseline)}</b> '
        f'→ Scenario spend: <b style="color:{c_cyan}">{fmt_currency(total_scenario)}</b> '
        f'(<span style="color:{c_delta}">{sign}{fmt_currency(delta)}</span>)</div>',
        unsafe_allow_html=True,
    )

    # Download
    csv = tbl.to_csv(index=False)
    st.download_button(
        "⬇ Download Scenario CSV",
        data=csv,
        file_name="budget_scenario.csv",
        mime="text/csv",
        key="budget_download",
        width='stretch',
    )


def _render_waterfall(sc: dict):
    """Plotly waterfall: Baseline Revenue → −Revenue Lost → +Revenue Gained → Projected Revenue."""
    baseline  = sc["baseline_revenue"]
    lost      = -abs(sc["revenue_lost"])
    gained    = sc["revenue_gained"]
    projected = sc["projected_revenue"]

    fig = go.Figure(go.Waterfall(
        name="Budget Flow",
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Baseline Revenue", "Revenue Lost (Cut)", "Revenue Gained (Scale)", "Projected Revenue"],
        y=[baseline, lost, gained, projected],
        text=[
            fmt_currency(baseline),
            fmt_currency(lost),
            f"+{fmt_currency(gained)}",
            fmt_currency(projected),
        ],
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"], size=11),
        decreasing=dict(marker_color=COLORS["negative"]),
        increasing=dict(marker_color=COLORS["positive"]),
        totals=dict(marker_color=COLORS["accent_blue"]),
        connector=dict(line=dict(color=COLORS["accent_blue"] + "60", width=2, dash="dot")),
        hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
    ))
    apply_layout(fig, "Budget Reallocation Flow: Cut → Scale")
    fig.update_layout(height=290, showlegend=False)
    st.plotly_chart(fig, width='stretch', key="budget_waterfall")


def _render_roi_gauge(sc: dict):
    """ECharts half-gauge showing Projected ROI vs Baseline ROI."""
    proj_roi     = sc["projected_roi"] if not (isinstance(sc["projected_roi"], float) and math.isnan(sc["projected_roi"])) else 0
    baseline_roi = sc["baseline_roi"]  if not (isinstance(sc["baseline_roi"],  float) and math.isnan(sc["baseline_roi"]))  else 0
    proj_roi_text = f"{proj_roi:.1%}\nProjected ROI"

    gauge_option = {
        "backgroundColor": "transparent",
        "tooltip": {"formatter": "{a} <br/>{b} : {c}%"},
        "series": [
            {
                "name": "Baseline ROI",
                "type": "gauge",
                "startAngle": 180,
                "endAngle": 0,
                "min": -50,
                "max": 100,
                "radius": "75%",
                "center": ["50%", "70%"],
                "itemStyle": {"color": COLORS["accent_purple"] + "80"},
                "progress": {"show": True, "width": 14},
                "pointer": {"show": False},
                "axisLine": {"lineStyle": {"width": 14, "color": [[1, COLORS["bg_card_alt"]]]}},
                "axisTick": {"show": False},
                "splitLine": {"show": False},
                "axisLabel": {"show": False},
                "detail": {"show": False},
                "data": [{"value": round(baseline_roi * 100, 2), "name": "Baseline ROI"}],
            },
            {
                "name": "Projected ROI",
                "type": "gauge",
                "startAngle": 180,
                "endAngle": 0,
                "min": -50,
                "max": 100,
                "radius": "60%",
                "center": ["50%", "70%"],
                "itemStyle": {"color": COLORS["positive"] if proj_roi >= baseline_roi else COLORS["negative"]},
                "progress": {"show": True, "width": 14},
                "pointer": {"show": False},
                "axisLine": {"lineStyle": {"width": 14, "color": [[1, COLORS["bg_card_alt"]]]}},
                "axisTick": {"show": False},
                "splitLine": {"show": False},
                "axisLabel": {"show": False},
                "detail": {
                    "show": True,
                    "offsetCenter": [0, "0%"],
                    "formatter": proj_roi_text,
                    "color": COLORS["white"],
                    "fontSize": 16,
                    "fontWeight": "bold",
                },
                "data": [{"value": round(proj_roi * 100, 2), "name": "Projected ROI"}],
            },
        ],
    }
    st_echarts(options=gauge_option, height="260px", key="budget_roi_gauge")
    st.caption(
        f"Outer ring: Baseline ROI ({baseline_roi:.2%})  ·  "
        f"Inner ring: Projected ROI ({proj_roi:.2%})"
    )


def _render_moved_budget_detail(sc: dict):
    """Metric breakdown of the money movement."""
    moved  = sc["moved_budget"]
    lost   = sc["revenue_lost"]
    gained = sc["revenue_gained"]
    net    = gained - lost

    s_roas_str = f"{sc['source_roas']:.2f}x" if not (isinstance(sc['source_roas'], float) and math.isnan(sc['source_roas'])) else "–"
    t_roas_str = f"{sc['target_roas']:.2f}x" if not (isinstance(sc['target_roas'], float) and math.isnan(sc['target_roas'])) else "–"

    rows = [
        ("Moved Budget (from Cut channels)", fmt_currency(moved),    COLORS["accent_blue"]),
        ("Revenue Lost (Cut channels stop)", fmt_currency(-lost),     COLORS["negative"]),
        ("Revenue Gained (Scale channels)",  fmt_currency(gained),    COLORS["positive"]),
        ("Net Revenue Impact",               fmt_currency(net),
         COLORS["positive"] if net >= 0 else COLORS["negative"]),
        ("Source ROAS (Cut)",                s_roas_str,              COLORS["accent_purple"]),
        ("Target ROAS (Scale)",              t_roas_str,              COLORS["positive"]),
    ]

    c_border = COLORS["accent_blue"]
    c_sec = COLORS["text_secondary"]
    for label, val, color in rows:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:7px 12px;border-bottom:1px solid {c_border}20;'
            f'font-size:0.82rem">'
            f'<span style="color:{c_sec}">{label}</span>'
            f'<span style="color:{color};font-weight:700">{val}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_recommendation(sc: dict, shift_pct: float, eff_factor: float):
    """Auto-generate the recommendation box matching Power BI's text block."""
    moved  = sc["moved_budget"]
    net    = sc["revenue_change"]
    proj_r = sc["projected_roi"]
    base_r = sc["baseline_roi"]
    roi_pp = sc["roi_change_pp"]

    direction = "gains" if net >= 0 else "loses"
    arrow     = "▲" if net >= 0 else "▼"
    color     = COLORS["positive"] if net >= 0 else COLORS["negative"]
    c_card    = COLORS["bg_card"]
    c_grad    = COLORS["gradient_start"]
    c_pri     = COLORS["text_primary"]
    c_sec     = COLORS["text_secondary"]
    c_neg     = COLORS["negative"]
    c_pos     = COLORS["positive"]
    c_white   = COLORS["white"]

    # Conservative case from scenario_df
    sc_df = sc.get("scenario_df", pd.DataFrame())
    conservative_change = ""
    if not sc_df.empty:
        cons_row = sc_df[sc_df["Scenario"] == "Conservative"]
        if not cons_row.empty:
            c_val = cons_row.iloc[0]["Revenue Change"]
            c_word = "gains" if c_val >= 0 else "loses"
            conservative_change = f"Conservative case still {c_word} <b>{fmt_currency(abs(c_val))}</b>. "

    cut_names = "YouTube and Facebook"
    scale_names = "Instagram and Google Ads"
    moved_str = fmt_currency(moved)
    net_str = fmt_currency(abs(net))
    rev_chg_pct = fmt_pct(sc["revenue_change_pct"])
    base_r_pct = fmt_pct(base_r)
    proj_r_pct = fmt_pct(proj_r)
    roi_pp_str = f"{roi_pp:+.2f} pp"

    html = (
        f'<div style="background:linear-gradient(135deg, {c_card} 0%, {c_grad}44 100%);'
        f'border:2px solid {color}50;border-left:5px solid {color};border-radius:10px;'
        f'padding:18px 22px;margin:12px 0 16px;">'
        f'<div style="font-size:0.82rem;font-weight:800;color:{color};margin-bottom:10px;'
        f'letter-spacing:0.05em;text-transform:uppercase">💡 Strategic Recommendation</div>'
        f'<p style="margin:0 0 8px;color:{c_pri};font-size:0.9rem;line-height:1.7">'
        f'Shifting <b style="color:{c_white}">{shift_pct:.0%}</b> of '
        f'<b style="color:{c_neg}">{cut_names}</b> budget '
        f'(≈ <b style="color:{c_white}">{moved_str}</b>) to '
        f'<b style="color:{c_pos}">{scale_names}</b> at '
        f'<b style="color:{c_white}">{eff_factor:.0%}</b> efficiency {direction} '
        f'<b style="color:{color}">{arrow} {net_str}</b> '
        f'(<b>{rev_chg_pct}</b>). '
        f'ROI moves from <b>{base_r_pct}</b> → <b style="color:{color}">{proj_r_pct}</b> '
        f'(<b>{roi_pp_str}</b>). '
        f'{conservative_change}'
        f'Pilot with <b>10%</b> first and monitor marginal returns.</p></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─── INSIGHTS ─────────────────────────────────────────────────────────────────

def _generate_insights(sc: dict, shift_pct: float, eff_factor: float) -> list[str]:
    items = []

    items.append(
        f"Baseline portfolio: Revenue <b>{fmt_currency(sc['baseline_revenue'])}</b>, "
        f"ROI <b>{fmt_pct(sc['baseline_roi'])}</b>."
    )

    moved = sc["moved_budget"]
    items.append(
        f"Moving <b>{shift_pct:.0%}</b> of Cut-channel spend = "
        f"<b>{fmt_currency(moved)}</b> reallocated. "
        f"Revenue lost: <b>{fmt_currency(sc['revenue_lost'])}</b>, "
        f"Revenue gained: <b>{fmt_currency(sc['revenue_gained'])}</b>."
    )

    net = sc["revenue_change"]
    c_res = COLORS["positive"] if net >= 0 else COLORS["negative"]
    items.append(
        f"Net revenue impact: <b style='color:{c_res}'>"
        f"{fmt_currency(net)}</b> ({fmt_pct(sc['revenue_change_pct'])})."
    )

    sc_df = sc.get("scenario_df", pd.DataFrame())
    if not sc_df.empty:
        for _, row in sc_df.iterrows():
            items.append(
                f"<b>{row['Scenario']}</b> scenario (factor {row['Factor']:.0%}): "
                f"Revenue change = <b>{fmt_currency(row['Revenue Change'])}</b>."
            )

    items.append(
        f"Source ROAS (Cut channels): <b>{sc['source_roas']:.2f}x</b>  ·  "
        f"Target ROAS (Scale channels): <b>{sc['target_roas']:.2f}x</b>. "
        f"Higher target ROAS means each moved ₹ earns more on Scale channels."
    )

    return items
