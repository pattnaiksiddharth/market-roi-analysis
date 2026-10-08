# Power BI Validation & Quality Assurance Checklist

**Purpose:** Validate that all Power BI measures, totals, and visual aggregations match the Python baseline data in `data/processed/summary_channel.csv` exactly.

---

## 1. Portfolio Level Verification

Compare your Power BI top-level KPI Card values against these exact baseline figures:

| Metric Name | Power BI Card Target | Python Baseline Target | Status (`PASS` / `FAIL`) |
| :--- | :---: | :---: | :---: |
| **Total Spend** | `$2,500,878,608.00` ($2.50B) | `$2,500,878,608.00` | [ ] PASS |
| **Total Revenue** | `$2,654,825,117.12` ($2.65B) | `$2,654,825,117.12` | [ ] PASS |
| **Total Net Profit** | `+$153,946,509.12` ($153.9M) | `+$153,946,509.12` | [ ] PASS |
| **Overall ROI** | **`+6.16%`** | **`+6.16%`** | [ ] PASS |
| **Overall ROAS** | **`1.06`** | **`1.0616`** | [ ] PASS |
| **Average CAC** | **`$473.40`** | **`$473.40`** | [ ] PASS |
| **Total Conversions** | `8,794,765` | `8,794,765` | [ ] PASS |
| **Total Clicks** | `109,958,406` | `109,958,406` | [ ] PASS |
| **Total Impressions** | `1,099,460,746` | `1,099,460,746` | [ ] PASS |

---

## 2. Channel Level Verification Matrix

Verify that filtered channel visuals match these exact values from `data/processed/summary_channel.csv`:

| Channel Name | Total Spend ($) | Total Revenue ($) | ROI (%) | ROAS | CAC ($) | CVR (%) | Spend Share (%) | Rev Share (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Instagram** | $417,124,850.00 | $612,316,844.98 | **+46.79%** | 1.47 | $475.21 | 7.99% | 16.68% | 23.06% |
| **Google Ads** | $418,912,314.00 | $564,394,027.79 | **+34.73%** | 1.35 | $475.37 | 8.01% | 16.75% | 21.26% |
| **Email** | $420,874,104.00 | $495,760,405.48 | **+17.79%** | 1.18 | $472.23 | 8.03% | 16.83% | 18.67% |
| **Website** | $416,593,500.00 | $429,344,944.22 | **+3.06%** | 1.03 | $469.88 | 8.02% | 16.66% | 16.17% |
| **Facebook** | $410,595,258.00 | $317,142,246.00 | **-22.76%** | 0.77 | $473.14 | 8.02% | 16.42% | 11.95% |
| **YouTube** | $416,778,582.00 | $235,866,648.65 | **-43.41%** | 0.57 | $474.59 | 7.98% | 16.67% | 8.88% |

---

## 3. Data Integrity & DAX Auditing Checklist

- [ ] **Ratio-of-Sums Audit:** Confirm all DAX ratio measures (`ROI`, `ROAS`, `CTR`, `CVR`, `CAC`, `CPA`) use `DIVIDE([Total Numerator], [Total Denominator], 0)`.
- [ ] **No Averaging of Ratios:** Verify that no visual uses implicit averaging (`AVERAGE(fact_campaign[roi])`).
- [ ] **Relationship Cardinality:** Confirm relationships are $1:*$ (1-to-many) from `dim_date` and `dim_channel` to `fact_campaign`.
- [ ] **Filter Context:** Selecting a channel slicer (e.g. `Instagram`) updates all KPI cards to Instagram totals ($417.1M spend, $612.3M revenue, +46.8% ROI).
- [ ] **Conditional Formatting:** Verify that Facebook (-22.8%) and YouTube (-43.4%) ROI bars are colored Crimson Red (`#E74C3C`), while positive ROI channels are colored Emerald Green (`#2ECC71`).
