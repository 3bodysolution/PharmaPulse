/*
PharmaPulse SQL Analysis Queries

Phase 6 is analysis-only:
- No views are created.
- No schema changes are made.
- No data is inserted, updated, or deleted.

These queries use net_sales as the main revenue metric.
*/


/*
Query 01: Total Net Sales Revenue
Business question: What is the total net sales revenue across the full dataset?
Why it matters: This gives the executive topline revenue number for PharmaPulse.
*/
SELECT
    ROUND(SUM(net_sales), 2) AS total_net_sales
FROM sales;

-- Interpret the output as the total realized revenue after discounts.


/*
Query 02: Revenue by Territory
Business question: Which territories generate the most net sales revenue?
Why it matters: Territory performance helps sales leaders focus coaching, resourcing, and growth plans.
*/
SELECT
    t.territory_id,
    t.territory_name,
    t.region,
    t.city,
    ROUND(SUM(s.net_sales), 2) AS total_net_sales,
    COUNT(DISTINCT s.hcp_id) AS buying_hcps,
    COUNT(*) AS sales_transactions
FROM sales s
JOIN territories t
    ON s.territory_id = t.territory_id
GROUP BY
    t.territory_id,
    t.territory_name,
    t.region,
    t.city
ORDER BY total_net_sales DESC;

-- Higher revenue territories may be strong markets, while lower revenue territories may need deeper diagnosis.


/*
Query 03: Revenue by Product Therapy Area
Business question: Which therapy areas contribute the most revenue?
Why it matters: Therapy-area performance supports portfolio planning and brand investment decisions.
*/
SELECT
    p.therapy_area,
    ROUND(SUM(s.net_sales), 2) AS total_net_sales,
    COUNT(DISTINCT s.product_id) AS products_sold,
    COUNT(DISTINCT s.hcp_id) AS unique_hcps
FROM sales s
JOIN products p
    ON s.product_id = p.product_id
GROUP BY p.therapy_area
ORDER BY total_net_sales DESC;

-- Use this to compare revenue concentration across therapy areas.


/*
Query 04: Top 10 HCPs by Revenue
Business question: Which HCPs generate the highest net sales?
Why it matters: High-value HCPs are important for account planning and relationship management.
*/
SELECT
    h.hcp_id,
    h.hcp_name,
    h.specialty,
    h.hcp_tier,
    t.territory_name,
    ROUND(SUM(s.net_sales), 2) AS total_net_sales,
    COUNT(*) AS sales_transactions
FROM sales s
JOIN hcps h
    ON s.hcp_id = h.hcp_id
JOIN territories t
    ON h.territory_id = t.territory_id
GROUP BY
    h.hcp_id,
    h.hcp_name,
    h.specialty,
    h.hcp_tier,
    t.territory_name
ORDER BY total_net_sales DESC
LIMIT 10;

-- These HCPs are the strongest current revenue contributors in the dataset.


/*
Query 05: Medical Rep Target Achievement
Business question: Which medical reps are meeting or missing their sales targets?
Why it matters: This supports field performance coaching and target tracking.
*/
SELECT
    mr.rep_id,
    mr.rep_name,
    mr.manager_name,
    t.territory_name,
    ROUND(mr.sales_target, 2) AS sales_target,
    ROUND(COALESCE(SUM(s.net_sales), 0), 2) AS total_net_sales,
    ROUND(COALESCE(SUM(s.net_sales), 0) / NULLIF(mr.sales_target, 0) * 100, 2)
        AS target_achievement_percent,
    CASE
        WHEN COALESCE(SUM(s.net_sales), 0) >= mr.sales_target THEN 'At or above target'
        ELSE 'Below target'
    END AS target_status
FROM medical_reps mr
JOIN territories t
    ON mr.territory_id = t.territory_id
LEFT JOIN sales s
    ON mr.rep_id = s.rep_id
GROUP BY
    mr.rep_id,
    mr.rep_name,
    mr.manager_name,
    t.territory_name,
    mr.sales_target
ORDER BY target_achievement_percent DESC;

