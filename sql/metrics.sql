-- ============================================================
-- metrics.sql
-- Equivalent GROUP BY queries for the 02_metrics.ipynb notebook
-- Dialect : PostgreSQL (also compatible with SQLite with minor
--           adjustments noted inline)
-- Author  : Portfolio Project — Marketing Campaign ROI Analysis
-- Note    : All revenue figures are SIMULATED. See README.md.
--
-- ASSUMPTION: new_customer_share = 0.60 (60% of conversions
--             are first-time customers — no new_customer column
--             exists in the dataset, so this is approximated)
-- ASSUMPTION: gross_margin = 0.40 (40% e-commerce gross margin)
-- ASSUMPTION: avg_orders_per_customer = 2.5
-- ASSUMPTION: avg_months_active = 12
-- ============================================================


-- ============================================================
-- 0. Grand Totals (sanity anchor — all group-bys must reconcile)
-- ============================================================
SELECT
    COUNT(*)                             AS n_campaigns,
    SUM(impressions)                     AS total_impressions,
    SUM(clicks)                          AS total_clicks,
    SUM(conversions)                     AS total_conversions,
    SUM(spend)                           AS total_spend,
    SUM(revenue)                         AS total_revenue,
    -- ROI: ratio of SUMS (correct) — never AVG(roi_computed)
    ROUND(
        (SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0), 4
    )                                    AS portfolio_roi,
    ROUND(
        SUM(revenue) / NULLIF(SUM(spend), 0), 4
    )                                    AS portfolio_roas
FROM clean;


-- ============================================================
-- 1. Summary by Channel
--    Business question: which channel should we invest more in
--    and which should we stop?
-- ============================================================
SELECT
    channel,
    COUNT(*)                                                AS n_campaigns,
    SUM(impressions)                                        AS impressions,
    SUM(clicks)                                             AS clicks,
    SUM(conversions)                                        AS conversions,
    ROUND(SUM(spend),   2)                                  AS spend,
    ROUND(SUM(revenue), 2)                                  AS revenue,

    -- CTR = clicks / impressions  (all ratios from SUMS, never from AVG of row-level)
    ROUND(SUM(clicks)::NUMERIC / NULLIF(SUM(impressions), 0), 4)      AS ctr,

    -- CVR = conversions / clicks
    ROUND(SUM(conversions)::NUMERIC / NULLIF(SUM(clicks), 0), 4)      AS cvr,

    -- CPC = spend / clicks
    ROUND(SUM(spend) / NULLIF(SUM(clicks), 0), 2)                     AS cpc,

    -- CPA = spend / conversions
    ROUND(SUM(spend) / NULLIF(SUM(conversions), 0), 2)                AS cpa,

    -- CAC = spend / new_customers  (assumption: 60% of conversions are new)
    ROUND(SUM(spend) / NULLIF(SUM(conversions) * 0.60, 0), 2)        AS cac,

    -- ROAS = revenue / spend
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 4)                    AS roas,

    -- ROI = (revenue - spend) / spend  — THE CORRECT AGGREGATE METHOD
    ROUND((SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0), 4)    AS roi,

    -- ROI as percentage
    ROUND(
        (SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0) * 100, 2
    )                                                                  AS roi_pct,

    -- Gross Profit = revenue * margin (40%)
    ROUND(SUM(revenue) * 0.40, 2)                                     AS gross_profit,

    -- Effective AOV = revenue / conversions
    ROUND(SUM(revenue) / NULLIF(SUM(conversions), 0), 2)             AS effective_aov,

    -- LTV = effective_AOV * avg_orders * margin
    -- = (revenue/conversions) * 2.5 * 0.40
    ROUND(
        (SUM(revenue) / NULLIF(SUM(conversions), 0)) * 2.5 * 0.40, 2
    )                                                                  AS ltv,

    -- LTV:CAC ratio
    ROUND(
        ((SUM(revenue) / NULLIF(SUM(conversions), 0)) * 2.5 * 0.40)
        /
        NULLIF(SUM(spend) / NULLIF(SUM(conversions) * 0.60, 0), 0),
        2
    )                                                                  AS ltv_cac_ratio,

    -- Payback months = CAC / (monthly_revenue_per_cust * margin)
    -- monthly_rev = effective_aov / 12 months
    ROUND(
        (SUM(spend) / NULLIF(SUM(conversions) * 0.60, 0))
        /
        NULLIF(
            (SUM(revenue) / NULLIF(SUM(conversions), 0) / 12.0) * 0.40,
            0
        ),
        1
    )                                                                  AS payback_months

