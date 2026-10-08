# Data Documentation & Data Dictionary

## Data Policy & Reproducibility Notice
To keep the GitHub repository lightweight and comply with git best practices, large regenerable CSV datasets are excluded from version control via `.gitignore`. 

### Excluded Files (`.gitignore`)
* `data/raw/raw_dataset.csv` (~27.2 MB) — Raw Kaggle marketing dataset.
* `data/raw/simulated_marketing.csv` (~42.4 MB) — Dataset after simulation pipeline execution.
* `data/processed/clean.csv` (~42.4 MB) — Full cleaned and feature-engineered dataset.
* `dashboard/data/fact_campaign.csv` (~22.9 MB) — Fact table formatted for Power BI.

### Committed Data Files
* `data/sample/clean_sample.csv` — First 1,000 rows of `clean.csv` for immediate schema inspection and light testing.
* `data/processed/summary_channel.csv` — Aggregated metrics by marketing channel.
* `data/processed/summary_campaign.csv` — Aggregated metrics by campaign type.
* `data/processed/summary_month.csv` — Aggregated metrics by year-month.
* `data/processed/scenario_results.csv` — Budget reallocation what-if simulation outputs.
* `data/processed/cleaning_log.csv` — Audit trail of data cleaning operations.
* `dashboard/data/dim_channel.csv` — Dimension table for marketing channels.
* `dashboard/data/dim_date.csv` — Dimension table for dates.

---

## Raw Data Source
* **Kaggle Dataset Name**: Marketing Campaign Dataset
* **Kaggle URL**: [https://www.kaggle.com/datasets/siddharthpattnaik/marketing-campaign-dataset](https://www.kaggle.com/datasets/siddharthpattnaik/marketing-campaign-dataset)
* **Exact Filename**: `raw_dataset.csv`
* **Download Instructions**: Download `raw_dataset.csv` from Kaggle and place it inside `data/raw/`.

---

## Data Dictionary (`data/processed/clean.csv`)

| Column Name | Data Type | Description | Source / Status |
| :--- | :--- | :--- | :--- |
| `campaign_id` | Integer | Unique identifier for each marketing campaign | **REAL** |
| `company` | String | Company/Brand name running the campaign | **REAL** |
| `campaign_type` | String | Type of campaign (e.g. Email, Social Media, Search, Display, Influencer) | **REAL** |
| `channel` | String | Marketing channel platform (e.g. Google Ads, Facebook, Instagram, YouTube, Email, Referral) | **REAL** |
| `target_audience` | String | Target demographic group (e.g. Men 18-24, Women 25-34) | **REAL** |
| `customer_segment` | String | Targeted customer segment (e.g. Tech Enthusiasts, Fashion Lovers) | **REAL** |
| `location` | String | Geographic location / city of campaign targeting | **REAL** |
| `language` | String | Language of the ad content | **REAL** |
| `date` | String (ISO) | Standardized campaign start date (`YYYY-MM-DD`) | **REAL** (Parsed) |
| `date_raw` | String | Original raw date string from source file | **REAL** |
| `year` | Integer | Extracted campaign start year | **REAL** |
| `year_month` | String | Formatted `YYYY-MM` string for monthly aggregation | **REAL** |
| `month` | Integer | Extracted month number (1–12) | **REAL** |
| `quarter` | Integer | Extracted financial quarter (1–4) | **REAL** |
| `week` | Integer | Extracted week of the year (1–52) | **REAL** |
| `duration_days` | Integer | Cleaned duration of the campaign in days | **REAL** |
| `duration_raw` | String | Raw duration string (e.g., "30 days") | **REAL** |
| `impressions` | Integer | Total number of ad impressions served | **REAL** |
| `clicks` | Integer | Total number of ad clicks generated | **REAL** |
| `ctr` | Float | Click-Through Rate (`clicks / impressions`) | **REAL** |
| `conversion_rate` | Float | Conversion Rate (`conversions / clicks`) | **REAL** |
| `conversions` | Integer | Total conversion transactions generated | **REAL** |
| `spend` | Float | Total ad spend in USD | **REAL** (Parsed) |
| `cpa` | Float | Cost Per Acquisition (`spend / conversions`) | **REAL** |
| `aov` | Float | Average Order Value in USD (Lognormal dist: $\mu=4.2, \sigma=0.5$, clipped $\$15-\$350$) | **SIMULATED** |
| `revenue` | Float | Gross revenue generated in USD (`conversions * aov * channel_multiplier`) | **SIMULATED** |
| `roi_computed` | Float | Campaign-level ROI ratio (`(revenue - spend) / spend`) | **SIMULATED** |
| `engagement_score` | Integer | Campaign engagement metric score (1–10) | **REAL** |
| `acquisition_cost_raw` | String | Original raw cost string with currency symbols | **REAL** |

---

## How to Reproduce Full Datasets
To regenerate all processed and model-ready files from scratch:
1. Download `raw_dataset.csv` into `data/raw/`.
2. Run `notebooks/00_simulation.ipynb` $\rightarrow$ generates `data/raw/simulated_marketing.csv`.
3. Run `notebooks/01_cleaning.ipynb` $\rightarrow$ generates `data/processed/clean.csv` and `data/processed/cleaning_log.csv`.
4. Run `notebooks/02_metrics.ipynb` $\rightarrow$ generates `data/processed/summary_channel.csv`, `summary_campaign.csv`, `summary_month.csv`.
5. Run `notebooks/03_analysis.ipynb` $\rightarrow$ generates visual charts in `images/`.
6. Run `notebooks/04_scenario.ipynb` $\rightarrow$ generates `data/processed/scenario_results.csv` and `dashboard/data/fact_campaign.csv`.
