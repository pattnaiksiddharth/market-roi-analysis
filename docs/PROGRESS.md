# Project Progress Log

---

## Phase 0 — Repo Scaffolding
**Date:** 2026-10-03
**Status:** COMPLETE

### Actions taken
- Created directory tree: data/raw, data/processed, notebooks/, sql/, dashboard/, images/, docs/
- Confirmed raw dataset: 200,000 rows x 16 columns
- Identified key data issues to fix in Phase 1:
  - `Acquisition_Cost` stored as string with dollar sign and comma (e.g. "$16,174.00")
  - `Date` stored as DD-MM-YYYY string, needs parsing to datetime
  - `Duration` stored as "30 days" string, needs numeric extraction
  - `ROI` and `Conversion_Rate` are already numeric (float) - verify range
  - `Impressions`, `Clicks` - need CTR derivation
- README.md written with full data provenance and methodology rules

### Next step
Wait for "next" to begin Phase 1: Data Audit and Cleaning.

---

---

## Phase 1 — Dataset Audit & Simulation Layer
**Date:** 2026-10-03
**Status:** COMPLETE

### Dataset facts confirmed
- 200,000 rows x 16 columns, zero nulls
- Date range: 01-Jan-2021 to 31-Dec-2021 (365 unique dates, full year)
- 6 channels, 5 campaign types, 5 companies, 5 locations — all uniformly distributed (~33k rows/channel, ~40k rows/campaign type)
- Acquisition_Cost = total campaign budget ($5k-$20k), NOT CPA — key interpretation finding
- Raw ROI column is uniform noise (all channels ~5.0) — NOT usable for analysis

### Critical finding
The raw dataset has NO channel performance differentiation. All channels return ROI ~5.0.
This is uniform random noise, not real business signal. We must simulate Revenue to create
a realistic analytical story.

### Simulation decisions
- Spend = Acquisition_Cost_num (total campaign budget per row)
- Conversions = max(1, round(Clicks x Conversion_Rate)) — pure derivation
- CPA = Spend / Conversions — pure derivation
- CTR = Clicks / Impressions — pure derivation
- AOV ~ Lognormal(mu, sigma) per channel, seed=42 — SIMULATED
- Revenue = Conversions x AOV — derived from simulation

### Output file
- data/raw/simulated_marketing.csv (200,000 rows x 29 columns)
- 16 original columns: unmodified
- 13 new columns: Acquisition_Cost_num, Date_dt, Duration_days, Spend, Conversions, CPA, AOV, Revenue, ROI_computed, CTR, Month, Quarter, Week

### Channel ROI story (aggregate, seed=42)
- Instagram: +46.8% (scale up)
- Google Ads: +34.7% (invest more)
- Email: +17.8% (maintain)
- Website: +3.1% (monitor)
- Facebook: -22.8% (reduce)
- YouTube: -43.4% (stop)
- Overall portfolio ROI: +6.2%

### Next step
Wait for "next" to begin Phase 1 proper: 01_data_cleaning.ipynb

---

---

## Phase 2 — Data Cleaning & Validation (01_cleaning.ipynb)
**Date:** 2026-10-03
**Status:** COMPLETE

### Audit findings
- 200,000 rows x 29 columns loaded from simulated_marketing.csv
- Zero nulls, zero full-row duplicates, zero Campaign_ID duplicates
- All 8 logical checks PASSED (spend>0, revenue>0, clicks<=impressions, etc.)
- All 365 calendar days present — zero date gaps
- Spend: zero IQR outliers (bounded raw field $5k-$20k)
- Revenue: 9,874 rows above IQR upper fence — KEPT (lognormal right-tail, expected)
- ROI_computed: 2,841 rows capped at upper=5.0 / lower=-1.0

### Key decisions logged
1. KEEP Revenue outliers — lognormal right-tail is mathematically expected, not errors
2. CAP ROI_computed at [−1.0, +5.0] — controls modelling leverage, preserves row count
3. DROP raw ROI column — uniform noise ~5.0 across all channels, zero signal
4. FIX date parsing with dayfirst=True — critical for DD-MM-YYYY format
5. RENAME all columns to snake_case — Python/SQL convention

### Outputs created
- data/processed/clean.csv (200,000 rows x 29 columns — 0 rows dropped)
- data/processed/cleaning_log.csv (13 entries)
- images/01_missing_values.png
- images/01_boxplot_spend_revenue_by_channel.png
- images/01_boxplot_roi_by_channel.png

### Before / After
- Rows: 200,000 → 200,000 (0 dropped)
- Columns: 29 → 29 (3 dropped, 2 added: year, year_month)
- ROI capped rows: 2,841 (1.42%)

### Next step
Wait for "next" to begin Phase 3: 02_eda.ipynb (Exploratory Data Analysis)

---

---

