"""
Page 2: Funnel & Acquisition
Replicates the Campaign Analysis page from Power BI, adapted as Funnel & Acquisition:
  - ECharts funnel: Impressions → Clicks → Conversions
  - KPI row: CTR, CVR, CPC, CPA, CAC, Revenue per Conversion
  - Bar: ROI by campaign_type
  - Pie: Profit Margin by channel
  - AgGrid cross-tab: channel × campaign_type ROI pivot
  - Scatter: Count of spend vs ROI
  - Auto-generated insights
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_echarts import st_echarts

from components.charts import (
    apply_layout, fmt, fmt_compact, fmt_currency, fmt_pct,
    insight_block, kpi_row, page_header, empty_state, section_divider,
    section_header,
)
from utils.data_loader import apply_filters, apply_filters_no_channel, load_fact
from utils.measures import (
    compute_measures, compute_channel_measures,
    compute_campaign_type_measures, compute_channel_campaign_pivot,
)
from utils.theme import CHANNEL_COLORS, COLORS, CHART_COLORS


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

    df_filtered = apply_filters(df_raw, channels, date_start, date_end, campaign_types, locations)
    df_no_ch    = apply_filters_no_channel(df_raw, date_start, date_end, campaign_types, locations)

    if df_filtered.empty:
        empty_state()
        return

    m  = compute_measures(df_filtered, nc_share)
    ch = compute_channel_measures(df_filtered, df_no_ch, nc_share)
    ct = compute_campaign_type_measures(df_filtered)
    pv = compute_channel_campaign_pivot(df_filtered)

    # ── Page header ───────────────────────────────────────────────────────────
    page_header(
        "Funnel & Acquisition",
        "Impressions → Clicks → Conversions · Channel acquisition efficiency",
    )

    # ── SECTION 1: Acquisition & Conversion Metrics ───────────────────────────
    section_header("Acquisition & Conversion Metrics", "SECTION 1")

    # ── KPI Row: funnel metrics ────────────────────────────────────────────────
    kpi_row([
        {
            "title": "CTR",
            "value": fmt_pct(m["ctr"]),
            "tooltip": "Click-Through Rate = Clicks / Impressions",
            "icon": "👆",
            "accent_color": COLORS["accent_cyan"],
        },
        {
            "title": "CVR",
            "value": fmt_pct(m["cvr"]),
            "tooltip": "Conversion Rate = Conversions / Clicks",
            "icon": "🔄",
            "accent_color": COLORS["accent_purple"],
        },
        {
            "title": "CPC",
            "value": fmt_currency(m["cpc"]),
            "tooltip": "Cost Per Click = Spend / Clicks",
            "icon": "🖱️",
        },
        {
            "title": "CPA",
            "value": fmt_currency(m["cpa"]),
            "tooltip": "Cost Per Acquisition = Spend / Conversions",
            "icon": "🎯",
        },
        {
            "title": "CAC",
            "value": fmt_currency(m["cac"]),
            "tooltip": f"Customer Acquisition Cost = Spend / (Conversions × {nc_share:.0%})",
            "icon": "👤",
            "accent_color": COLORS["accent_blue"],
        },
        {
            "title": "Rev / Conversion",
            "value": fmt_currency(m["rev_per_conversion"]),
            "tooltip": "Revenue per Conversion = Revenue / Conversions",
            "icon": "💎",
            "accent_color": COLORS["positive"],
        },
    ])

    # ── SECTION 2: Funnel Flow & Campaign ROI ─────────────────────────────────
    section_header("Funnel Flow & Campaign ROI", "SECTION 2")

    col_funnel, col_roi_ct = st.columns([1, 1], gap="medium")

    with col_funnel:
        with st.container(border=True):
            imp = int(m["total_impressions"])
            clk = int(m["total_clicks"])
            conv = int(m["total_conversions"])

            funnel_option = {
                "backgroundColor": "transparent",
                "tooltip": {"trigger": "item", "formatter": "{b}: {c:,}"},
                "series": [
                    {
                        "name": "Acquisition Funnel",
                        "type": "funnel",
                        "left": "10%",
                        "width": "80%",
                        "label": {
                            "show": True,
                            "position": "inside",
                            "color": "#ffffff",
                            "fontSize": 12,
                            "fontWeight": "bold",
                            "formatter": "{b}\n{c}",
                        },
                        "labelLine": {"show": False},
                        "itemStyle": {"borderColor": "#0c1033", "borderWidth": 2},
                        "emphasis": {"label": {"fontSize": 14}},
                        "data": [
                            {"value": imp,  "name": "Impressions", "itemStyle": {"color": COLORS["accent_blue"]}},
                            {"value": clk,  "name": "Clicks",      "itemStyle": {"color": COLORS["accent_purple"]}},
                            {"value": conv, "name": "Conversions", "itemStyle": {"color": COLORS["positive"]}},
                        ],
                    }
                ],
            }
            st_echarts(options=funnel_option, height="260px", key="funnel_chart")

            # Drop-off rates
            ctr_pct = m["ctr"] * 100 if not np.isnan(m["ctr"]) else 0
            cvr_pct = m["cvr"] * 100 if not np.isnan(m["cvr"]) else 0
            col_a, col_b = st.columns(2)
            c_card = COLORS["bg_card"]
            c_sec = COLORS["text_secondary"]
            c_cyan = COLORS["accent_cyan"]
            c_pos = COLORS["positive"]
            col_a.markdown(
                f'<div style="text-align:center;padding:10px;background:#090d2a;border:1.5px solid rgba(255,255,255,0.18);border-radius:8px">'
                f'<div style="font-size:0.7rem;color:{c_sec};font-weight:700;text-transform:uppercase">Click-Through Rate</div>'
                f'<div style="font-size:1.25rem;font-weight:800;color:{c_cyan}">{ctr_pct:.2f}%</div>'
                f'</div>', unsafe_allow_html=True,
            )
            col_b.markdown(
                f'<div style="text-align:center;padding:10px;background:#090d2a;border:1.5px solid rgba(255,255,255,0.18);border-radius:8px">'
                f'<div style="font-size:0.7rem;color:{c_sec};font-weight:700;text-transform:uppercase">Conversion Rate</div>'
                f'<div style="font-size:1.25rem;font-weight:800;color:{c_pos}">{cvr_pct:.2f}%</div>'
                f'</div>', unsafe_allow_html=True,
            )

    with col_roi_ct:
        with st.container(border=True):
            if not ct.empty:
                ct_sorted = ct.sort_values("roi")
                bar_colors = [
                    COLORS["positive"] if r >= 0 else COLORS["negative"]
                    for r in ct_sorted["roi"]
                ]
                fig_ct = go.Figure(go.Bar(
                    x=ct_sorted["roi"],
                    y=ct_sorted["campaign_type"],
                    orientation="h",
                    marker_color=bar_colors,
                    text=[f"{r:.2f}" for r in ct_sorted["roi"]],
                    textposition="outside",
                    textfont=dict(color=COLORS["text_secondary"], size=10),
                    hovertemplate="<b>%{y}</b><br>ROI: %{x:.2%}<extra></extra>",
                ))
                fig_ct.add_vline(x=0, line_color=COLORS["text_secondary"], line_width=1)
                apply_layout(fig_ct, "ROI by campaign_type")
                fig_ct.update_layout(height=340)
                st.plotly_chart(fig_ct, width='stretch', key="funnel_roi_ct")

    # ── SECTION 3: Channel Margins & Cross-Tab Analysis ───────────────────────
    section_header("Channel Margins & Cross-Tab Analysis", "SECTION 3")

    col_pie, col_pivot = st.columns([0.9, 1.1], gap="medium")

    with col_pie:
        with st.container(border=True):
            ch_profit = ch[ch["profit_margin"].notna()].copy()
            ch_profit["abs_margin"] = ch_profit["profit_margin"].abs()
            pie_colors = [CHANNEL_COLORS.get(c, COLORS["accent_blue"]) for c in ch_profit["channel"]]

            fig_pie = go.Figure(go.Pie(
                labels=ch_profit["channel"].tolist(),
                values=ch_profit["abs_margin"].tolist(),
                marker=dict(colors=pie_colors, line=dict(color=COLORS["bg_card"], width=2)),
                textinfo="label+percent",
                textfont=dict(color=COLORS["white"], size=10),
                hovertemplate=(
                    "<b>%{label}</b><br>Margin: %{customdata:.2%}<extra></extra>"
                ),
                customdata=ch_profit["profit_margin"].tolist(),
            ))
            apply_layout(fig_pie, "Profit Margin by channel")
            fig_pie.update_layout(height=340, legend=dict(orientation="h", y=-0.22))
            st.plotly_chart(fig_pie, width='stretch', key="funnel_pie")

    with col_pivot:
        with st.container(border=True):
            if not pv.empty:
                # Style the pivot table
                type_cols = [c for c in pv.columns if c not in ["channel", "Total"]]
                display_cols = ["channel"] + type_cols + ["Total"]
                pv_display = pv[display_cols].copy()

                def _colour_roi(v):
                    if isinstance(v, (int, float)) and not np.isnan(v):
                        c = COLORS["positive"] if v >= 0 else COLORS["negative"]
                        return f"color: {c}; font-weight: 600"
                    return ""

                styled = (
                    pv_display.style
                    .map(_colour_roi, subset=type_cols + ["Total"])
                    .format({c: "{:.2f}" for c in type_cols + ["Total"]}, na_rep="–")
                    .set_properties(**{
                        "background-color": COLORS["bg_card"],
                        "color": COLORS["text_primary"],
                        "border": f"1px solid {COLORS['accent_blue']}30",
                        "font-size": "0.8rem",
                    })
                )
                st.dataframe(styled, width='stretch', height=340, hide_index=True)

    # ── SECTION 4: Spend vs ROI Portfolio Distribution ────────────────────────
    section_header("Spend vs ROI Portfolio Distribution", "SECTION 4")

    with st.container(border=True):
        fig_scatter = go.Figure()
        max_conv = max(ch["conversions"]) if (not ch.empty and max(ch["conversions"]) > 0) else 1
        for _, row in ch.iterrows():
            fig_scatter.add_trace(go.Scatter(
                x=[row["spend"]],
                y=[row["roi"]],
                mode="markers+text",
                name=row["channel"],
                text=[row["channel"]],
                textposition="top center",
                textfont=dict(size=10, color=COLORS["text_secondary"]),
                marker=dict(
                    size=max(10, row["conversions"] / max_conv * 60),
                    color=CHANNEL_COLORS.get(row["channel"], COLORS["accent_blue"]),
                    opacity=0.85,
                    line=dict(color=COLORS["white"], width=1.5),
                ),
                hovertemplate=(
                    f"<b>{row['channel']}</b><br>"
                    f"Spend: ₹{row['spend']:,.0f}<br>"
                    f"ROI: {row['roi']:.2%}<br>"
                    f"Conversions: {row['conversions']:,.0f}<extra></extra>"
                ),
            ))

        fig_scatter.add_hline(y=0, line_color=COLORS["negative"], line_dash="dot", line_width=1,
                              annotation_text="Break-even", annotation_font_color=COLORS["negative"])
        apply_layout(fig_scatter, "Count of Spend and ROI (bubble size = conversions)")
        fig_scatter.update_layout(showlegend=False, height=320)
        st.plotly_chart(fig_scatter, width='stretch', key="funnel_scatter")

    # ── SECTION 5: Strategic Recommendations & Insights ───────────────────────
    section_header("Strategic Recommendations & Insights", "SECTION 5")

    insights = _generate_insights(m, ch, ct)
    insight_block(insights)


def _generate_insights(m, ch, ct) -> list[str]:
    items = []

    # Funnel drop-off
    ctr = m["ctr"] * 100 if not np.isnan(m["ctr"]) else 0
    cvr = m["cvr"] * 100 if not np.isnan(m["cvr"]) else 0
    items.append(
        f"Funnel: <b>{fmt_compact(m['total_impressions'])}</b> impressions → "
        f"<b>{fmt_compact(m['total_clicks'])}</b> clicks (CTR {ctr:.2f}%) → "
        f"<b>{fmt_compact(m['total_conversions'])}</b> conversions (CVR {cvr:.2f}%)."
    )

    # CAC vs Rev/conv
    items.append(
        f"Each new customer costs <b>{fmt_currency(m['cac'])}</b> to acquire (CAC), "
        f"but generates <b>{fmt_currency(m['rev_per_conversion'])}</b> per conversion."
    )

    # Best campaign type
    if not ct.empty and "roi" in ct.columns and ct["roi"].notna().any():
        best_ct = ct.loc[ct["roi"].idxmax(), "campaign_type"]
        best_ct_roi = ct["roi"].max()
        items.append(
            f"Best campaign type by ROI: <b>{best_ct}</b> ({fmt_pct(best_ct_roi)}). "
            f"Focus budget here for higher returns."
        )

    # Profit margin outliers
    pm_valid = ch["profit_margin"].dropna() if (not ch.empty and "profit_margin" in ch.columns) else pd.Series()
    if not pm_valid.empty:
        worst_margin_ch = ch.loc[ch["profit_margin"].idxmin(), "channel"]
        best_margin_ch  = ch.loc[ch["profit_margin"].idxmax(), "channel"]
        items.append(
            f"Best margin channel: <b>{best_margin_ch}</b>. "
            f"Worst margin channel: <b>{worst_margin_ch}</b>."
        )

    items.append(
        f"CPC is <b>{fmt_currency(m['cpc'])}</b> and CPA is <b>{fmt_currency(m['cpa'])}</b>. "
        f"Reducing CPC by 10% could add ~{fmt_currency(m['total_clicks'] * m['cpc'] * 0.1)} in savings."
    )

    return items
