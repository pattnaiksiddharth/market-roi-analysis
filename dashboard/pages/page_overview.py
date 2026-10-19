"""
Page 1: Executive Overview
Replicates the Power BI Overview page:
  - KPI row: CAC, ROI, Total Spend, Total Revenue (+ Profit, ROAS, Conversions, Profit Margin)
  - Horizontal grouped bar: Spend vs Revenue by channel
  - Diverging bar: ROI by channel (positive=green, negative=red)
  - Area line chart: Spend + Revenue over time
  - Donut: Conversions (and Revenue share) by channel
  - Auto-generated insights block
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.charts import (
    apply_layout, donut_chart, fmt, fmt_compact, fmt_currency,
    fmt_pct, insight_block, kpi_row, page_header, empty_state,
    section_divider, section_header, active_filter_chip, bar_chart,
)
from utils.data_loader import apply_filters, apply_filters_no_channel, load_fact
from utils.measures import (
    best_channel, compute_channel_measures, compute_measures,
    compute_timeseries, worst_channel,
)
from utils.theme import CHANNEL_COLORS, COLORS


def show():
    # ── Load & filter data ────────────────────────────────────────────────────
    df_raw = load_fact()
    f = st.session_state.get("filters", {})

    channels        = f.get("channels", sorted(df_raw["channel"].unique().tolist()))
    date_start      = f.get("date_start")
    date_end        = f.get("date_end")
    campaign_types  = f.get("campaign_types")
    locations       = f.get("locations")
    granularity     = f.get("granularity", "monthly")
    nc_share        = float(f.get("new_customer_share", 0.7))

    df_filtered  = apply_filters(df_raw, channels, date_start, date_end, campaign_types, locations)
    df_no_ch     = apply_filters_no_channel(df_raw, date_start, date_end, campaign_types, locations)

    if df_filtered.empty:
        empty_state("No data matches the current filters. Please adjust the sidebar.")
        return

    # ── Compute measures ──────────────────────────────────────────────────────
    m  = compute_measures(df_filtered, nc_share)
    ch = compute_channel_measures(df_filtered, df_no_ch, nc_share)
    ts = compute_timeseries(df_filtered, granularity)

    best_ch, best_roi   = best_channel(df_filtered)
    worst_ch, worst_roi = worst_channel(df_filtered)

    # ── Cross-filter state ────────────────────────────────────────────────────
    if "ov_selected_channel" not in st.session_state:
        st.session_state["ov_selected_channel"] = None

    sel_ch = st.session_state["ov_selected_channel"]
    if sel_ch:
        # Narrow down data for cross-filtered charts
        df_xf = df_filtered[df_filtered["channel"] == sel_ch]
        m_xf  = compute_measures(df_xf, nc_share)
        ts_xf = compute_timeseries(df_xf, granularity)
    else:
        df_xf, m_xf, ts_xf = df_filtered, m, ts

    # ── Page header (starts at the very top of the page) ──────────────────────
    page_header(
        "Marketing ROI: Executive Overview",
        f"Period: {date_start} → {date_end}  |  {len(channels)} channel(s)",
    )

    if sel_ch:
        col_chip, col_btn = st.columns([4, 1])
        with col_chip:
            active_filter_chip(f"Channel: {sel_ch}")
        with col_btn:
            if st.button("✕ Clear Filter", key="ov_clear_ch"):
                st.session_state["ov_selected_channel"] = None
                st.rerun()

    # ── SECTION 1: Key Performance Indicators ─────────────────────────────────
    section_header("Key Performance Indicators", "SECTION 1")

    # ── KPI Row 1 ─────────────────────────────────────────────────────────────
    kpi_row([
        {
            "title": "CAC",
            "value": fmt_currency(m_xf["cac"]),
            "tooltip": "Customer Acquisition Cost = Total Spend / New Customers",
            "icon": "🎯",
            "accent_color": COLORS["accent_purple"],
        },
        {
            "title": "ROI",
            "value": fmt_pct(m_xf["roi"]),
            "tooltip": "Return on Investment = (Revenue − Spend) / Spend",
            "icon": "📈",
            "delta": fmt_pct(m_xf["roi"]),
            "delta_positive": (m_xf["roi"] > 0),
            "accent_color": COLORS["positive"] if m_xf["roi"] >= 0 else COLORS["negative"],
        },
        {
            "title": "Total Spend",
            "value": fmt_currency(m_xf["total_spend"]),
            "tooltip": "Total marketing spend across all channels",
            "icon": "💸",
        },
        {
            "title": "Total Revenue",
            "value": fmt_currency(m_xf["total_revenue"]),
            "tooltip": "Total gross revenue from all campaigns",
            "icon": "💰",
            "accent_color": COLORS["positive"],
        },
    ])

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── KPI Row 2 ─────────────────────────────────────────────────────────────
    kpi_row([
        {
            "title": "Profit",
            "value": fmt_currency(m_xf["profit"]),
            "tooltip": "Total Profit = Revenue − Spend",
            "icon": "✅" if m_xf["profit"] >= 0 else "🔴",
            "accent_color": COLORS["positive"] if m_xf["profit"] >= 0 else COLORS["negative"],
        },
        {
            "title": "ROAS",
            "value": fmt(m_xf["roas"], "number", suffix="x") if not np.isnan(m_xf["roas"]) else "–",
            "tooltip": "Return on Ad Spend = Revenue / Spend",
            "icon": "📊",
        },
        {
            "title": "Total Conversions",
            "value": fmt_compact(m_xf["total_conversions"]),
            "tooltip": "Total number of conversion events",
            "icon": "🔁",
            "accent_color": COLORS["accent_cyan"],
        },
        {
            "title": "Profit Margin",
            "value": fmt_pct(m_xf["profit_margin"]),
            "tooltip": "Profit Margin = Profit / Revenue",
            "icon": "📉" if m_xf["profit_margin"] < 0 else "📈",
            "accent_color": COLORS["positive"] if m_xf["profit_margin"] >= 0 else COLORS["negative"],
        },
    ])

    # ── SECTION 2: Channel Acquisition & ROI Analysis ─────────────────────────
    section_header("Channel Spend, Revenue & ROI Analysis", "SECTION 2")

    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        with st.container(border=True):
            # Grouped bar: Total Spend and Total Revenue by channel (horizontal)
            fig_grouped = go.Figure()
            ch_sorted = ch.sort_values("spend", ascending=True)
            fig_grouped.add_trace(go.Bar(
                y=ch_sorted["channel"], x=ch_sorted["spend"],
                name="Total Spend",
                orientation="h",
                marker_color=COLORS["accent_blue"],
                hovertemplate="<b>%{y}</b><br>Spend: ₹%{x:,.0f}<extra></extra>",
            ))
            fig_grouped.add_trace(go.Bar(
                y=ch_sorted["channel"], x=ch_sorted["revenue"],
                name="Total Revenue",
                orientation="h",
                marker_color=COLORS["accent_cyan"],
                hovertemplate="<b>%{y}</b><br>Revenue: ₹%{x:,.0f}<extra></extra>",
            ))
            apply_layout(fig_grouped, "Total Spend and Total Revenue by channel")
            fig_grouped.update_layout(height=340, barmode="group", legend=dict(orientation="h", y=-0.22))

            event_grouped = st.plotly_chart(
                fig_grouped, width='stretch', key="ov_grouped_bar",
                on_select="rerun", selection_mode="points",
            )
            if event_grouped and event_grouped.selection and event_grouped.selection.get("points"):
                clicked = event_grouped.selection["points"][0].get("label") or \
                          event_grouped.selection["points"][0].get("y")
                if clicked and clicked in ch["channel"].values:
                    st.session_state["ov_selected_channel"] = clicked
                    st.rerun()

    with col_right:
        with st.container(border=True):
            # Diverging ROI bar by channel
            ch_roi = ch.sort_values("roi", ascending=True)
            bar_colors = [
                COLORS["positive"] if r >= 0 else COLORS["negative"]
                for r in ch_roi["roi"]
            ]
            fig_roi = go.Figure(go.Bar(
                x=ch_roi["roi"],
                y=ch_roi["channel"],
                orientation="h",
                marker_color=bar_colors,
                text=[f"{r:.2f}" for r in ch_roi["roi"]],
                textposition="outside",
                textfont=dict(color=COLORS["text_secondary"], size=10),
                hovertemplate="<b>%{y}</b><br>ROI: %{x:.2%}<extra></extra>",
            ))
            # Zero line
            fig_roi.add_vline(x=0, line_color=COLORS["text_secondary"], line_width=1)
            worst_roi_str = f"loses {abs(worst_roi):.0%}" if worst_roi < 0 else f"returns {worst_roi:.0%}"
            apply_layout(fig_roi, f"{best_ch} returns {best_roi:.0%} ROI, {worst_ch} {worst_roi_str}")
            fig_roi.update_layout(height=340)
            st.plotly_chart(fig_roi, width='stretch', key="ov_roi_bar")

    # ── SECTION 3: Revenue Trends & Conversion Distribution ───────────────────
    section_header("Portfolio Trends & Conversion Share", "SECTION 3")

    col_bottom_l, col_bottom_r = st.columns([1.1, 0.9], gap="medium")

    with col_bottom_l:
        with st.container(border=True):
            # Area chart: Spend & Revenue over time
            ts_data = ts_xf
            if not ts_data.empty:
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=ts_data["period"], y=ts_data["spend"],
                    name="Total Spend",
                    mode="lines",
                    line=dict(color=COLORS["accent_blue"], width=2.5),
                    fill="tozeroy",
                    fillcolor=f"{COLORS['accent_blue']}22",
                    hovertemplate="<b>%{x}</b><br>Spend: ₹%{y:,.0f}<extra></extra>",
                ))
                fig_trend.add_trace(go.Scatter(
                    x=ts_data["period"], y=ts_data["revenue"],
                    name="Total Revenue",
                    mode="lines",
                    line=dict(color=COLORS["accent_cyan"], width=2.5),
                    fill="tozeroy",
                    fillcolor=f"{COLORS['accent_cyan']}22",
                    hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.0f}<extra></extra>",
                ))
                # Deficit alert markers where spend > revenue
                loss_periods = ts_data[ts_data["spend"] > ts_data["revenue"]]
                if not loss_periods.empty:
                    fig_trend.add_trace(go.Scatter(
                        x=loss_periods["period"],
                        y=loss_periods["spend"],
                        mode="markers",
                        name="Deficit (Spend > Rev)",
                        marker=dict(color=COLORS["negative"], size=8, symbol="triangle-up"),
                        hovertemplate="<b>%{x}</b><br>Deficit Alert: Spend exceeds Revenue<extra></extra>",
                    ))
                apply_layout(fig_trend, f"Total Spend and Total Revenue by {granularity} period")
                fig_trend.update_layout(height=340, legend=dict(orientation="h", y=-0.22))
                st.plotly_chart(fig_trend, width='stretch', key="ov_trend")
            else:
                empty_state("No time-series data for selected filters.")

    with col_bottom_r:
        with st.container(border=True):
            # Donut: Total Conversions by channel
            ch_sorted_conv = ch.sort_values("conversions", ascending=False)
            fig_donut = go.Figure(go.Pie(
                labels=ch_sorted_conv["channel"].tolist(),
                values=ch_sorted_conv["conversions"].tolist(),
                hole=0.55,
                marker=dict(
                    colors=[CHANNEL_COLORS.get(c, COLORS["accent_blue"]) for c in ch_sorted_conv["channel"]],
                    line=dict(color=COLORS["bg_card"], width=2),
                ),
                textinfo="label+percent",
                textfont=dict(color=COLORS["white"], size=10),
                hovertemplate="<b>%{label}</b><br>Conversions: %{value:,.0f}<br>Share: %{percent}<extra></extra>",
            ))
            # Center annotation
            total_conv_compact = fmt_compact(m_xf["total_conversions"])
            fig_donut.add_annotation(
                text=f"<b>{total_conv_compact}</b>",
                x=0.5, y=0.5, font=dict(color=COLORS["white"], size=18, family="Inter"),
                showarrow=False,
            )
            apply_layout(fig_donut, "Total Conversions and Revenue by channel")
            fig_donut.update_layout(height=340, legend=dict(orientation="h", y=-0.22))
            st.plotly_chart(fig_donut, width='stretch', key="ov_donut")

    # ── SECTION 4: Strategic Recommendations & Insights ───────────────────────
    section_header("Strategic Recommendations & Insights", "SECTION 4")

    insights = _generate_insights(m_xf, ch, best_ch, best_roi, worst_ch, worst_roi)
    insight_block(insights)


def _generate_insights(m, ch, best_ch, best_roi, worst_ch, worst_roi) -> list[str]:
    """Auto-generate bullet-point insights from the computed measures."""
    items = []

    # Profit status
    status = "profitable" if m["profit"] >= 0 else "loss-making"
    items.append(
        f"Overall portfolio is <b>{status}</b> with a profit of "
        f"<b>{fmt_currency(m['profit'])}</b> "
        f"({fmt_pct(m['profit_margin'])} margin)."
    )

    # ROI
    items.append(
        f"Portfolio ROI is <b>{fmt_pct(m['roi'])}</b> — "
        f"every ₹1 spent returns ₹{m['roas']:.2f} in revenue (ROAS)."
    )

    # Best / worst channel
    items.append(
        f"<b>{best_ch}</b> is the best-performing channel (ROI: {fmt_pct(best_roi)}). "
        f"<b>{worst_ch}</b> is the worst (ROI: {fmt_pct(worst_roi)})."
    )

    # Loss-making channels
    loss_ch = ch[ch["profit"] < 0]["channel"].tolist()
    if loss_ch:
        items.append(
            f"Loss-making channels: <b>{', '.join(loss_ch)}</b>. "
            f"Consider reducing their budget or optimising campaigns."
        )

    # CAC
    items.append(
        f"Customer Acquisition Cost: <b>{fmt_currency(m['cac'])}</b> per new customer. "
        f"Revenue per conversion: <b>{fmt_currency(m['rev_per_conversion'])}</b>."
    )

    # Spend vs Revenue gap
    gap = m["total_revenue"] - m["total_spend"]
    items.append(
        f"Revenue exceeds spend by <b>{fmt_currency(abs(gap))}</b> "
        f"({'surplus' if gap >= 0 else 'deficit'})."
    )

    return items
