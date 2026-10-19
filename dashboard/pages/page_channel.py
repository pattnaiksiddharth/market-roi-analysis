"""
Page 3: Channel Performance
Replicates the Power BI Channel Performance page exactly:

Layout (top → bottom):
  ROW 0: page header with Best Channel / Worst Channel / Revenue per Conversion KPI cards
  ROW 1: Parameter-driven horizontal bar (metric selector: CAC | Rev/Conv | ROAS | ROI | Profit)
          + AgGrid table (channel × Spend, Revenue, ROI, CAC, ROAS, Conversions) + Total row
  ROW 2: % of Spend & % of Revenue side-by-side donut/bar
          + Revenue per Conversion by channel bar

Extra beyond brief:
  - Top-N slider to limit visible channels
  - Sort toggle (ascending / descending)
  - Compare channels multi-select that cross-highlights
  - Loss Making badge per channel row
  - CSV download of the channel table
  - Sparkline mini-charts inside the AgGrid are approximated with conditional formatting
  - Detailed hover tooltips on every chart
"""

from __future__ import annotations

import io
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

from components.charts import (
    apply_layout,
    fmt, fmt_compact, fmt_currency, fmt_pct,
    insight_block, kpi_row, page_header, empty_state, section_divider,
    section_header, active_filter_chip,
)
from utils.data_loader import apply_filters, apply_filters_no_channel, load_fact
from utils.measures import (
    best_channel, compute_channel_measures, compute_measures, worst_channel,
)
from utils.theme import CHANNEL_COLORS, COLORS