-- Compare target_achievement_percent across reps to identify coaching and recognition opportunities.


/*
Query 06: Revenue per HCP Call by Rep
Business question: How much revenue is associated with each rep's HCP call activity?
Why it matters: Revenue per call is a practical efficiency metric for call planning.
*/
WITH rep_calls AS (
    SELECT
        rep_id,
        COUNT(*) AS total_calls
    FROM hcp_calls
    WHERE call_status = 'Completed'
    GROUP BY rep_id
),
rep_sales AS (
    SELECT
        rep_id,
        SUM(net_sales) AS total_net_sales
    FROM sales
    GROUP BY rep_id
)
SELECT
    mr.rep_id,
    mr.rep_name,
    t.territory_name,
    COALESCE(rc.total_calls, 0) AS completed_calls,
    ROUND(COALESCE(rs.total_net_sales, 0), 2) AS total_net_sales,
    ROUND(COALESCE(rs.total_net_sales, 0) / NULLIF(rc.total_calls, 0), 2)
        AS revenue_per_completed_call
FROM medical_reps mr
JOIN territories t
    ON mr.territory_id = t.territory_id
LEFT JOIN rep_calls rc
    ON mr.rep_id = rc.rep_id
LEFT JOIN rep_sales rs
    ON mr.rep_id = rs.rep_id
ORDER BY revenue_per_completed_call DESC NULLS LAST;

-- Higher revenue per call can signal stronger targeting, better conversion, or stronger territory potential.


/*
Query 07: HCP Engagement Score Summary
Business question: How engaged are HCPs by tier and specialty?
Why it matters: Engagement patterns help teams prioritize outreach and channel strategy.
*/
SELECT
    h.hcp_tier,
    h.specialty,
    COUNT(hc.call_id) AS total_calls,
    ROUND(AVG(hc.engagement_score), 2) AS avg_engagement_score,
    MIN(hc.engagement_score) AS min_engagement_score,
    MAX(hc.engagement_score) AS max_engagement_score
FROM hcps h
LEFT JOIN hcp_calls hc
    ON h.hcp_id = hc.hcp_id
GROUP BY
    h.hcp_tier,
    h.specialty
ORDER BY
    h.hcp_tier,
    avg_engagement_score DESC;

-- Look for tiers or specialties with low engagement that may need different call planning.


/*
Query 08: High-Engagement but Low-Sales HCPs
Business question: Which HCPs are engaged but not yet generating high sales?
Why it matters: These HCPs may be good candidates for focused follow-up or next-best-action planning.
*/
WITH hcp_metrics AS (
    SELECT
        h.hcp_id,
        h.hcp_name,
        h.specialty,
        h.hcp_tier,
        t.territory_name,
        ROUND(ca.avg_engagement_score, 2) AS avg_engagement_score,
        COALESCE(ca.total_calls, 0) AS total_calls,
        ROUND(COALESCE(sa.total_net_sales, 0), 2) AS total_net_sales
    FROM hcps h
    JOIN territories t
        ON h.territory_id = t.territory_id
    LEFT JOIN (
        SELECT
            hcp_id,
            AVG(engagement_score) AS avg_engagement_score,
            COUNT(*) AS total_calls
        FROM hcp_calls
        GROUP BY hcp_id
    ) ca
        ON h.hcp_id = ca.hcp_id
    LEFT JOIN (
        SELECT
            hcp_id,
            SUM(net_sales) AS total_net_sales
        FROM sales
        GROUP BY hcp_id
    ) sa
        ON h.hcp_id = sa.hcp_id
),
benchmarks AS (
    SELECT
        AVG(avg_engagement_score) AS average_engagement_benchmark,
        PERCENTILE_CONT(0.35) WITHIN GROUP (ORDER BY total_net_sales)
            AS low_sales_threshold
    FROM hcp_metrics
)
SELECT
    hm.hcp_id,
    hm.hcp_name,
    hm.specialty,
    hm.hcp_tier,
    hm.territory_name,
    hm.avg_engagement_score,
    hm.total_calls,
    hm.total_net_sales
