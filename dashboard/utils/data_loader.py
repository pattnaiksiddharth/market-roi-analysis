"""
Data loading utilities.
Uses @st.cache_data so large CSV is read once per session.
Maps flat-file columns to the fact_campaign / dim_channel model.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

# ─── PATHS ────────────────────────────────────────────────────────────────────
_THIS_DIR = Path(__file__).resolve().parent
_DATA_DIR = _THIS_DIR.parent / "data"

# Fallback paths if run from different working directory locations
if not (_DATA_DIR / "fact_campaign.csv").exists():
    if (Path("dashboard") / "data" / "fact_campaign.csv").exists():
        _DATA_DIR = Path("dashboard") / "data"
    elif (Path("data") / "fact_campaign.csv").exists():
        _DATA_DIR = Path("data")

_FACT_PATH = _DATA_DIR / "fact_campaign.csv"
_DIM_CHANNEL_PATH = _DATA_DIR / "dim_channel.csv"
_DIM_DATE_PATH = _DATA_DIR / "dim_date.csv"


@st.cache_data(show_spinner="Loading campaign data…")
def load_fact() -> pd.DataFrame:
    """
    Load fact_campaign.csv and return a cleaned DataFrame.

    Columns in file:
        campaign_id, date, channel, campaign_type, company,
        target_audience, customer_segment, location,
        impressions, clicks, conversions, spend, revenue

    No column mismatches detected against the DAX model:
        - spend, revenue, conversions, clicks, impressions all present.
        - 'channel' joins directly to dim_channel on channel name.
    """
    df = pd.read_csv(
        _FACT_PATH,
        parse_dates=["date"],
        dtype={
            "campaign_id":       "int32",
            "impressions":       "int32",
            "clicks":            "int32",
            "conversions":       "int32",
            "spend":             "float32",
            "revenue":           "float32",
            "channel":           "category",
            "campaign_type":     "category",
            "company":           "category",
            "target_audience":   "category",
            "customer_segment":  "category",
            "location":          "category",
        },
    )

    # Derive time columns used by slicers and charts
    df["year_month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["year_week"]  = df["date"].dt.to_period("W").dt.to_timestamp()
    df["year"]       = df["date"].dt.year
    df["month"]      = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b %Y")
    df["quarter"]    = df["date"].dt.to_period("Q").astype(str)

    return df


@st.cache_data(show_spinner=False)
def load_dim_channel() -> pd.DataFrame:
    """Load dim_channel.csv with Role column appended."""
    from utils.theme import get_role  # avoid circular at module level

    df = pd.read_csv(_DIM_CHANNEL_PATH)
    df["Role"] = df["channel"].map(get_role).fillna("Hold")
    return df


@st.cache_data(show_spinner=False)
def load_dim_date() -> pd.DataFrame:
    """Load dim_date.csv."""
    return pd.read_csv(_DIM_DATE_PATH, parse_dates=["date"])


def apply_filters(
    df: pd.DataFrame,
    channels: list[str] | None,
    date_start,
    date_end,
    campaign_types: list[str] | None = None,
    locations: list[str] | None = None,
) -> pd.DataFrame:
    """
    Apply global filter selections to the fact DataFrame.
    Returns df_filtered (all filters applied).
    """
    mask = pd.Series(True, index=df.index)

    if channels:
        mask &= df["channel"].isin(channels)
    if date_start is not None:
        mask &= df["date"] >= pd.Timestamp(date_start)
    if date_end is not None:
        mask &= df["date"] <= pd.Timestamp(date_end)
    if campaign_types:
        mask &= df["campaign_type"].isin(campaign_types)
    if locations:
        mask &= df["location"].isin(locations)

    filtered = df[mask]
    if filtered.empty:
        return filtered  # caller must handle empty gracefully

    return filtered


def apply_filters_no_channel(
    df: pd.DataFrame,
    date_start,
    date_end,
    campaign_types: list[str] | None = None,
    locations: list[str] | None = None,
) -> pd.DataFrame:
    """
    Apply all filters EXCEPT channel filter.
    Used for REMOVEFILTERS(dim_channel) semantics:
    Baseline*, Source*, Target*, % of Spend, % of Revenue.
    """
    return apply_filters(df, None, date_start, date_end, campaign_types, locations)
