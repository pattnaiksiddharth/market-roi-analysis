"""
measures.py – Python translation of every Power BI DAX measure.

Each function has the original DAX measure name in a comment above it.
Translation rules:
  - DIVIDE(a, b) -> safe_div(a, b) returns NaN when b==0 (never inf).
  - REMOVEFILTERS(dim_channel) -> caller passes df_no_channel_filter.
  - Group-level measures use groupby("channel").agg() then apply formula on sums.
  - Ratios are NEVER averaged; always computed from summed numerators/denominators.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.theme import CHANNEL_ROLES, SCENARIOS, get_role


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def safe_div(numerator, denominator, fill=np.nan):
    """
    Replicate DAX DIVIDE(n, d) semantics.
    Returns fill (default NaN) when denominator is 0 or NaN.
    Never returns inf.
    """
    if isinstance(denominator, (int, float, np.number)):
        return fill if (denominator == 0 or np.isnan(denominator)) else numerator / denominator
    # vectorised pandas path
    with np.errstate(divide="ignore", invalid="ignore"):
        result = numerator / denominator
    if isinstance(result, pd.Series):
        result = result.replace([np.inf, -np.inf], fill)
    return result


# ─── CORE AGGREGATION ─────────────────────────────────────────────────────────

def compute_measures(df: pd.DataFrame, new_customer_share: float = 0.7) -> dict:
    """
    Primary entry-point.
    Takes an already-filtered DataFrame and returns a flat dict of all measures.
    Every KPI card, chart and table calls this function — no ad-hoc calculations.

    Parameters
    ----------
    df : pd.DataFrame
        Already filtered fact_campaign rows (date + channel filters applied).
    new_customer_share : float
        Fraction of conversions assumed to be new customers (default 0.7).
        Exposed as a sidebar widget on the Funnel page.

    Returns
    -------
    dict with keys matching DAX measure names (snake_case).
    """
    if df.empty:
        # Return NaN for every measure so UI can display "–"
        return _empty_measures()

    # ── Core sums ─────────────────────────────────────────────────────────────
    # DAX: Total Spend = SUM(fact_campaign[spend])
    total_spend = float(df["spend"].sum())

    # DAX: Total Revenue = SUM(fact_campaign[revenue])
    total_revenue = float(df["revenue"].sum())

    # DAX: Total Conversions = SUM(fact_campaign[conversions])
    total_conversions = float(df["conversions"].sum())

    total_impressions = float(df["impressions"].sum())
    total_clicks = float(df["clicks"].sum())

    # ── Customer acquisition ───────────────────────────────────────────────────
    # DAX: New Customers = [Total Conversions] * 0.7
    new_customers = total_conversions * new_customer_share

    # DAX: CAC = DIVIDE([Total Spend], [New Customers])
    cac = safe_div(total_spend, new_customers)

    # DAX: CPA = DIVIDE([Total Spend], [Total Conversions])
    cpa = safe_div(total_spend, total_conversions)

    # DAX: Revenue per Conversion = DIVIDE([Total Revenue], [Total Conversions])
    rev_per_conversion = safe_div(total_revenue, total_conversions)

    # ── Funnel ────────────────────────────────────────────────────────────────
    # DAX: CTR = DIVIDE(SUM(clicks), SUM(impressions))
    ctr = safe_div(total_clicks, total_impressions)

    # DAX: CVR = DIVIDE([Total Conversions], SUM(clicks))
    cvr = safe_div(total_conversions, total_clicks)

    # DAX: CPC = DIVIDE([Total Spend], SUM(clicks))
    cpc = safe_div(total_spend, total_clicks)

    # ── ROI / ROAS ────────────────────────────────────────────────────────────
    # DAX: ROI = DIVIDE([Total Revenue] - [Total Spend], [Total Spend])
    roi = safe_div(total_revenue - total_spend, total_spend)

    # DAX: ROAS = DIVIDE([Total Revenue], [Total Spend])
    roas = safe_div(total_revenue, total_spend)

    # ── Profit & Loss ─────────────────────────────────────────────────────────
    # DAX: Profit = [Total Revenue] - [Total Spend]
    profit = total_revenue - total_spend

    # DAX: Profit Margin = DIVIDE([Profit], [Total Revenue])
    profit_margin = safe_div(profit, total_revenue)

    # DAX: Loss Making = IF([Profit] < 0, "Loss", "Profit")
    loss_making = "Loss" if profit < 0 else "Profit"

    # DAX: Total Loss = SUMX(VALUES(channel), IF([Profit] < 0, [Profit], 0))
    ch_grp = _channel_aggregates(df)
    ch_grp["profit"] = ch_grp["revenue"] - ch_grp["spend"]
    total_loss = float(ch_grp.loc[ch_grp["profit"] < 0, "profit"].sum())

    return {
        "total_spend":         total_spend,
        "total_revenue":       total_revenue,
        "total_conversions":   total_conversions,
        "total_impressions":   total_impressions,
        "total_clicks":        total_clicks,
        "new_customers":       new_customers,
        "cac":                 cac,
        "cpa":                 cpa,
        "rev_per_conversion":  rev_per_conversion,
        "ctr":                 ctr,
        "cvr":                 cvr,
        "cpc":                 cpc,
        "roi":                 roi,
        "roas":                roas,
        "profit":              profit,
        "profit_margin":       profit_margin,
        "loss_making":         loss_making,
        "total_loss":          total_loss,
    }


# ─── CHANNEL-LEVEL MEASURES ───────────────────────────────────────────────────

def compute_channel_measures(df: pd.DataFrame, df_all: pd.DataFrame, new_customer_share: float = 0.7) -> pd.DataFrame:
    """
    Return per-channel aggregated measures.

    Parameters
    ----------
    df : DataFrame  – channel-filtered fact rows.
    df_all : DataFrame  – same date/type filters BUT no channel filter
                          (REMOVEFILTERS(dim_channel) equivalent).
    new_customer_share : float

    Never averages ratios — always recomputes from summed numerators/denominators.
    """
    grp = _channel_aggregates(df)

    total_spend_all  = float(df_all["spend"].sum())
    total_rev_all    = float(df_all["revenue"].sum())

    grp["new_customers"]      = grp["conversions"] * new_customer_share
    grp["roi"]                = safe_div(grp["revenue"] - grp["spend"], grp["spend"])
    grp["roas"]               = safe_div(grp["revenue"], grp["spend"])
    grp["profit"]             = grp["revenue"] - grp["spend"]
    grp["profit_margin"]      = safe_div(grp["profit"], grp["revenue"])
    grp["cac"]                = safe_div(grp["spend"], grp["new_customers"])
    grp["cpa"]                = safe_div(grp["spend"], grp["conversions"])
    grp["rev_per_conversion"] = safe_div(grp["revenue"], grp["conversions"])
    grp["ctr"]                = safe_div(grp["clicks"], grp["impressions"])
    grp["cvr"]                = safe_div(grp["conversions"], grp["clicks"])
    grp["cpc"]                = safe_div(grp["spend"], grp["clicks"])

    # DAX: % of Spend = DIVIDE([Total Spend], CALCULATE([Total Spend], ALL(dim_channel)))
    grp["spend_share"]        = safe_div(grp["spend"], total_spend_all)
    # DAX: % of Revenue = DIVIDE([Total Revenue], CALCULATE([Total Revenue], ALL(dim_channel)))
    grp["revenue_share"]      = safe_div(grp["revenue"], total_rev_all)

    # DAX: Loss Making flag per channel
    grp["loss_making"]        = grp["profit"].apply(lambda p: "Loss" if p < 0 else "Profit")

    # DAX: ROI Rank (Dense, DESC)
    grp["roi_rank"]           = grp["roi"].rank(ascending=False, method="dense").astype(int)

    # Add Role
    grp["role"]               = grp["channel"].map(get_role)

    return grp.reset_index(drop=True)


# ─── BEST / WORST CHANNEL ─────────────────────────────────────────────────────

def best_channel(df: pd.DataFrame) -> tuple[str, float]:
    """
    DAX: Best Channel = MAXX(TOPN(1, VALUES(channel), [ROI], DESC), channel)
    Returns (channel_name, roi_value) tuple.
    """
    grp = _channel_aggregates(df)
    grp["roi"] = safe_div(grp["revenue"] - grp["spend"], grp["spend"])
    idx = grp["roi"].idxmax()
    return grp.loc[idx, "channel"], float(grp.loc[idx, "roi"])


def worst_channel(df: pd.DataFrame) -> tuple[str, float]:
    """
    DAX: Worst Channel = MAXX(TOPN(1, VALUES(channel), [ROI], ASC), channel)
    Returns (channel_name, roi_value) tuple.
    """
    grp = _channel_aggregates(df)
    grp["roi"] = safe_div(grp["revenue"] - grp["spend"], grp["spend"])
    idx = grp["roi"].idxmin()
    return grp.loc[idx, "channel"], float(grp.loc[idx, "roi"])


# ─── BUDGET SCENARIO MEASURES ─────────────────────────────────────────────────

def compute_scenario_measures(
    df_no_channel: pd.DataFrame,
    budget_shift_pct: float,
    efficiency_factor: float,
    new_customer_share: float = 0.7,
) -> dict:
    """
    Compute all Budget Scenario DAX measures.

    Parameters
    ----------
    df_no_channel : DataFrame
        All filters EXCEPT channel (REMOVEFILTERS equiv).
    budget_shift_pct : float
        Fraction of Cut-channel spend to move (0–0.5). From Streamlit slider.
    efficiency_factor : float
        Conversion efficiency on target channels (0.5–1.0). From Streamlit slider.

    Returns
    -------
    dict of all Baseline*, Source*, Target*, Projected* measures + Scenario table.
    """
    if df_no_channel.empty:
        return _empty_scenario_measures()

    dim_ch = _load_dim_channel_cached()

    # ── Baseline (all channels, no channel filter) ─────────────────────────────
    # DAX: Baseline Spend = CALCULATE([Total Spend], REMOVEFILTERS(dim_channel))
    baseline_spend   = float(df_no_channel["spend"].sum())
    # DAX: Baseline Revenue = CALCULATE([Total Revenue], REMOVEFILTERS(dim_channel))
    baseline_revenue = float(df_no_channel["revenue"].sum())
    # DAX: Baseline ROI = DIVIDE([Baseline Revenue] - [Baseline Spend], [Baseline Spend])
    baseline_roi     = safe_div(baseline_revenue - baseline_spend, baseline_spend)

    # ── Source channels (Role = "Cut") ────────────────────────────────────────
    cut_channels  = [c for c, r in CHANNEL_ROLES.items() if r == "Cut"]
    scale_channels = [c for c, r in CHANNEL_ROLES.items() if r == "Scale"]

    df_cut   = df_no_channel[df_no_channel["channel"].isin(cut_channels)]
    df_scale = df_no_channel[df_no_channel["channel"].isin(scale_channels)]

    # DAX: Source Spend = CALCULATE([Total Spend], ..., dim_channel[Role] = "Cut")
    source_spend   = float(df_cut["spend"].sum())
    # DAX: Source Revenue = CALCULATE([Total Revenue], ..., dim_channel[Role] = "Cut")
    source_revenue = float(df_cut["revenue"].sum())
    # DAX: Source ROAS = DIVIDE([Source Revenue], [Source Spend])
    source_roas    = safe_div(source_revenue, source_spend)

    # ── Target channels (Role = "Scale") ──────────────────────────────────────
    # DAX: Target Spend = CALCULATE([Total Spend], ..., dim_channel[Role] = "Scale")
    target_spend   = float(df_scale["spend"].sum())
    # DAX: Target Revenue = CALCULATE([Total Revenue], ..., dim_channel[Role] = "Scale")
    target_revenue = float(df_scale["revenue"].sum())
    # DAX: Target ROAS = DIVIDE([Target Revenue], [Target Spend])
    target_roas    = safe_div(target_revenue, target_spend)

    # ── Core scenario maths ───────────────────────────────────────────────────
    # DAX: Moved Budget = [Source Spend] * [Budget Shift % Value]
    moved_budget   = source_spend * budget_shift_pct

    # DAX: Revenue Lost = [Moved Budget] * [Source ROAS]
    revenue_lost   = moved_budget * (source_roas if not np.isnan(source_roas) else 0)

    # DAX: Revenue Gained = [Moved Budget] * [Target ROAS] * [Efficiency Factor Value]
    revenue_gained = moved_budget * (target_roas if not np.isnan(target_roas) else 0) * efficiency_factor

    # DAX: Projected Revenue = [Baseline Revenue] - [Revenue Lost] + [Revenue Gained]
    projected_revenue = baseline_revenue - revenue_lost + revenue_gained

    # DAX: Revenue Change = [Projected Revenue] - [Baseline Revenue]
    revenue_change = projected_revenue - baseline_revenue

    # DAX: Revenue Change % = DIVIDE([Revenue Change], [Baseline Revenue])
    revenue_change_pct = safe_div(revenue_change, baseline_revenue)

    # DAX: Projected ROI = DIVIDE([Projected Revenue] - [Baseline Spend], [Baseline Spend])
    projected_roi = safe_div(projected_revenue - baseline_spend, baseline_spend)

    # DAX: ROI Change (pp) = ([Projected ROI] - [Baseline ROI]) * 100
    roi_change_pp = (projected_roi - baseline_roi) * 100 if not np.isnan(projected_roi) else np.nan

    # ── Scenarios table ───────────────────────────────────────────────────────
    # DAX: Revenue Change by Scenario = Moved Budget * Target ROAS * factor - Revenue Lost
    scenario_rows = []
    for s in SCENARIOS:
        factor = s["Factor"]
        rev_gained_s = moved_budget * (target_roas if not np.isnan(target_roas) else 0) * factor
        rev_change_s = rev_gained_s - revenue_lost
        scenario_rows.append({
            "Scenario":       s["Scenario"],
            "Factor":         factor,
            "Revenue Change": rev_change_s,
        })
    scenario_df = pd.DataFrame(scenario_rows)

    # ── Per-channel Scenario Spend ─────────────────────────────────────────────
    # DAX: Scenario Spend per channel
    # Scale channels: spend + (Moved Budget / count of ALL Scale channels)
    n_scale_all = len(scale_channels)
    ch_grp = _channel_aggregates(df_no_channel)
    ch_grp["role"] = ch_grp["channel"].map(get_role)

    def _scenario_spend(row):
        # DAX: "Cut" -> spend * (1 - shift%), "Scale" -> spend + moved/n_scale, else unchanged
        if row["role"] == "Cut":
            return row["spend"] * (1 - budget_shift_pct)
        elif row["role"] == "Scale":
            return row["spend"] + safe_div(moved_budget, n_scale_all, fill=row["spend"])
        else:
            return row["spend"]

    ch_grp["scenario_spend"] = ch_grp.apply(_scenario_spend, axis=1)
    ch_grp["roas"]           = safe_div(ch_grp["revenue"], ch_grp["spend"])

    return {
        "baseline_spend":      baseline_spend,
        "baseline_revenue":    baseline_revenue,
        "baseline_roi":        baseline_roi,
        "source_spend":        source_spend,
        "source_revenue":      source_revenue,
        "source_roas":         source_roas,
        "target_spend":        target_spend,
        "target_revenue":      target_revenue,
        "target_roas":         target_roas,
        "moved_budget":        moved_budget,
        "revenue_lost":        revenue_lost,
        "revenue_gained":      revenue_gained,
        "projected_revenue":   projected_revenue,
        "revenue_change":      revenue_change,
        "revenue_change_pct":  revenue_change_pct,
        "projected_roi":       projected_roi,
        "roi_change_pp":       roi_change_pp,
        "scenario_df":         scenario_df,
        "channel_scenario_df": ch_grp,
    }


# ─── TIME-SERIES AGGREGATION ──────────────────────────────────────────────────

def compute_timeseries(df: pd.DataFrame, granularity: str = "monthly") -> pd.DataFrame:
    """
    Aggregate fact rows to a time-series for trend charts.
    granularity: 'daily' | 'weekly' | 'monthly'
    """
    if df.empty:
        return pd.DataFrame()

    col_map = {
        "daily":   "date",
        "weekly":  "year_week",
        "monthly": "year_month",
    }
    time_col = col_map.get(granularity, "year_month")

    grp = (
        df.groupby(time_col)
        .agg(
            spend=("spend", "sum"),
            revenue=("revenue", "sum"),
            conversions=("conversions", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
        )
        .reset_index()
        .rename(columns={time_col: "period"})
    )
    grp["profit"]       = grp["revenue"] - grp["spend"]
    grp["roi"]          = safe_div(grp["revenue"] - grp["spend"], grp["spend"])
    grp["roas"]         = safe_div(grp["revenue"], grp["spend"])
    grp["profit_margin"] = safe_div(grp["profit"], grp["revenue"])
    return grp


# ─── CAMPAIGN-TYPE AGGREGATION ────────────────────────────────────────────────

def compute_campaign_type_measures(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by campaign_type for Campaign Analysis page."""
    if df.empty:
        return pd.DataFrame()
    grp = (
        df.groupby("campaign_type")
        .agg(spend=("spend", "sum"), revenue=("revenue", "sum"),
             conversions=("conversions", "sum"), impressions=("impressions", "sum"),
             clicks=("clicks", "sum"))
        .reset_index()
    )
    grp["roi"]    = safe_div(grp["revenue"] - grp["spend"], grp["spend"])
    grp["roas"]   = safe_div(grp["revenue"], grp["spend"])
    grp["profit"] = grp["revenue"] - grp["spend"]
    grp["profit_margin"] = safe_div(grp["profit"], grp["revenue"])
    return grp