FROM hcp_metrics hm
CROSS JOIN benchmarks b
WHERE hm.avg_engagement_score >= b.average_engagement_benchmark
  AND hm.total_net_sales <= b.low_sales_threshold
ORDER BY
    hm.avg_engagement_score DESC,
    hm.total_net_sales ASC
LIMIT 25;

-- These HCPs show engagement strength but comparatively low revenue, so they may warrant targeted follow-up.


/*
Query 09: Campaign Response by Territory
Business question: Which territories show the strongest campaign engagement?
Why it matters: Campaign response helps assess territory-level message reach and interaction quality.
*/
SELECT
    t.territory_id,
    t.territory_name,
    t.region,
    COUNT(ce.engagement_id) AS total_engagements,
    SUM(CASE WHEN ce.opened THEN 1 ELSE 0 END) AS opens,
    SUM(CASE WHEN ce.clicked THEN 1 ELSE 0 END) AS clicks,
    SUM(CASE WHEN ce.attended THEN 1 ELSE 0 END) AS attendances,
    ROUND(AVG(ce.response_score), 2) AS avg_response_score,
    ROUND(SUM(CASE WHEN ce.clicked THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(ce.engagement_id), 0) * 100, 2) AS click_rate_percent
FROM campaign_engagement ce
JOIN territories t
    ON ce.territory_id = t.territory_id
GROUP BY
    t.territory_id,
    t.territory_name,
    t.region
ORDER BY avg_response_score DESC;

-- Use response and click rates as directional campaign engagement indicators by territory.


/*
Query 10: Product Margin Contribution
Business question: Which products contribute the most estimated margin?
Why it matters: Revenue alone can hide margin differences across products.
*/
SELECT
    p.product_id,
    p.product_name,
    p.therapy_area,
    p.margin_percent,
    ROUND(SUM(s.net_sales), 2) AS total_net_sales,
    ROUND(SUM(s.net_sales * p.margin_percent / 100), 2) AS estimated_margin_contribution
FROM sales s
JOIN products p
    ON s.product_id = p.product_id
GROUP BY
    p.product_id,
    p.product_name,
    p.therapy_area,
    p.margin_percent
ORDER BY estimated_margin_contribution DESC;

-- Products with high revenue and high margin_percent rise to the top of this list.


/*
Query 11: Monthly Revenue Trend
Business question: How does net sales revenue trend by month?
Why it matters: Monthly trends reveal growth patterns, dips, and seasonality.
*/
SELECT
    DATE_TRUNC('month', sale_date)::DATE AS sales_month,
    ROUND(SUM(net_sales), 2) AS monthly_net_sales,
    COUNT(*) AS sales_transactions,
    COUNT(DISTINCT hcp_id) AS active_hcps
FROM sales
GROUP BY DATE_TRUNC('month', sale_date)::DATE
ORDER BY sales_month;

-- Read this chronologically to spot revenue momentum or months that need investigation.


/*
Query 12: Month-over-Month Revenue Growth
Business question: What is the month-over-month revenue growth rate?
Why it matters: Growth rate shows whether business performance is accelerating or slowing down.
*/
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', sale_date)::DATE AS sales_month,
        SUM(net_sales) AS monthly_net_sales
    FROM sales
    GROUP BY DATE_TRUNC('month', sale_date)::DATE
),
monthly_growth AS (
    SELECT
        sales_month,
        monthly_net_sales,
        LAG(monthly_net_sales) OVER (ORDER BY sales_month) AS previous_month_net_sales
    FROM monthly_sales
)
SELECT
    sales_month,
    ROUND(monthly_net_sales, 2) AS monthly_net_sales,
    ROUND(previous_month_net_sales, 2) AS previous_month_net_sales,
    ROUND(
        (monthly_net_sales - previous_month_net_sales)
        / NULLIF(previous_month_net_sales, 0) * 100,
        2
    ) AS month_over_month_growth_percent
FROM monthly_growth
ORDER BY sales_month;

-- A positive growth percent means revenue increased versus the prior month.


