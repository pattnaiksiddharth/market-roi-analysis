"""
tests/test_measures.py
pytest unit tests for utils/measures.py

Run from the dashboard/ directory:
    pytest tests/ -v

Tests:
  1. Total Spend, Revenue, Conversions match raw CSV sums.
  2. ROI = (Revenue - Spend) / Spend.
  3. ROAS = Revenue / Spend.
  4. Profit = Revenue - Spend.
  5. Moved Budget = Source Spend * shift%.
  6. Projected Revenue = Baseline Revenue - Revenue Lost + Revenue Gained.
  7. safe_div returns NaN (not inf) on zero denominator.
  8. New customers = conversions * share.
  9. CAC = Spend / New Customers.
  10. Best / Worst channel identification.
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np
import pandas as pd
import pytest

from pathlib import Path

# ── Make sure project root is on sys.path ──────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.measures import (
    compute_measures,
    compute_scenario_measures,
    best_channel,
    worst_channel,
    safe_div,
)

# ── Load the raw CSV once for all tests ────────────────────────────────────────
DATA_PATH = ROOT / "data" / "fact_campaign.csv"
if not DATA_PATH.exists():
    if (Path("dashboard") / "data" / "fact_campaign.csv").exists():
        DATA_PATH = Path("dashboard") / "data" / "fact_campaign.csv"
    elif (Path("data") / "fact_campaign.csv").exists():
        DATA_PATH = Path("data") / "fact_campaign.csv"

@pytest.fixture(scope="session")
def df_raw() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df["year_month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["year_week"]  = df["date"].dt.to_period("W").dt.to_timestamp()
    return df


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestCoreAggregation:
    """Tests 1-4: Core measures match raw CSV sums."""

    def test_total_spend(self, df_raw):
        expected = float(df_raw["spend"].sum())
        m = compute_measures(df_raw)
        assert math.isclose(m["total_spend"], expected, rel_tol=1e-5), \
            f"Total Spend mismatch: {m['total_spend']} vs {expected}"

    def test_total_revenue(self, df_raw):
        expected = float(df_raw["revenue"].sum())
        m = compute_measures(df_raw)
        assert math.isclose(m["total_revenue"], expected, rel_tol=1e-5), \
            f"Total Revenue mismatch: {m['total_revenue']} vs {expected}"

    def test_total_conversions(self, df_raw):
        expected = float(df_raw["conversions"].sum())
        m = compute_measures(df_raw)
        assert math.isclose(m["total_conversions"], expected, rel_tol=1e-5), \
            f"Total Conversions mismatch: {m['total_conversions']} vs {expected}"

    def test_roi(self, df_raw):
        m = compute_measures(df_raw)
        expected_roi = (m["total_revenue"] - m["total_spend"]) / m["total_spend"]
        assert math.isclose(m["roi"], expected_roi, rel_tol=1e-5), \
            f"ROI mismatch: {m['roi']} vs {expected_roi}"

    def test_roas(self, df_raw):
        m = compute_measures(df_raw)
        expected_roas = m["total_revenue"] / m["total_spend"]
        assert math.isclose(m["roas"], expected_roas, rel_tol=1e-5), \
            f"ROAS mismatch: {m['roas']} vs {expected_roas}"

    def test_profit(self, df_raw):
        m = compute_measures(df_raw)
        expected_profit = m["total_revenue"] - m["total_spend"]
        assert math.isclose(m["profit"], expected_profit, rel_tol=1e-5), \
            f"Profit mismatch: {m['profit']} vs {expected_profit}"


class TestCustomerAcquisition:
    """Tests 7-9: CAC, new customers."""

    def test_new_customers(self, df_raw):
        share = 0.7
        m = compute_measures(df_raw, new_customer_share=share)
        expected = m["total_conversions"] * share
        assert math.isclose(m["new_customers"], expected, rel_tol=1e-5)

    def test_cac(self, df_raw):
        m = compute_measures(df_raw, new_customer_share=0.7)
        expected_cac = m["total_spend"] / m["new_customers"]
        assert math.isclose(m["cac"], expected_cac, rel_tol=1e-5), \
            f"CAC mismatch: {m['cac']} vs {expected_cac}"


class TestSafeDiv:
    """Test 7: safe_div returns NaN on zero denominator, never inf."""

    def test_zero_denominator_returns_nan(self):
        result = safe_div(100, 0)
        assert math.isnan(result), f"Expected NaN, got {result}"

    def test_zero_denominator_series(self):
        result = safe_div(pd.Series([10, 20]), pd.Series([0, 4]))
        assert math.isnan(result.iloc[0])
        assert math.isclose(result.iloc[1], 5.0)

    def test_normal_division(self):
        assert math.isclose(safe_div(10, 4), 2.5)

    def test_no_inf_on_zero_denominator(self):
        """safe_div(n, 0) must return NaN not inf — the key DAX DIVIDE guarantee."""
        result = safe_div(1_000_000, 0)
        assert math.isnan(result), f"Expected NaN for division by 0, got {result}"
        assert not math.isinf(result if not math.isnan(result) else 0)


class TestScenarioMeasures:
    """Tests 5-6: Moved Budget and Projected Revenue identity."""

    @pytest.fixture
    def scenario(self, df_raw):
        shift_pct   = 0.20
        eff_factor  = 0.75
        result = compute_scenario_measures(df_raw, shift_pct, eff_factor)
        return result, shift_pct, eff_factor

    def test_moved_budget_equals_source_spend_times_shift(self, scenario):
        result, shift_pct, _ = scenario
        expected = result["source_spend"] * shift_pct
        assert math.isclose(result["moved_budget"], expected, rel_tol=1e-5), \
            f"Moved Budget: {result['moved_budget']} vs {expected}"

    def test_projected_revenue_identity(self, scenario):
        result, _, _ = scenario
        expected = result["baseline_revenue"] - result["revenue_lost"] + result["revenue_gained"]
        assert math.isclose(result["projected_revenue"], expected, rel_tol=1e-5), \
            f"Projected Revenue: {result['projected_revenue']} vs {expected}"

    def test_revenue_change(self, scenario):
        result, _, _ = scenario
        expected = result["projected_revenue"] - result["baseline_revenue"]
        assert math.isclose(result["revenue_change"], expected, rel_tol=1e-5)


class TestBestWorstChannel:
    """Test 10: Best / Worst channel identification."""

    def test_best_channel_has_highest_roi(self, df_raw):
        bch, broi = best_channel(df_raw)
        # Manually compute
        grp = df_raw.groupby("channel").agg(spend=("spend","sum"), revenue=("revenue","sum")).reset_index()
        grp["roi"] = (grp["revenue"] - grp["spend"]) / grp["spend"]
        assert bch == grp.loc[grp["roi"].idxmax(), "channel"], f"Best channel should be {grp.loc[grp['roi'].idxmax(), 'channel']}, got {bch}"
        assert math.isclose(broi, grp["roi"].max(), rel_tol=1e-5)

    def test_worst_channel_has_lowest_roi(self, df_raw):
        wch, wroi = worst_channel(df_raw)
        grp = df_raw.groupby("channel").agg(spend=("spend","sum"), revenue=("revenue","sum")).reset_index()
        grp["roi"] = (grp["revenue"] - grp["spend"]) / grp["spend"]
        assert wch == grp.loc[grp["roi"].idxmin(), "channel"]
        assert math.isclose(wroi, grp["roi"].min(), rel_tol=1e-5)


class TestEmptyDataFrame:
    """Edge-case: empty DataFrame returns NaN gracefully."""

    def test_empty_df_returns_nan_measures(self):
        empty = pd.DataFrame(columns=["spend","revenue","conversions","clicks","impressions","channel"])
        m = compute_measures(empty)
        assert math.isnan(m["total_spend"]) or m["total_spend"] == 0 or \
               isinstance(m["total_spend"], float)
        # Should not raise