# ─── METRIC OPTIONS ───────────────────────────────────────────────────────────
_METRIC_OPTIONS = {
    "ROI":                   ("roi",                "ROI",                  ",.2%",  False),
    "ROAS":                  ("roas",               "ROAS (x)",             ",.2f",  False),
    "Profit":                ("profit",             "Profit (₹)",           ",.0f",  True),
    "% of Spend":            ("spend_share",        "% of Spend",           ",.2%",  False),
    "CAC":                   ("cac",                "CAC (₹)",              ",.2f",  True),
    "Revenue per Conversion":("rev_per_conversion", "Rev / Conversion (₹)", ",.2f",  True),
}


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

    best_ch,  best_roi  = best_channel(df_filtered)
    worst_ch, worst_roi = worst_channel(df_filtered)

    # ── Page header (starts right at top of page) ─────────────────────────────
    page_header(
        "Channel Performance:",
        f"Best: {best_ch}  ·  Worst: {worst_ch}  ·  Period: {date_start} → {date_end}",
    )

    # ── Cross-filter state ────────────────────────────────────────────────────
    if "ch_selected" not in st.session_state:
        st.session_state["ch_selected"] = None
    sel = st.session_state["ch_selected"]
    if sel:
        col_chip, col_btn = st.columns([4, 1])
        with col_chip:
            active_filter_chip(f"Channel: {sel}")
        with col_btn:
            if st.button("✕ Clear filter", key="ch_clear"):
                st.session_state["ch_selected"] = None
                st.rerun()

    # ── SECTION 1: Channel Performance Highlights ─────────────────────────────
    section_header("Channel Performance Highlights", "SECTION 1")

    # ── Top KPI row: Best Channel / Worst Channel / Revenue per Conversion ────
    kpi_row([
        {
            "title":        "Best Channel",
            "value":        best_ch,
            "delta":        fmt_pct(best_roi),
            "delta_positive": True,
            "tooltip":      f"Highest ROI channel: {best_ch} at {best_roi:.2%}",
            "icon":         "🏆",
            "accent_color": COLORS["positive"],
            "height":       110,
        },
        {
            "title":        "Worst Channel",
            "value":        worst_ch,
            "delta":        fmt_pct(worst_roi),
            "delta_positive": False,
            "tooltip":      f"Lowest ROI channel: {worst_ch} at {worst_roi:.2%}",
            "icon":         "⚠️",
            "accent_color": COLORS["negative"],
            "height":       110,
        },
        {
            "title":        "Revenue per Conversion",
            "value":        fmt_currency(m["rev_per_conversion"]),
            "tooltip":      "Revenue per Conversion = Total Revenue / Total Conversions",
            "icon":         "💎",
            "accent_color": COLORS["accent_cyan"],
            "height":       110,
        },
    ])

    # ── SECTION 2: Interactive Parameter Analysis & Channel Summary ───────────
    section_header("Interactive Parameter Analysis & Channel Summary", "SECTION 2")

    # ── Controls container partition ──────────────────────────────────────────
    with st.container(border=True):
        ctrl1, ctrl2, ctrl3 = st.columns([2, 1.5, 1.5])
        with ctrl1:
            metric_label = st.selectbox(
                "📊 Parameter (chart metric)",
                options=list(_METRIC_OPTIONS.keys()),
                index=0,  # default: ROI
                key="ch_metric",
            )
        with ctrl2:
            top_n = st.slider("Top N channels", min_value=2, max_value=len(ch), value=len(ch), step=1, key="ch_topn")
        with ctrl3:
            sort_asc = st.toggle("Sort ascending", value=False, key="ch_sort_asc")

    metric_col, metric_label_fmt, metric_fmt, is_currency = _METRIC_OPTIONS[metric_label]

    # Prepare / sort channel data
    ch_display = ch.copy()
    ch_display = ch_display.sort_values(metric_col, ascending=sort_asc).head(top_n)

    # ── Charts Row 1: Parameter bar + AgGrid table ─────────────────────────────
    col_bar, col_table = st.columns([1, 1.2], gap="medium")

    with col_bar:
        with st.container(border=True):
            _render_parameter_bar(ch_display, metric_col, metric_label, metric_label_fmt, metric_fmt, sel)

    with col_table:
        with st.container(border=True):
            _render_aggrid(ch, m, nc_share)

    # ── SECTION 3: Revenue Share & Conversion Efficiency ───────────────────────
    section_header("Revenue Share & Conversion Efficiency", "SECTION 3")

    col_share, col_rev = st.columns([1, 1], gap="medium")

    with col_share:
        with st.container(border=True):
            _render_share_chart(ch_display)

    with col_rev:
        with st.container(border=True):
            _render_rev_per_conv_bar(ch_display, sel)

    # ── SECTION 4: Channel Profitability Breakdown ─────────────────────────────
    section_header("Channel Profitability Breakdown", "SECTION 4")

    with st.container(border=True):
        _render_profit_bar(ch, sel)

    # ── SECTION 5: Strategic Recommendations & Insights ───────────────────────
    section_header("Strategic Recommendations & Insights", "SECTION 5")

    insight_block(_generate_insights(m, ch, best_ch, best_roi, worst_ch, worst_roi))


# ─── CHART RENDERERS ──────────────────────────────────────────────────────────