/*
Query 13: Top Reps per Territory
Business question: Who are the highest revenue reps within each territory?
Why it matters: Territory-level rep ranking supports benchmarking and coaching.
*/
WITH rep_territory_sales AS (
    SELECT
        t.territory_id,
        t.territory_name,
        mr.rep_id,
        mr.rep_name,
        ROUND(SUM(s.net_sales), 2) AS total_net_sales
    FROM sales s
    JOIN medical_reps mr
        ON s.rep_id = mr.rep_id
    JOIN territories t
        ON s.territory_id = t.territory_id
    GROUP BY
        t.territory_id,
        t.territory_name,
        mr.rep_id,
        mr.rep_name
),
ranked_reps AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY territory_id
            ORDER BY total_net_sales DESC
        ) AS territory_revenue_rank
    FROM rep_territory_sales
)
SELECT
    territory_id,
    territory_name,
    rep_id,
    rep_name,
    total_net_sales,
    territory_revenue_rank
FROM ranked_reps
WHERE territory_revenue_rank <= 3
ORDER BY
    territory_name,
    territory_revenue_rank;

-- Each territory can have up to three top-ranked reps depending on available rep coverage.


/*
Query 14: Underperforming Territories
Business question: Which territories have low sales compared with market potential?
Why it matters: This highlights territories where commercial opportunity may not be fully captured.
*/
SELECT
    t.territory_id,
    t.territory_name,
    t.region,
    ROUND(t.market_potential, 2) AS market_potential,
    ROUND(COALESCE(SUM(s.net_sales), 0), 2) AS total_net_sales,
    ROUND(COALESCE(SUM(s.net_sales), 0) / NULLIF(t.market_potential, 0) * 100, 2)
        AS market_capture_percent,
    CASE
        WHEN COALESCE(SUM(s.net_sales), 0) / NULLIF(t.market_potential, 0) < 0.75
            THEN 'Underperforming'
        ELSE 'Healthy'
    END AS territory_status
FROM territories t
LEFT JOIN sales s
    ON t.territory_id = s.territory_id
GROUP BY
    t.territory_id,
    t.territory_name,
    t.region,
    t.market_potential
ORDER BY market_capture_percent ASC;

-- Lower market_capture_percent suggests a territory may need deeper review.


/*
Query 15: Tier 1 HCP Performance
Business question: How are Tier 1 HCPs performing across revenue, calls, and engagement?
Why it matters: Tier 1 HCPs are priority customers and should be closely monitored.
*/
SELECT
    h.hcp_id,
    h.hcp_name,
    h.specialty,
    t.territory_name,
    COALESCE(ca.total_calls, 0) AS total_calls,
    ROUND(ca.avg_engagement_score, 2) AS avg_engagement_score,
    ROUND(COALESCE(sa.total_net_sales, 0), 2) AS total_net_sales
FROM hcps h
JOIN territories t
    ON h.territory_id = t.territory_id
LEFT JOIN (
    SELECT
        hcp_id,
        COUNT(*) AS total_calls,
        AVG(engagement_score) AS avg_engagement_score
    FROM hcp_calls
    GROUP BY hcp_id
) ca
    ON h.hcp_id = ca.hcp_id
LEFT JOIN (
    SELECT
        hcp_id,
        SUM(net_sales) AS total_net_sales
    FROM sales
    GROUP BY hcp_id
) sa
    ON h.hcp_id = sa.hcp_id
WHERE h.hcp_tier = 'Tier 1'
ORDER BY total_net_sales DESC;

-- Use this list to check whether priority HCPs are receiving attention and generating revenue.


/*
Query 16: Sales by Affiliated Hospital
Business question: Which affiliated hospitals are associated with the most HCP revenue?
Why it matters: Hospital-level concentration can guide institutional account planning.
*/
SELECT
    h.affiliated_hospital,
    COUNT(DISTINCT h.hcp_id) AS hcps_at_hospital,
    COUNT(*) AS sales_transactions,
    ROUND(SUM(s.net_sales), 2) AS total_net_sales
