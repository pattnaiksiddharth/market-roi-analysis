# Marketing ROI Dashboard – Streamlit

> A production-quality Streamlit dashboard that replicates the Marketing ROI Power BI report — with richer interactivity, cross-filtering, and budget what-if analysis.

---

## Quick Start

```bash
# 1. Navigate to the dashboard folder
cd dashboard

# 2. Create and activate virtual environment
py -3 -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac / Linux

# 3. Install dependencies (pinned)
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501**.

---

## Project Structure

```
dashboard/
├── app.py                   # Entry point (navigation, shared CSS, data loading)
├── pages/
│   ├── page_overview.py     # Page 1: Executive Overview
│   ├── page_funnel.py       # Page 2: Funnel & Acquisition
│   ├── page_channel.py      # Page 3: Channel Performance (Phase 2)
│   └── page_budget.py       # Page 4: Budget Scenario (Phase 2)
├── components/
│   ├── charts.py            # KPI cards, chart builders, insight blocks
│   └── filters.py           # Sidebar global filters
├── utils/
│   ├── data_loader.py       # Cached CSV loading + filter helpers
│   ├── measures.py          # All DAX measures as Python functions
│   └── theme.py             # Colour palette, Plotly template, channel roles
├── assets/
│   └── style.css            # Global CSS (dark navy theme)
├── data/
│   ├── fact_campaign.csv    # 200 000 rows of campaign data
│   ├── dim_channel.csv      # 6 channels + metadata
│   └── dim_date.csv         # Date dimension table
├── tests/
│   ├── conftest.py
│   └── test_measures.py     # pytest suite (15 tests)
├── .streamlit/
│   └── config.toml          # Theme + server config (iframe-ready)
└── requirements.txt         # Pinned dependencies
```

---

## Running Tests

```bash
# From the project root (parent of dashboard/)
dashboard\.venv\Scripts\python.exe -m pytest dashboard/tests/ -v
```

---

## Deploying to Streamlit Community Cloud

1. Push the `dashboard/` folder to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app.
3. Set:
   - **Repository**: your repo
   - **Branch**: `main`
   - **Main file path**: `dashboard/app.py`
4. Click **Deploy**.

### Embedding in a Website (iframe)

The `config.toml` already sets `enableCORS = false` and `headless = true`.  
Use this snippet on your site:

```html
<iframe
  src="https://your-app.streamlit.app/?embed=true"
  width="100%"
  height="900"
  frameborder="0"
  allow="fullscreen"
></iframe>
```

> **Note:** Streamlit Community Cloud free tier apps sleep after inactivity. For always-on embedding, consider Streamlit Cloud Teams or self-host with Docker.

---

## Pages

| # | Page | Key Visuals |
|---|------|-------------|
| 1 | Executive Overview | 8 KPI cards · Grouped bar (Spend vs Revenue by channel) · Diverging ROI bar · Area trend · Conversion donut |
| 2 | Funnel & Acquisition | ECharts funnel · 6 KPI cards · ROI by campaign type · Profit margin pie · Channel × campaign type pivot · Scatter |
| 3 | Channel Performance | Best/Worst KPI · Parameter-driven bar · AgGrid table · Revenue per Conversion bar *(Phase 2)* |
| 4 | Budget Scenario | 6 KPI cards · Sliders · Scenario bar chart · Channel table with Scenario Spend *(Phase 2)* |

---

## Colour Palette (from Power BI screenshots)

| Token | Hex | Use |
|-------|-----|-----|
| `bg_primary` | `#0a0e2e` | Page background |
| `bg_card` | `#1a2060` | Cards / panels |
| `accent_blue` | `#4f6cf7` | Primary highlight |
| `accent_purple` | `#8b5cf6` | Secondary accent |
| `accent_cyan` | `#06b6d4` | Chart line 2 |
| `positive` | `#22c55e` | Profit / gain |
| `negative` | `#ef4444` | Loss / drop |

---

## Dataset Notes

| Column | Type | Note |
|--------|------|-------|
| `campaign_id` | int | Unique row key |
| `date` | date | 2021-01-01 → 2021-12-31 |
| `channel` | str | Email, Facebook, Google Ads, Instagram, Website, YouTube |
| `campaign_type` | str | Display, Email, Influencer, Search, Social Media |
| `company` | str | Advertiser name |
| `target_audience` / `customer_segment` / `location` | str | Dimension slicers |
| `impressions` / `clicks` / `conversions` | int | Funnel metrics |
| `spend` / `revenue` | float | Core financial measures |

**No nulls, no duplicates.** 200 000 rows total.

**Column mapping vs DAX model:** All column names in the CSV match the DAX references exactly. No renames required.

**New Customers assumption (DAX file):** The local `measures.dax` file sets New Customers = Conversions × **0.60**, but the brief specifies **0.70**. The dashboard uses 0.70 as default (editable via sidebar) per the brief. Change in `utils/theme.py` or the sidebar widget.