def _render_parameter_bar(ch_display, metric_col, metric_label, metric_label_fmt, metric_fmt, sel):
    """Horizontal bar for the selected parameter metric matching Power BI slicer behavior."""
    col_colors = []
    text_labels = []
    for _, r in ch_display.iterrows():
        val = r[metric_col]
        if sel and r["channel"] == sel:
            col_colors.append(COLORS["white"])
        elif metric_col == "roi":
            col_colors.append(COLORS["positive"] if val >= 0 else COLORS["negative"])
        elif metric_col == "profit":
            col_colors.append(COLORS["positive"] if val >= 0 else COLORS["negative"])
        else:
            col_colors.append(CHANNEL_COLORS.get(r["channel"], COLORS["accent_blue"]))

        if metric_col == "roi":
            text_labels.append(f"{val:.2%}")
        elif metric_col == "roas":
            text_labels.append(f"{val:.2f}x")
        elif metric_col in ("profit", "cac", "rev_per_conversion"):
            text_labels.append(fmt_currency(val))
        elif metric_col == "spend_share":
            text_labels.append(f"{val:.1%}")
        else:
            text_labels.append(f"{val:,.2f}")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=ch_display["channel"],
        x=ch_display[metric_col],
        name=metric_label,
        orientation="h",
        marker_color=col_colors,
        text=text_labels,
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"], size=10),
        hovertemplate=f"<b>%{{y}}</b><br>{metric_label}: %{{x:{metric_fmt}}}<extra></extra>",
    ))
    if metric_col in ("roi", "profit"):
        fig.add_vline(x=0, line_color=COLORS["text_secondary"], line_width=1)
    fig.update_layout(showlegend=False)
    apply_layout(fig, f"{metric_label} by Channel")
    event = st.plotly_chart(fig, width='stretch', key="ch_param_bar", on_select="rerun", selection_mode="points")
    if event and event.selection and event.selection.get("points"):
        clicked = event.selection["points"][0].get("y") or event.selection["points"][0].get("label")
        if clicked and clicked != st.session_state.get("ch_selected"):
            st.session_state["ch_selected"] = clicked
            st.rerun()


def _render_aggrid(ch: pd.DataFrame, m: dict, nc_share: float):
    """AgGrid with sorting, column filters, conditional formatting, and Total row."""
    # Build display table
    table = ch[["channel", "spend", "revenue", "roi", "cac", "roas", "conversions", "loss_making", "role"]].copy()

    # Total row
    total_row = pd.DataFrame([{
        "channel":      "Total",
        "spend":        table["spend"].sum(),
        "revenue":      table["revenue"].sum(),
        "roi":          m["roi"],
        "cac":          m["cac"],
        "roas":         m["roas"],
        "conversions":  table["conversions"].sum(),
        "loss_making":  m["loss_making"],
        "role":         "—",
    }])
    table = pd.concat([table, total_row], ignore_index=True)

    # Format for display
    disp = table.copy()
    disp["spend"]       = disp["spend"].apply(lambda v: f"₹{v/1e6:.1f}M")
    disp["revenue"]     = disp["revenue"].apply(lambda v: f"₹{v/1e6:.2f}M")
    disp["roi"]         = disp["roi"].apply(lambda v: f"{v:.2f}" if not (isinstance(v, float) and math.isnan(v)) else "–")
    disp["cac"]         = disp["cac"].apply(lambda v: f"₹{v:,.2f}" if not (isinstance(v, float) and math.isnan(v)) else "–")
    disp["roas"]        = disp["roas"].apply(lambda v: f"{v:.2f}" if not (isinstance(v, float) and math.isnan(v)) else "–")
    disp["conversions"] = disp["conversions"].apply(lambda v: f"{int(v):,}" if pd.notna(v) and not (isinstance(v, float) and math.isnan(v)) else "–")
    disp.columns       = ["Channel", "Total Spend", "Total Revenue", "ROI", "CAC", "ROAS", "Total Conversions", "Status", "Role"]

    # AgGrid
    gb = GridOptionsBuilder.from_dataframe(disp)
    gb.configure_default_column(
        resizable=True, filterable=True, sortable=True,
        cellStyle={"color": COLORS["text_primary"], "backgroundColor": COLORS["bg_card"]},
    )
    gb.configure_column("Channel", minWidth=110, pinned="left",
                        cellStyle={"fontWeight": "bold", "color": COLORS["white"],
                                   "backgroundColor": COLORS["bg_card_alt"]})
    gb.configure_column("ROI", cellStyle=JsCode("""
        function(params) {
            var val = parseFloat(params.value);
            var color = val >= 0 ? '#22c55e' : '#ef4444';
            return { color: color, fontWeight: '700', backgroundColor: '#1a2060' };
        }
    """))
    gb.configure_column("Status", cellStyle=JsCode("""
        function(params) {
            var color = params.value === 'Loss' ? '#ef4444' : '#22c55e';
            return { color: color, fontWeight: '600', backgroundColor: '#1a2060' };
        }
    """))
    gb.configure_column("Role", cellStyle=JsCode("""
        function(params) {
            var colors = { 'Cut': '#fb923c', 'Scale': '#22c55e', 'Hold': '#94a3b8', '—': '#94a3b8' };
            return { color: colors[params.value] || '#e2e8f0', fontWeight: '600',
                     backgroundColor: '#1a2060' };
        }
    """))
    gb.configure_selection("single", use_checkbox=False, rowMultiSelectWithClick=False)
    gb.configure_grid_options(
        domLayout="autoHeight",
        rowStyle={"backgroundColor": COLORS["bg_card"]},
        rowHoverHighlight=True,
        suppressMovableColumns=True,
        headerHeight=36,
    )
    go_opts = gb.build()
    go_opts["defaultColDef"]["headerClass"] = "ag-header-dark"

    grid_resp = AgGrid(
        disp,
        gridOptions=go_opts,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        theme="balham-dark",  # closest dark theme
        fit_columns_on_grid_load=True,
        height=280,
        key="ch_aggrid",
    )

    # Cross-filter from row selection
    sel_rows = grid_resp.selected_rows
    if sel_rows is not None:
        clicked_ch = None
        if hasattr(sel_rows, 'iloc') and len(sel_rows) > 0:
            clicked_ch = sel_rows.iloc[0].get("Channel")
        elif isinstance(sel_rows, list) and len(sel_rows) > 0:
            item = sel_rows[0]
            clicked_ch = item.get("Channel") if isinstance(item, dict) else None
        elif isinstance(sel_rows, dict) and "Channel" in sel_rows:
            clicked_ch = sel_rows.get("Channel")

        if clicked_ch and clicked_ch != "Total" and clicked_ch != st.session_state.get("ch_selected"):
            st.session_state["ch_selected"] = clicked_ch
            st.rerun()

    # CSV download
    csv = table.to_csv(index=False)
    st.download_button(
        "⬇ Download CSV",
        data=csv,
        file_name="channel_performance.csv",
        mime="text/csv",
        key="ch_download",
        width='stretch',
    )