FROM sales s
JOIN hcps h
    ON s.hcp_id = h.hcp_id
GROUP BY h.affiliated_hospital
ORDER BY total_net_sales DESC
LIMIT 20;

-- The dataset has affiliated_hospital, not hospital type, so this ranks individual affiliations.


/*
Query 17: Call Type Effectiveness
Business question: Which call types are associated with stronger engagement and revenue?
Why it matters: Call planning can improve when teams know which call types perform better.
*/
WITH call_type_metrics AS (
    SELECT
        hc.call_type,
        COUNT(DISTINCT hc.call_id) AS total_calls,
        ROUND(AVG(hc.engagement_score), 2) AS avg_engagement_score,
        ROUND(COALESCE(SUM(s.net_sales), 0), 2) AS total_net_sales
    FROM hcp_calls hc
    LEFT JOIN sales s
        ON hc.hcp_id = s.hcp_id
       AND hc.rep_id = s.rep_id
       AND hc.product_id = s.product_id
       AND s.sale_date BETWEEN hc.call_date AND hc.call_date + INTERVAL '30 days'
    GROUP BY hc.call_type
)
SELECT
    call_type,
    total_calls,
    avg_engagement_score,
    total_net_sales,
    ROUND(total_net_sales / NULLIF(total_calls, 0), 2) AS revenue_per_call
FROM call_type_metrics
ORDER BY revenue_per_call DESC;

-- This is an association view by call type, not proof that one call type caused higher revenue.


/*
Query 18: Sample Dropped vs Sales Relationship
Business question: Are calls with sample drops associated with different sales levels?
Why it matters: This gives a directional comparison for sample strategy discussions.
*/
WITH sample_metrics AS (
    SELECT
        hc.sample_dropped,
        COUNT(DISTINCT hc.call_id) AS total_calls,
        ROUND(AVG(hc.engagement_score), 2) AS avg_engagement_score,
        ROUND(COALESCE(SUM(s.net_sales), 0), 2) AS net_sales_within_30_days
    FROM hcp_calls hc
    LEFT JOIN sales s
        ON hc.hcp_id = s.hcp_id
       AND hc.rep_id = s.rep_id
       AND hc.product_id = s.product_id
       AND s.sale_date BETWEEN hc.call_date AND hc.call_date + INTERVAL '30 days'
    GROUP BY hc.sample_dropped
)
SELECT
    CASE
        WHEN sample_dropped THEN 'Sample dropped'
        ELSE 'No sample dropped'
    END AS sample_group,
    total_calls,
    avg_engagement_score,
    net_sales_within_30_days,
    ROUND(net_sales_within_30_days / NULLIF(total_calls, 0), 2) AS revenue_per_call
FROM sample_metrics
ORDER BY sample_group;

-- Treat this as a correlation/proxy analysis only. It does not prove sample drops caused sales.


/*
Query 19: Campaign ROI Proxy
Business question: Which campaigns show stronger engagement and sales proxy performance versus budget?
Why it matters: Campaign teams need a directional view of spend efficiency and response quality.
*/
WITH campaign_sales_proxy AS (
    SELECT
        c.campaign_id,
        c.campaign_name,
        c.budget,
        ROUND(COALESCE(SUM(s.net_sales), 0), 2) AS territory_product_net_sales
    FROM campaigns c
    LEFT JOIN sales s
        ON c.territory_id = s.territory_id
       AND c.product_id = s.product_id
       AND s.sale_date BETWEEN c.start_date AND c.end_date
    GROUP BY
        c.campaign_id,
        c.campaign_name,
        c.budget
),
campaign_response AS (
    SELECT
        campaign_id,
        COUNT(*) AS total_engagements,
        SUM(CASE WHEN opened THEN 1 ELSE 0 END) AS opens,
        SUM(CASE WHEN clicked THEN 1 ELSE 0 END) AS clicks,
        SUM(CASE WHEN attended THEN 1 ELSE 0 END) AS attendances,
        ROUND(AVG(response_score), 2) AS avg_response_score
    FROM campaign_engagement
    GROUP BY campaign_id
)
SELECT
    csp.campaign_id,
    csp.campaign_name,
    ROUND(csp.budget, 2) AS budget,
    COALESCE(cr.total_engagements, 0) AS total_engagements,
    COALESCE(cr.opens, 0) AS opens,
    COALESCE(cr.clicks, 0) AS clicks,
    COALESCE(cr.attendances, 0) AS attendances,
    cr.avg_response_score,
    csp.territory_product_net_sales,
    ROUND(csp.territory_product_net_sales / NULLIF(csp.budget, 0), 2)
        AS sales_to_budget_proxy
