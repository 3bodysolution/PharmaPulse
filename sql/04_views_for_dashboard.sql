/*
PharmaPulse Dashboard Views

These views are designed for dashboard reporting and use net_sales as the
main revenue metric. Each view aggregates source tables before joining them
to avoid row multiplication across sales, call, and engagement activity.
*/


-- Drop dashboard views first so this script can be rerun safely.
DROP VIEW IF EXISTS vw_product_margin_summary;
DROP VIEW IF EXISTS vw_campaign_effectiveness;
DROP VIEW IF EXISTS vw_hcp_engagement_summary;
DROP VIEW IF EXISTS vw_rep_performance;
DROP VIEW IF EXISTS vw_territory_revenue;


-- Territory revenue summary for geographic sales performance dashboards.
CREATE OR REPLACE VIEW vw_territory_revenue AS
WITH sales_by_territory AS (
    SELECT
        territory_id,
        SUM(net_sales) AS total_net_sales,
        SUM(units_sold) AS total_units_sold
    FROM sales
    GROUP BY territory_id
),
hcp_counts AS (
    SELECT
        territory_id,
        COUNT(DISTINCT hcp_id) AS number_of_hcps
    FROM hcps
    GROUP BY territory_id
),
rep_counts AS (
    SELECT
        territory_id,
        COUNT(DISTINCT rep_id) AS number_of_reps
    FROM medical_reps
    GROUP BY territory_id
)
SELECT
    t.territory_id,
    t.territory_name,
    t.region,
    t.state,
    t.city,
    t.market_potential,
    ROUND(COALESCE(sbt.total_net_sales, 0), 2) AS total_net_sales,
    COALESCE(sbt.total_units_sold, 0) AS total_units_sold,
    COALESCE(hc.number_of_hcps, 0) AS number_of_hcps,
    COALESCE(rc.number_of_reps, 0) AS number_of_reps,
    ROUND(
        COALESCE(sbt.total_net_sales, 0) / NULLIF(t.market_potential, 0) * 100,
        2
    ) AS revenue_vs_market_potential_pct
FROM territories t
LEFT JOIN sales_by_territory sbt
    ON t.territory_id = sbt.territory_id
LEFT JOIN hcp_counts hc
    ON t.territory_id = hc.territory_id
LEFT JOIN rep_counts rc
    ON t.territory_id = rc.territory_id;


-- Medical rep performance summary for sales target and call planning dashboards.
CREATE OR REPLACE VIEW vw_rep_performance AS
WITH sales_by_rep AS (
    SELECT
        rep_id,
        SUM(net_sales) AS total_net_sales
    FROM sales
    GROUP BY rep_id
),
calls_by_rep AS (
    SELECT
        rep_id,
        COUNT(*) AS total_calls,
        COUNT(DISTINCT hcp_id) AS unique_hcps_called
    FROM hcp_calls
    GROUP BY rep_id
)
SELECT
    mr.rep_id,
    mr.rep_name,
    mr.territory_id,
    t.territory_name,
    mr.region,
    mr.sales_target,
    ROUND(COALESCE(sbr.total_net_sales, 0), 2) AS total_net_sales,
    COALESCE(cbr.total_calls, 0) AS total_calls,
    COALESCE(cbr.unique_hcps_called, 0) AS unique_hcps_called,
    ROUND(
        COALESCE(sbr.total_net_sales, 0) / NULLIF(mr.sales_target, 0) * 100,
        2
    ) AS target_achievement_pct,
    ROUND(
        COALESCE(sbr.total_net_sales, 0) / NULLIF(cbr.total_calls, 0),
        2
    ) AS revenue_per_call
FROM medical_reps mr
JOIN territories t
    ON mr.territory_id = t.territory_id
LEFT JOIN sales_by_rep sbr
    ON mr.rep_id = sbr.rep_id
LEFT JOIN calls_by_rep cbr
    ON mr.rep_id = cbr.rep_id;