def _render_share_chart(ch_display: pd.DataFrame):
    """Grouped bar: % of Spend vs % of Revenue per channel."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=ch_display["channel"],
        x=ch_display["spend_share"],
        name="% of Spend",
        orientation="h",
        marker_color=COLORS["accent_blue"],
        hovertemplate="<b>%{y}</b><br>Spend share: %{x:.2%}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=ch_display["channel"],
        x=ch_display["revenue_share"],
        name="% of Revenue",
        orientation="h",
        marker_color=COLORS["accent_cyan"],
        hovertemplate="<b>%{y}</b><br>Revenue share: %{x:.2%}<extra></extra>",
    ))
    fig.update_layout(barmode="group", legend=dict(orientation="h", y=-0.18))
    apply_layout(fig, "% of Spend vs % of Revenue")
    st.plotly_chart(fig, width='stretch', key="ch_share_bar")


def _render_rev_per_conv_bar(ch_display: pd.DataFrame, sel):
    """Horizontal bar: Revenue per Conversion by channel."""
    ch_sorted = ch_display.sort_values("rev_per_conversion")
    colors = [
        COLORS["white"] if (sel and r["channel"] == sel) else CHANNEL_COLORS.get(r["channel"], COLORS["accent_blue"])
        for _, r in ch_sorted.iterrows()
    ]
    fig = go.Figure(go.Bar(
        y=ch_sorted["channel"],
        x=ch_sorted["rev_per_conversion"],
        orientation="h",
        marker_color=colors,
        text=[f"₹{v:,.0f}" for v in ch_sorted["rev_per_conversion"]],
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"], size=10),
        hovertemplate="<b>%{y}</b><br>Rev/Conversion: ₹%{x:,.2f}<extra></extra>",
    ))
    apply_layout(fig, "Revenue per Conversion by channel")
    event = st.plotly_chart(fig, width='stretch', key="ch_rev_conv",
                            on_select="rerun", selection_mode="points")
    if event and event.selection and event.selection.get("points"):
        clicked = event.selection["points"][0].get("y") or event.selection["points"][0].get("label")
        if clicked and clicked != st.session_state.get("ch_selected"):
            st.session_state["ch_selected"] = clicked
            st.rerun()


def _render_profit_bar(ch: pd.DataFrame, sel):
    """Waterfall-style grouped bar: profit by channel, colour-coded."""
    ch_sorted = ch.sort_values("profit", ascending=False)
    colors = []
    for _, r in ch_sorted.iterrows():
        if sel and r["channel"] == sel:
            colors.append(COLORS["white"])
        elif r["profit"] >= 0:
            colors.append(COLORS["positive"])
        else:
            colors.append(COLORS["negative"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=ch_sorted["channel"],
        y=ch_sorted["profit"],
        name="Profit",
        marker_color=colors,
        text=[f"₹{v/1e6:.1f}M" for v in ch_sorted["profit"]],
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"], size=10),
        hovertemplate="<b>%{x}</b><br>Profit: ₹%{y:,.0f}<br>Loss Making: %{customdata}<extra></extra>",
        customdata=ch_sorted["loss_making"].values,
    ))
    fig.add_hline(y=0, line_color=COLORS["text_secondary"], line_width=1.5, line_dash="dot")
    apply_layout(fig, "Profit by channel (green = Profit, red = Loss)")
    fig.update_layout(height=260)
    event = st.plotly_chart(fig, width='stretch', key="ch_profit_bar",
                            on_select="rerun", selection_mode="points")
    if event and event.selection and event.selection.get("points"):
        clicked = event.selection["points"][0].get("x") or event.selection["points"][0].get("label")
        if clicked and clicked != st.session_state.get("ch_selected"):
            st.session_state["ch_selected"] = clicked
            st.rerun()


# ─── INSIGHTS ─────────────────────────────────────────────────────────────────

def _generate_insights(m, ch, best_ch, best_roi, worst_ch, worst_roi) -> list[str]:
    items = []

    # Best / worst
    items.append(
        f"<b>{best_ch}</b> leads with ROI of <b>{fmt_pct(best_roi)}</b> and "
        f"ROAS <b>{ch.loc[ch['channel']==best_ch,'roas'].values[0]:.2f}x</b>."
    )
    items.append(
        f"<b>{worst_ch}</b> is the worst performer at ROI <b>{fmt_pct(worst_roi)}</b> — "
        f"consider reallocating budget to Scale channels."
    )

    # Loss-making
    loss_chs = ch[ch["profit"] < 0]
    if not loss_chs.empty:
        total_loss = loss_chs["profit"].sum()
        items.append(
            f"Loss-making channels: <b>{', '.join(loss_chs['channel'].tolist())}</b>. "
            f"Combined loss: <b>{fmt_currency(total_loss)}</b>."
        )

    # Spend concentration
    if not ch.empty:
        top_ch = ch.sort_values("spend_share", ascending=False).iloc[0]
        items.append(
            f"<b>{top_ch['channel']}</b> accounts for the largest spend share "
            f"(<b>{top_ch['spend_share']:.1%}</b> of total portfolio spend)."
        )

    # Rev per conversion range
    rpc_valid = ch["rev_per_conversion"].dropna()
    if not rpc_valid.empty:
        rpc_max = rpc_valid.max()
        rpc_min = rpc_valid.min()
        best_rpc_ch = ch.loc[ch["rev_per_conversion"].idxmax(), "channel"]
        items.append(
            f"Revenue per conversion ranges from <b>{fmt_currency(rpc_min)}</b> to "
            f"<b>{fmt_currency(rpc_max)}</b>. "
            f"<b>{best_rpc_ch}</b> delivers the highest value per conversion."
        )

    return items
