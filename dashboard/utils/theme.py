"""
Central theme/colour configuration.
Extracted from Power BI screenshots (dark-mode, blue-purple gradient).
All pages, charts, and CSS import from here — edit in one place to restyle everything.
"""

# ─── COLOUR PALETTE ────────────────────────────────────────────────────────────
COLORS = {
    # Backgrounds
    "bg_primary":       "#5c61a6",   # Contrasting periwinkle/purple (page canvas background)
    "bg_card":          "#0c1033",   # Deep navy for distinct card partitions
    "bg_card_alt":      "#090d2a",   # Darker card variant
    "bg_sidebar":       "#0a0e2a",   # Dark navy sidebar
    "bg_header":        "#0c1033",   # Header partition card

    # Gradient ends (left → right on cards)
    "gradient_start":   "#1e2a8a",   # Mid-blue
    "gradient_end":     "#6b3fa0",   # Purple

    # Primary accents
    "accent_blue":      "#4f6cf7",   # Bright blue (active nav, highlights)
    "accent_purple":    "#8b5cf6",   # Purple (secondary accent)
    "accent_cyan":      "#06b6d4",   # Cyan (chart line 2)
    "accent_teal":      "#14b8a6",   # Teal

    # Chart colours (in order, match Power BI colourway)
    "chart_1":          "#4f6cf7",   # Blue
    "chart_2":          "#06b6d4",   # Cyan
    "chart_3":          "#a78bfa",   # Light purple
    "chart_4":          "#f472b6",   # Pink
    "chart_5":          "#34d399",   # Green
    "chart_6":          "#fb923c",   # Orange

    # Semantic
    "positive":         "#22c55e",   # Profit / good (green)
    "negative":         "#ef4444",   # Loss / bad (red)
    "neutral":          "#94a3b8",   # Hold / grey

    # Text
    "text_primary":     "#e2e8f0",   # Main text
    "text_secondary":   "#94a3b8",   # Muted / labels
    "text_accent":      "#a78bfa",   # Purple accent text
    "white":            "#ffffff",

    # KPI delta colours
    "delta_up":         "#22c55e",
    "delta_down":       "#ef4444",
}

# Chart colourway list (used in Plotly template)
CHART_COLORS = [
    COLORS["chart_1"],
    COLORS["chart_2"],
    COLORS["chart_3"],
    COLORS["chart_4"],
    COLORS["chart_5"],
    COLORS["chart_6"],
]

# ─── CHANNEL COLOURS ───────────────────────────────────────────────────────────
CHANNEL_COLORS = {
    "Email":      "#4f6cf7",
    "Facebook":   "#a78bfa",
    "Google Ads": "#06b6d4",
    "Instagram":  "#f472b6",
    "Website":    "#34d399",
    "YouTube":    "#fb923c",
}

# ─── PLOTLY TEMPLATE ───────────────────────────────────────────────────────────
def get_plotly_layout() -> dict:
    """Return a base Plotly layout dict to apply to every figure."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_primary"], family="Inter, sans-serif", size=12),
        title_font=dict(color=COLORS["white"], size=14, family="Inter, sans-serif"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLORS["text_secondary"], size=11),
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.06)",
            linecolor="rgba(255,255,255,0.1)",
            tickcolor=COLORS["text_secondary"],
            tickfont=dict(color=COLORS["text_secondary"]),
            zerolinecolor="rgba(255,255,255,0.1)",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.06)",
            linecolor="rgba(255,255,255,0.1)",
            tickcolor=COLORS["text_secondary"],
            tickfont=dict(color=COLORS["text_secondary"]),
            zerolinecolor="rgba(255,255,255,0.1)",
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=dict(
            bgcolor=COLORS["bg_card"],
            bordercolor=COLORS["accent_blue"],
            font=dict(color=COLORS["white"], size=12),
        ),
        colorway=CHART_COLORS,
        autosize=True,
    )

# ─── ECHARTS BASE THEME ────────────────────────────────────────────────────────
ECHARTS_THEME = {
    "backgroundColor": "transparent",
    "textStyle": {"color": COLORS["text_primary"], "fontFamily": "Inter, sans-serif"},
    "title": {"textStyle": {"color": COLORS["white"]}},
    "legend": {"textStyle": {"color": COLORS["text_secondary"]}},
    "color": CHART_COLORS,
}

# ─── ROLE MAPPING ─────────────────────────────────────────────────────────────
# Edit here to change which channels are Cut / Scale / Hold
CHANNEL_ROLES = {
    "YouTube":    "Cut",
    "Facebook":   "Cut",
    "Instagram":  "Scale",
    "Google Ads": "Scale",
    # Everything else defaults to "Hold"
}

def get_role(channel: str) -> str:
    return CHANNEL_ROLES.get(channel, "Hold")

# ─── SCENARIO TABLE ────────────────────────────────────────────────────────────
SCENARIOS = [
    {"Scenario": "Conservative", "Factor": 0.60},
    {"Scenario": "Base",         "Factor": 0.75},
    {"Scenario": "Optimistic",   "Factor": 0.90},
]