def compute_channel_campaign_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """
    ROI pivot: channels × campaign_types.
    Used for the cross-tab table on Campaign Analysis page.
    """
    if df.empty:
        return pd.DataFrame()

    grp = (
        df.groupby(["channel", "campaign_type"])
        .agg(spend=("spend", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    grp["roi"] = safe_div(grp["revenue"] - grp["spend"], grp["spend"])

    pivot = grp.pivot_table(
        index="channel",
        columns="campaign_type",
        values="roi",
        aggfunc="first",
    ).reset_index()

    # Add total ROI per channel
    ch_total = (
        df.groupby("channel")
        .agg(spend=("spend", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    ch_total["roi"] = safe_div(ch_total["revenue"] - ch_total["spend"], ch_total["spend"])
    pivot = pivot.merge(ch_total[["channel", "roi"]].rename(columns={"roi": "Total"}), on="channel")

    return pivot


# ─── PRIVATE HELPERS ──────────────────────────────────────────────────────────

def _channel_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("channel", observed=True)
        .agg(
            spend=("spend", "sum"),
            revenue=("revenue", "sum"),
            conversions=("conversions", "sum"),
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
        )
        .reset_index()
    )


def _empty_measures() -> dict:
    keys = [
        "total_spend", "total_revenue", "total_conversions", "total_impressions",
        "total_clicks", "new_customers", "cac", "cpa", "rev_per_conversion",
        "ctr", "cvr", "cpc", "roi", "roas", "profit", "profit_margin",
        "loss_making", "total_loss",
    ]
    d = {k: np.nan for k in keys}
    d["loss_making"] = "–"
    return d


def _empty_scenario_measures() -> dict:
    keys = [
        "baseline_spend", "baseline_revenue", "baseline_roi",
        "source_spend", "source_revenue", "source_roas",
        "target_spend", "target_revenue", "target_roas",
        "moved_budget", "revenue_lost", "revenue_gained",
        "projected_revenue", "revenue_change", "revenue_change_pct",
        "projected_roi", "roi_change_pp",
    ]
    d = {k: np.nan for k in keys}
    d["scenario_df"] = pd.DataFrame()
    d["channel_scenario_df"] = pd.DataFrame()
    return d


def _load_dim_channel_cached():
    """Import lazily to avoid circular dependency."""
    from utils.data_loader import load_dim_channel
    return load_dim_channel()
