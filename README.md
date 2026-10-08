# Marketing Campaign Performance & ROI Analysis

> **Portfolio project** for US/UK remote Data Analyst / Business Analyst roles.
> Demonstrates end-to-end analytical workflow: data audit → enrichment → EDA → ROI analysis → recommendation.

---

## Business Question

> *"Which campaigns and channels actually work? Where should we invest more, and which campaign should we stop?"*

---

## Repository Structure

```
marketing-campaign-roi/
├── data/
│   ├── raw/
│   │   ├── raw_dataset.csv          # Original, never modified (200k rows x 16 cols)
│   │   └── simulated_marketing.csv  # Enriched: 29 columns (derived + simulated)
│   └── processed/                   # Cleaned outputs from Phase 1 cleaning notebook
├── notebooks/
│   ├── 00_simulation.ipynb          # Simulation layer (this phase)
│   └── 01_data_cleaning.ipynb       # Phase 1: cleaning & validation
├── sql/                             # Ad-hoc SQL queries
├── dashboard/                       # Interactive dashboard (Phase 5)
├── images/                          # All saved charts (PNG, dpi=150)
├── docs/
│   └── PROGRESS.md                  # Phase-by-phase progress log
└── README.md
```

---

## Dataset & Assumptions

### Source

| Item | Detail |
|------|--------|
| Raw file | `data/raw/raw_dataset.csv` |
| Rows | 200,000 |
| Columns | 16 |
| Date range | 01-Jan-2021 to 31-Dec-2021 (full calendar year, all 365 days) |
| Channels | Email, Google Ads, YouTube, Instagram, Website, Facebook (~33k rows each) |
| Campaign types | Display, Email, Influencer, Search, Social Media (~40k each) |
| Companies | Innovate Industries, NexGen Systems, Alpha Innovations, DataTech Solutions, TechCorp |

### What is real (from raw_dataset.csv)

| Column | Type | Range / Values |
|--------|------|----------------|
| Campaign_ID | int | 1 – 200,000 |
| Company | str | 5 companies |
| Campaign_Type | str | Display, Email, Influencer, Search, Social Media |
| Target_Audience | str | Men 18-24, Men 25-34, Women 25-34, Women 35-44, All Ages |
| Duration | str | 15 / 30 / 45 / 60 days |
| Channel_Used | str | Email, Facebook, Google Ads, Instagram, Website, YouTube |
| Conversion_Rate | float | 0.01 – 0.15 (1% to 15%) |
| Acquisition_Cost | str | $5,000 – $20,000 (total campaign budget per row, currency string) |
| ROI | float | 2.0 – 8.0 — NOTE: uniform random noise, flat ~5.0 for all channels. NOT used for analysis. |
| Location | str | Chicago, Houston, Los Angeles, Miami, New York |
| Language | str | English, French, German, Mandarin, Spanish |
| Clicks | int | 100 – 1,000 |
| Impressions | int | 1,000 – 10,000 |
| Engagement_Score | int | 1 – 10 |
| Customer_Segment | str | Fashionistas, Foodies, Health & Wellness, Outdoor Adventurers, Tech Enthusiasts |
| Date | str | DD-MM-YYYY spanning 01-01-2021 to 31-12-2021 |

### What is derived (arithmetic from raw columns — no simulation)

| Column | Formula | Rationale |
|--------|---------|-----------|
| Acquisition_Cost_num | Strip $/, cast float | Enable arithmetic on spend |
| Date_dt | Parse DD-MM-YYYY | Enable time-series analysis |
| Duration_days | Extract integer from "N days" | Enable duration-based cuts |
| Spend | = Acquisition_Cost_num | Total campaign budget per row |
| Conversions | max(1, round(Clicks x Conversion_Rate)) | Absolute conversion count |
| CPA | Spend / Conversions | Effective cost per acquisition |
| CTR | Clicks / Impressions | Click-through rate |
| Month / Quarter / Week | From Date_dt | Seasonality analysis |
| ROI_computed | (Revenue - Spend) / Spend | True ROI using simulated Revenue |