## Phase 3 -- Metrics Engine (02_metrics.ipynb)
**Date:** 2026-10-03
**Status:** COMPLETE

### Deliverables
- notebooks/02_metrics.ipynb (27 cells, full metric function library + summarize())
- data/processed/summary_campaign.csv (5 rows x 21 cols)
- data/processed/summary_channel.csv (6 rows x 21 cols)
- data/processed/summary_month.csv (12 rows x 21 cols)
- sql/metrics.sql (5 GROUP BY queries, PostgreSQL syntax, fully commented)

### Metrics implemented
CTR, CVR, CPC, CPA, CAC, ROAS, ROI, Gross Profit, Effective AOV, LTV, LTV:CAC, Payback Months

### Key assumptions documented
- new_customer_share = 0.60 (60% of conversions assumed new customers)
- gross_margin = 0.40 (40% e-commerce gross margin)
- avg_orders_per_customer = 2.50
- avg_months_active = 12

### Sanity checks: 18/18 PASS
All five additive metrics (impressions, clicks, conversions, spend, revenue) and n_campaigns
reconcile perfectly across all three summary tables to grand totals in clean.csv.

### ROI proof
- WRONG (mean row-level): 19.91%
- RIGHT (ratio of sums):   6.16%
- Overstatement: 13.75 percentage points -- a critical methodological finding

### Channel findings (aggregate ROI, Rule #3 compliant)
- Instagram:  +46.8% ROI, 1.47x ROAS -- SCALE UP
- Google Ads: +34.7% ROI, 1.35x ROAS -- INVEST MORE
- Email:      +17.8% ROI, 1.18x ROAS -- MAINTAIN
- Website:     +3.1% ROI, 1.03x ROAS -- MONITOR
- Facebook:   -22.8% ROI, 0.77x ROAS -- REDUCE
- YouTube:    -43.4% ROI, 0.57x ROAS -- STOP

### LTV:CAC note
All channels show LTV:CAC < 1.0 under current assumptions (AOV ~$302, CAC ~$474).
This means the business recaptures acquisition cost only through repeat purchases.
In the real project, this would trigger a recommendation to either:
(a) increase average order value through upsell/cross-sell, or
(b) reduce acquisition costs, or
(c) obtain real retention data to compute true multi-purchase LTV.

### Next step
Wait for "next" to begin Phase 4: 03_eda_and_viz.ipynb

---

---

## Phase 4A -- Channel Comparison Analysis (03_analysis.ipynb)
**Date:** 2026-10-03
**Status:** COMPLETE

### Deliverables
- notebooks/03_analysis.ipynb (17 cells)
- images/03_spend_vs_revenue_share.png  -- HEADLINE CHART
- images/03_roi_by_channel.png
- images/03_cac_vs_cvr_scatter.png

### Flag results (thresholds: spend_share >= 16.67%, ROI vs 6.16% portfolio avg)
- YouTube: HIGH VOLUME, POOR RETURN (spend_share=16.67%, ROI=-43.4%)
- Facebook: Below Average ROI (spend_share=16.42% -- just below threshold, ROI=-22.8%)
- Instagram, Google Ads, Email: Above Average
- Website: Below Average ROI (ROI=+3.1%, below portfolio 6.16%)