FROM campaign_sales_proxy csp
LEFT JOIN campaign_response cr
    ON csp.campaign_id = cr.campaign_id
ORDER BY sales_to_budget_proxy DESC NULLS LAST;

-- This is a proxy analysis based on matching campaign territory, product, and dates. It is not causal ROI.


/*
Query 20: Next-Best HCP Candidates for Reps
Business question: Which HCPs should reps consider prioritizing for future call planning?
Why it matters: A simple rule-based score can help reps find valuable HCPs who may need follow-up.
*/
WITH hcp_rep_activity AS (
    SELECT
        mr.rep_id,
        mr.rep_name,
        h.hcp_id,
        h.hcp_name,
        h.hcp_tier,
        h.specialty,
        h.patient_volume,
        t.territory_name,
        ca.last_call_date,
        ROUND(ca.avg_engagement_score, 2) AS avg_engagement_score,
        ROUND(COALESCE(sa.total_net_sales, 0), 2) AS total_net_sales
    FROM medical_reps mr
    JOIN hcps h
        ON mr.territory_id = h.territory_id
    JOIN territories t
        ON h.territory_id = t.territory_id
    LEFT JOIN (
        SELECT
            rep_id,
            hcp_id,
            MAX(call_date) AS last_call_date,
            AVG(engagement_score) AS avg_engagement_score
        FROM hcp_calls
        GROUP BY
            rep_id,
            hcp_id
    ) ca
        ON mr.rep_id = ca.rep_id
       AND h.hcp_id = ca.hcp_id
    LEFT JOIN (
        SELECT
            rep_id,
            hcp_id,
            SUM(net_sales) AS total_net_sales
        FROM sales
        GROUP BY
            rep_id,
            hcp_id
    ) sa
        ON mr.rep_id = sa.rep_id
       AND h.hcp_id = sa.hcp_id
),
scored_candidates AS (
    SELECT
        *,
        CURRENT_DATE - last_call_date AS days_since_last_call,
        CASE hcp_tier
            WHEN 'Tier 1' THEN 40
            WHEN 'Tier 2' THEN 25
            ELSE 10
        END
        + CASE
            WHEN last_call_date IS NULL THEN 25
            WHEN CURRENT_DATE - last_call_date >= 60 THEN 25
            WHEN CURRENT_DATE - last_call_date >= 30 THEN 15
            ELSE 5
        END
        + CASE
            WHEN COALESCE(avg_engagement_score, 0) >= 75 THEN 20
            WHEN COALESCE(avg_engagement_score, 0) >= 50 THEN 10
            ELSE 0
        END
        + CASE
            WHEN patient_volume >= 700 THEN 15
            WHEN patient_volume >= 400 THEN 10
            ELSE 5
        END
        + CASE
            WHEN total_net_sales < 100000 THEN 10
            ELSE 0
        END AS next_best_action_score
    FROM hcp_rep_activity
)
SELECT
    rep_id,
    rep_name,
    territory_name,
    hcp_id,
    hcp_name,
    hcp_tier,
    specialty,
    patient_volume,
    last_call_date,
    days_since_last_call,
    avg_engagement_score,
    total_net_sales,
    next_best_action_score
FROM scored_candidates
ORDER BY
    rep_id,
    next_best_action_score DESC,
    hcp_tier,
    total_net_sales ASC
LIMIT 100;

-- Higher scores suggest stronger candidates for rep follow-up based on tier, recency, engagement, and potential.