### What is simulated (labelled clearly in every chart)

**Only AOV (Average Order Value) is simulated.** Revenue = Conversions x AOV.

AOV is drawn from a Lognormal distribution stratified by channel (seed=42).
Lognormal is the standard distribution for order-value simulation: always positive,
right-skewed (a minority of high-value orders pulls mean above median — matching real e-commerce).

#### Simulation parameters and justification

| Channel | mu (log-scale) | sigma | Mean AOV | Industry rationale |
|---------|---------------|-------|----------|--------------------|
| Instagram | 5.99 | 0.30 | ~$418 | Visual discovery drives premium purchases; highest intent among social channels (Meta Business, 2022) |
| Google Ads | 5.87 | 0.40 | ~$384 | Search intent = highest purchase readiness; strong AOV supported by WordStream benchmarks |
| Email | 5.75 | 0.35 | ~$334 | Owned channel reaches warm/existing audience; high AOV from retargeting (HubSpot, 2022) |
| Website | 5.60 | 0.38 | ~$291 | Organic visitors show moderate intent; mix of returning and new visitors |
| Facebook | 5.29 | 0.45 | ~$219 | Broad targeting lowers buyer intent; declining organic reach (eMarketer, 2021) |
| YouTube | 4.96 | 0.50 | ~$161 | Top-of-funnel channel; high reach, low direct conversion value under last-click attribution |

#### Resulting channel ROI (aggregate, recomputed from summed totals)

| Channel | Agg ROI | Business verdict |
|---------|---------|-----------------|
| Instagram | +46.8% | Scale up |
| Google Ads | +34.7% | Invest more |
| Email | +17.8% | Maintain |
| Website | +3.1% | Monitor |
| Facebook | -22.8% | Reduce budget |
| YouTube | -43.4% | Stop / repurpose |

**Overall portfolio ROI: +6.2%** (profitable but efficiency is uneven across channels)

### Important caveats

1. All revenue figures are simulated. Absolute dollar amounts are illustrative, not real.
2. Spend = Acquisition_Cost (total budget) understates true media spend — non-converting impressions and clicks are not separated.
3. Attribution is last-click. YouTube's top-of-funnel assist value is invisible in this model.
4. Every chart carries the label: "Simulated Revenue — Portfolio Project".
5. When filtering to small segments, always check sample size before drawing conclusions.

---

## Global Methodology Rules

1. Python: pandas, matplotlib, seaborn. random_state=42 / np.random.seed(42) everywhere.
2. Every code cell block preceded by a markdown cell explaining what and why. Every decision (drop/cap/impute) logged in markdown.
3. Aggregate ratios recomputed from summed totals. NEVER average row-level ratios.
4. Every division guarded against zero (np.where pattern).
5. Charts saved as PNG dpi=150 to /images/ with titles, axis labels, units.
6. After each phase: print Findings summary, append to docs/PROGRESS.md, stop and wait.
7. Metrics that can mislead are flagged explicitly (tiny spend, last-click, small samples).
8. No invented facts. Everything simulated is labelled.

---

## Phases

| Phase | Notebook | Status |
|-------|----------|--------|
| 0 — Simulation Layer | notebooks/00_simulation.ipynb | COMPLETE |
| 1 — Data Cleaning & Audit | notebooks/01_data_cleaning.ipynb | Pending |
| 2 — Exploratory Data Analysis | notebooks/02_eda.ipynb | Pending |
| 3 — ROI & Channel Analysis | notebooks/03_roi_channel_analysis.ipynb | Pending |
| 4 — Recommendations | notebooks/04_recommendations.ipynb | Pending |
| 5 — Dashboard | dashboard/app.py | Pending |

---

## How to Run

```bash
pip install pandas numpy matplotlib seaborn jupyter plotly
jupyter notebook notebooks/
```

*Last updated: Phase 0 — Simulation layer complete.*