### Combined Rank (ROI + CAC + CVR)
1. Email (#1 overall: best CVR, 2nd lowest CAC)
2. Website (#2: lowest CAC)
3. Facebook (#3)
4. Instagram (#4: best ROI, but highest CAC)
5. Google Ads (#5)
6. YouTube (#6: worst ROI, worst CVR)

### Key insight: CVR and CAC are nearly identical across channels
This is a data construction artifact (uniform distribution). The real differentiator
is effective AOV: Instagram $419, Google Ads $384, Email $334, Website $291, Facebook $219, YouTube $161.
This becomes the central analytical story: same cost to acquire, wildly different customer value.

### 5 Decision-Ready Insights
1. STOP YouTube -- destroying $181M annually (ROI -43.4%)
2. Scale Instagram -- best ROI (+46.8%), highest AOV ($419), revenue share 6.4pp above spend share
3. Facebook + YouTube combined destroy $274M on $827M spend
4. CVR/CAC uniform -- differentiator is customer quality (AOV), not funnel efficiency
5. Email is underrated -- +17.8% ROI, lowest CAC, highest CVR

### Next step
Wait for "next" to begin Phase 4B: campaign-type analysis and time-series trends

---

---

## Phase 5 -- Trends, Seasonality & Diminishing Returns Analysis (03_analysis.ipynb Part B)
**Date:** 2026-10-03
**Status:** COMPLETE

### Deliverables
- notebooks/03_analysis.ipynb (Updated with Part A + Part B, 25 cells total)
- images/03_monthly_spend_vs_revenue.png (Monthly spend vs revenue and ROI trend)
- images/03_seasonality_heatmap.png (Channel x Month ROI heatmap)
- images/03_diminishing_returns_scatter.png (Log-Log spend vs revenue scatter with power-law fit)

### Strategic Allocation Decisions
1. **Instagram (Scale):** Elasticity $\beta = 1.079$, ROI +46.79%.
2. **Google Ads (Scale):** Elasticity $\beta = 1.174$, ROI +34.73%.
3. **Email (Scale):** Elasticity $\beta = 0.938$, ROI +17.79%.
4. **Website (Hold):** Elasticity $\beta = 0.762$, ROI +3.06% (diminishing returns threshold).
5. **Facebook (Saturated):** Elasticity $\beta = 0.863$, ROI -22.76% (capital incinerator).
6. **YouTube (Saturated):** Elasticity $\beta = 0.895$, ROI -43.41% (severe saturation).

---

## Phase 6 -- Campaign Level Analysis & Budget Recommendations (03_analysis.ipynb Part C)
**Date:** 2026-10-03
**Status:** COMPLETE

### Deliverables
- notebooks/03_analysis.ipynb (Complete master notebook with Parts A, B, and C - 35 cells total)
- images/03_top_bottom_campaigns_roi.png (Horizontal bar chart of top 5 and bottom 5 ROI campaigns)

### Summary of Findings
1. **Minimum Spend Filter:** Applied 25th percentile spend threshold (\.62M) across 30 campaign entities (Channel - CampaignType). Retained 22 filtered campaigns, excluded 8 low-volume cells.
2. **Top Winners:** All top 5 campaigns belong to **Instagram** (Instagram - Social Media +48.82% ROI down to Instagram - Email +45.60% ROI).
3. **Negative ROI & Net Losses:** Exactly 10 campaigns generated negative ROI (all YouTube and Facebook campaigns), accounting for **\,364,945.35** in cumulative net capital loss.
4. **Pause Recommendations:**
   - Pause YouTube - Search & YouTube - Influencer (\.1M spend, -\.46M loss) -- Caution: Check top-of-funnel assisted conversions.
   - Pause Facebook - Influencer & Facebook - Email (\.4M spend, -\.99M loss) -- Caution: Check retargeting pixel overlap with Instagram.
   - Restructure Website - Search (\.65M spend, +\.94M net profit, +2.26% ROI) -- Caution: Protect branded search terms against competitor conquesting.

---

## Phase 7 -- Budget Reallocation Scenario & Sensitivity Analysis (04_scenario.ipynb)
**Date:** 2026-10-03
**Status:** COMPLETE

### Deliverables
- notebooks/04_scenario.ipynb (13 parametric, execution-ready cells)
- data/processed/scenario_results.csv (Scenario comparison table)
- images/04_sensitivity_analysis.png (Dual sensitivity plot)

### Scenario Results Summary (20% Reallocation = \.47M Shift)
- **Conservative ($\eta = 0.60$):** Revenue Gained +\.7M, Lost -\.8M, Net Gain = **+\.90M** (+1.13%), Projected ROI = **7.35%** (+1.20 pp lift).
- **Base Case ($\eta = 0.75$):** Revenue Gained +\.7M, Lost -\.8M, Net Gain = **+\.84M** (+2.44%), Projected ROI = **8.75%** (+2.59 pp lift).
- **Optimistic ($\eta = 0.90$):** Revenue Gained +\.6M, Lost -\.8M, Net Gain = **+\.78M** (+3.76%), Projected ROI = **10.15%** (+3.99 pp lift).

### CEO Headline
> By reallocating 20% (\.5M) of ad spend away from underperforming YouTube and Facebook campaigns into high-return Instagram and Google Ads channels, we project a Base Case net revenue gain of +\.8M (+2.4%) and an overall ROI expansion from 6.16% to 8.75% without increasing our total budget.

---

## Phase 8 -- Power BI Dashboard Preparation (dashboard/)
**Date:** 2026-10-03
**Status:** COMPLETE

### Deliverables
- dashboard/data/fact_campaign.csv (200,000 rows model-ready fact table)
- dashboard/data/dim_date.csv (365 rows date dimension)
- dashboard/data/dim_channel.csv (6 rows channel dimension)
- dashboard/measures.dax (15 commented DAX measures with DIVIDE() ratio-of-sums)
- dashboard/BUILD_GUIDE.md (Step-by-step Power BI guide, ASCII canvas layout, color palette, visual configs)
- dashboard/CHECKLIST.md (Quality assurance checklist with exact validation targets)

### Summary of Data Files Exported
1. act_campaign.csv: 200,000 rows containing spend, impressions, clicks, conversions, revenue per campaign.
2. dim_date.csv: 365 rows covering 2021 date attributes.
3. dim_channel.csv: 6 unique channel attributes.