FROM clean
GROUP BY channel
ORDER BY roi_pct DESC;


-- ============================================================
-- 2. Summary by Campaign Type
-- ============================================================
SELECT
    campaign_type,
    COUNT(*)                                                           AS n_campaigns,
    ROUND(SUM(spend),   2)                                             AS spend,
    ROUND(SUM(revenue), 2)                                             AS revenue,
    ROUND(SUM(clicks)::NUMERIC / NULLIF(SUM(impressions), 0), 4)      AS ctr,
    ROUND(SUM(conversions)::NUMERIC / NULLIF(SUM(clicks), 0), 4)      AS cvr,
    ROUND(SUM(spend) / NULLIF(SUM(conversions), 0), 2)                AS cpa,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 4)                    AS roas,
    ROUND(
        (SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0) * 100, 2
    )                                                                  AS roi_pct,
    ROUND(
        (SUM(revenue) / NULLIF(SUM(conversions), 0)) * 2.5 * 0.40, 2
    )                                                                  AS ltv,
    ROUND(
        ((SUM(revenue) / NULLIF(SUM(conversions), 0)) * 2.5 * 0.40)
        /
        NULLIF(SUM(spend) / NULLIF(SUM(conversions) * 0.60, 0), 0),
        2
    )                                                                  AS ltv_cac_ratio
FROM clean
GROUP BY campaign_type
ORDER BY roi_pct DESC;


-- ============================================================
-- 3. Summary by Month
--    For seasonality trends and budget pacing analysis
-- ============================================================
SELECT
    year_month,
    COUNT(*)                                                           AS n_campaigns,
    ROUND(SUM(spend),   2)                                             AS spend,
    ROUND(SUM(revenue), 2)                                             AS revenue,
    SUM(impressions)                                                   AS impressions,
    SUM(clicks)                                                        AS clicks,
    SUM(conversions)                                                   AS conversions,
    ROUND(SUM(clicks)::NUMERIC / NULLIF(SUM(impressions), 0), 4)      AS ctr,
    ROUND(SUM(conversions)::NUMERIC / NULLIF(SUM(clicks), 0), 4)      AS cvr,
    ROUND(SUM(spend) / NULLIF(SUM(conversions), 0), 2)                AS cpa,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 4)                    AS roas,
    ROUND(
        (SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0) * 100, 2
    )                                                                  AS roi_pct
FROM clean
GROUP BY year_month
ORDER BY year_month;


-- ============================================================
-- 4. Channel x Campaign Type cross-tab
--    Identifies which channel+type combinations win or lose
-- ============================================================
SELECT
    channel,
    campaign_type,
    COUNT(*)                                                           AS n_campaigns,
    ROUND(SUM(spend),   2)                                             AS spend,
    ROUND(SUM(revenue), 2)                                             AS revenue,
    ROUND(
        (SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0) * 100, 2
    )                                                                  AS roi_pct,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 4)                    AS roas,
    ROUND(SUM(spend) / NULLIF(SUM(conversions), 0), 2)                AS cpa
FROM clean
GROUP BY channel, campaign_type
ORDER BY roi_pct DESC;


-- ============================================================
-- 5. Channel x Month — for trend analysis by channel
-- ============================================================
SELECT
    channel,
    year_month,
    COUNT(*)                                                           AS n_campaigns,
    ROUND(SUM(spend),   2)                                             AS spend,
    ROUND(SUM(revenue), 2)                                             AS revenue,
    ROUND(
        (SUM(revenue) - SUM(spend)) / NULLIF(SUM(spend), 0) * 100, 2
    )                                                                  AS roi_pct,
    ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 4)                    AS roas
FROM clean
GROUP BY channel, year_month
ORDER BY channel, year_month;


-- ============================================================
-- NOTE FOR SQLITE USERS:
--   Replace ::NUMERIC with CAST(... AS REAL)
--   e.g. SUM(clicks)::NUMERIC  -->  CAST(SUM(clicks) AS REAL)
--   Everything else is compatible.
-- ============================================================
