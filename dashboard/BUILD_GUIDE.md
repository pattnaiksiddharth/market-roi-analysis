# Power BI Dashboard Build Guide (Step-by-Step for Beginners)

**Project:** Marketing Campaign Performance & ROI Analysis  
**Goal:** Build an interactive executive Power BI dashboard to answer: *"Which campaigns and channels work, where should we invest more, and which campaigns should we stop?"*

---

## Step 1: Import Data into Power BI Desktop

1. Open **Power BI Desktop**.
2. Click **Get Data** > **Text/CSV**.
3. Navigate to the project folder: `dashboard/data/`.
4. Import the following 3 CSV files one by one:
   - `fact_campaign.csv`
   - `dim_date.csv`
   - `dim_channel.csv`
5. Click **Load** for each table.

---

## Step 2: Set Up Model Relationships

1. Go to the **Model View** tab (icon on the far left sidebar).
2. Verify / Create the following **1-to-Many ($1 : *$) single-direction** relationships:
   - Drag `dim_date[date]` $\rightarrow$ `fact_campaign[date]`
   - Drag `dim_channel[channel]` $\rightarrow$ `fact_campaign[channel]`

```
+------------------+             +--------------------+             +-------------------+
|    dim_date      |             |   fact_campaign    |             |    dim_channel    |
+------------------+             +--------------------+             +-------------------+
| date (PK)        | 1 --------* | date (FK)          | * -------- 1| channel (PK)      |
| year             |             | campaign_id        |             | channel_category  |
| month_name       |             | channel (FK)       |             | is_digital        |
| quarter          |             | spend              |             +-------------------+
+------------------+             | revenue            |
                                 | conversions        |
                                 +--------------------+
```

---

## Step 3: Create DAX Measures

1. In the **Report View**, right-click `fact_campaign` in the Data pane and select **New Measure**.
2. Open `dashboard/measures.dax` in any text editor and copy-paste each measure:
   - `Total Spend`, `Total Revenue`, `Total Net Profit`
   - `CTR`, `CVR`, `CPC`, `CPA`, `CAC`, `ROAS`, `ROI`
   - `Spend Share %`, `Revenue Share %`

---

## Step 4: Dashboard Canvas Layout & Visuals

### ASCII Dashboard Canvas Sketch (16:9 Standard Page)

```
+---------------------------------------------------------------------------------------------------+
|  [LOGO] MARKETING CAMPAIGN PERFORMANCE & ROI DASHBOARD                              [Date Slicer] |
+---------------------------------------------------------------------------------------------------+
|  +----------------+  +----------------+  +----------------+  +----------------+  [Channel     |
|  | TOTAL SPEND    |  | TOTAL REVENUE  |  | OVERALL ROI    |  | AVERAGE CAC    |   Slicer]     |
|  | $2.50 Billion  |  | $2.65 Billion  |  | +6.16%         |  | $473.40        |               |
|  +----------------+  +----------------+  +----------------+  +----------------+  +------------+
+----------------------------------------------------------------------------------+               |
|  VISUAL 1: Spend Share vs. Revenue Share per Channel (Clustered Bar Chart)       |  +------------+
|  "Instagram Delivers 23.1% Revenue on 16.7% Spend; YouTube Consumes 16.7% Spend" |  | TOP/BOTTOM  |
|                                                                                  |  | CAMPAIGNS   |
+----------------------------------------------------------------------------------+  | TABLE      |
|  VISUAL 2: Channel ROI (%) Ranking (Sorted Horizontal Bar)                       |  |            |
|  "Instagram (+46.8%) and Google (+34.7%) Lead; YouTube (-43.4%) Destroys Capital"|  | Instagram  |
|                                                                                  |  | Facebook   |
+----------------------------------------------------------------------------------+  | YouTube    |
|  VISUAL 3: Monthly Spend vs. Revenue Trend (Line & Clustered Column Chart)       |  | ...        |
|  "Monthly Performance Remains Stable Around +6.2% Portfolio ROI"                 |  +------------+
+---------------------------------------------------------------------------------------------------+
```

---

## Step 5: Visual Configurations & Color Palette

### Recommended Palette
- **Primary / Positive (Green):** `#2ECC71` (Emerald Green)
- **Negative / Alert (Red):** `#E74C3C` (Crimson Red)
- **Dark Neutral (Headers/Bars):** `#34495E` (Navy Slate)
- **Background:** `#F8F9FA` (Off-white)

### Visual 1: KPI Cards (Top Header Strip)
- Add 4 **Card** visuals across the top:
  1. `Total Spend` (Display units: Millions/Billions, formatted `$#,##0`)
  2. `Total Revenue` (Formatted `$#,##0`)
  3. `ROI` (Formatted `+0.00%`)
  4. `CAC` (Formatted `$#,##0.00`)

### Visual 2: Headline Bar Chart (Spend Share vs. Revenue Share)
- **Type:** Clustered Bar Chart
- **Y-Axis:** `dim_channel[channel]`
- **X-Axis:** `[Spend Share %]`, `[Revenue Share %]`
- **Insight Title:** *"Instagram Delivers 23.1% Revenue on 16.7% Spend; YouTube Consumes 16.7% Spend for 8.9% Revenue"*

### Visual 3: Channel ROI Ranking (Conditional Formatting)
- **Type:** Clustered Bar Chart (Sorted Descending by `[ROI]`)
- **Y-Axis:** `dim_channel[channel]`
- **X-Axis:** `[ROI]`
- **Conditional Color Rule:**
  - Go to **Visual Format** > **Bars** > **Fx (Conditional Formatting)**.
  - Format style: **Rules** based on field `[ROI]`.
  - Rule 1: If value `< 0` $\rightarrow$ `#E74C3C` (Crimson Red).
  - Rule 2: If value `>= 0` $\rightarrow$ `#2ECC71` (Emerald Green).
- **Insight Title:** *"Instagram (+46.8%) and Google Ads (+34.7%) Lead Returns; YouTube (-43.4%) and Facebook (-22.8%) Lose Money"*

### Visual 4: Monthly Spend vs. Revenue Trend
- **Type:** Line and Clustered Column Chart
- **X-Axis:** `dim_date[year_month]`
- **Column Y-Axis:** `[Total Spend]`, `[Total Revenue]`
- **Line Y-Axis:** `[ROI]`
- **Insight Title:** *"Monthly Spend & Revenue Track Consistently with Stable Portfolio ROI (+6.2%)"*

---

## Step 6: Export Screenshots for Portfolio

1. In Power BI Desktop, resize the window to full 1920x1080 resolution.
2. Capture screenshots using **Windows Snipping Tool** (`Win + Shift + S`) or **File > Export > Export to PDF / Image**.
3. Save screenshots into the repository `images/` directory:
   - `images/05_powerbi_dashboard_overview.png`
   - `images/05_powerbi_channel_deepdive.png`