-- HCP engagement summary for HCP prioritization and call planning dashboards.
CREATE OR REPLACE VIEW vw_hcp_engagement_summary AS
WITH sales_by_hcp AS (
    SELECT
        hcp_id,
        SUM(net_sales) AS total_net_sales
    FROM sales
    GROUP BY hcp_id
),
calls_by_hcp AS (
    SELECT
        hcp_id,
        COUNT(*) AS total_calls,
        AVG(engagement_score) AS avg_engagement_score,
        MAX(call_date) AS last_call_date
    FROM hcp_calls
    GROUP BY hcp_id
),
call_reference AS (
    SELECT
        MAX(call_date) AS reference_date
    FROM hcp_calls
)
SELECT
    h.hcp_id,
    h.hcp_name,
    h.specialty,
    h.hcp_tier,
    h.territory_id,
    t.territory_name,
    h.patient_volume,
    ROUND(COALESCE(sbh.total_net_sales, 0), 2) AS total_net_sales,
    COALESCE(cbh.total_calls, 0) AS total_calls,
    ROUND(cbh.avg_engagement_score, 2) AS avg_engagement_score,
    cbh.last_call_date,
    CASE
        WHEN cbh.last_call_date IS NULL THEN NULL
        ELSE cr.reference_date - cbh.last_call_date
    END AS days_since_last_call
FROM hcps h
JOIN territories t
    ON h.territory_id = t.territory_id
CROSS JOIN call_reference cr
LEFT JOIN sales_by_hcp sbh
    ON h.hcp_id = sbh.hcp_id
LEFT JOIN calls_by_hcp cbh
    ON h.hcp_id = cbh.hcp_id;


-- Campaign engagement summary for campaign response and effectiveness indicators.
CREATE OR REPLACE VIEW vw_campaign_effectiveness AS
WITH engagement_by_campaign AS (
    SELECT
        campaign_id,
        COUNT(*) AS total_engagements,
        SUM(CASE WHEN opened THEN 1 ELSE 0 END) AS opens,
        SUM(CASE WHEN clicked THEN 1 ELSE 0 END) AS clicks,
        SUM(CASE WHEN attended THEN 1 ELSE 0 END) AS attendances,
        AVG(response_score) AS avg_response_score
    FROM campaign_engagement
    GROUP BY campaign_id
)
SELECT
    c.campaign_id,
    c.campaign_name,
    c.campaign_type,
    c.product_id,
    p.product_name,
    p.therapy_area,
    c.territory_id,
    t.territory_name,
    c.budget,
    COALESCE(ebc.total_engagements, 0) AS total_engagements,
    ROUND(
        COALESCE(ebc.opens, 0)::NUMERIC / NULLIF(ebc.total_engagements, 0) * 100,
        2
    ) AS open_rate_pct,
    ROUND(
        COALESCE(ebc.clicks, 0)::NUMERIC / NULLIF(ebc.total_engagements, 0) * 100,
        2
    ) AS click_rate_pct,
    ROUND(
        COALESCE(ebc.attendances, 0)::NUMERIC / NULLIF(ebc.total_engagements, 0) * 100,
        2
    ) AS attendance_rate_pct,
    ROUND(ebc.avg_response_score, 2) AS avg_response_score
FROM campaigns c
JOIN products p
    ON c.product_id = p.product_id
JOIN territories t
    ON c.territory_id = t.territory_id
LEFT JOIN engagement_by_campaign ebc
    ON c.campaign_id = ebc.campaign_id;


-- Product margin summary for portfolio and margin contribution dashboards.
CREATE OR REPLACE VIEW vw_product_margin_summary AS
WITH sales_by_product AS (
    SELECT
        product_id,
        SUM(units_sold) AS total_units_sold,
        SUM(net_sales) AS total_net_sales
    FROM sales
    GROUP BY product_id
)
SELECT
    p.product_id,
    p.product_name,
    p.therapy_area,
    p.brand_type,
    p.unit_price,
    p.margin_percent,
    COALESCE(sbp.total_units_sold, 0) AS total_units_sold,
    ROUND(COALESCE(sbp.total_net_sales, 0), 2) AS total_net_sales,
    ROUND(
        COALESCE(sbp.total_net_sales, 0) * p.margin_percent / 100,
        2
    ) AS estimated_margin_contribution
FROM products p
LEFT JOIN sales_by_product sbp
    ON p.product_id = sbp.product_id;
