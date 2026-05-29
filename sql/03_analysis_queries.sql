/*
PharmaPulse SQL Analysis Queries

Phase 6 is analysis-only:
- No views are created.
- No schema changes are made.
- No data is inserted, updated, or deleted.

These 12 queries are designed to be interview-ready examples of pharma
commercial analytics using net_sales as the main revenue metric.
*/


/*
Query 01: Total Net Sales Revenue
Business question: What is the total net sales revenue across the full dataset?
Why it matters: This gives the executive topline revenue number for PharmaPulse.
*/
SELECT
    ROUND(SUM(net_sales), 2) AS total_net_sales
FROM sales;

-- Interpret the output as total realized revenue after discounts.


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
    COUNT(*) AS sales_transactions,
    ROUND(SUM(s.net_sales) / NULLIF(t.market_potential, 0) * 100, 2)
        AS market_capture_percent
FROM sales s
JOIN territories t
    ON s.territory_id = t.territory_id
GROUP BY
    t.territory_id,
    t.territory_name,
    t.region,
    t.city,
    t.market_potential
ORDER BY total_net_sales DESC;

-- Higher revenue territories may be strong markets, while low market capture can signal untapped potential.


/*
Query 03: Revenue by Therapy Area/Product Category
Business question: Which therapy areas contribute the most revenue?
Why it matters: Therapy-area performance supports portfolio planning and brand investment decisions.
*/
SELECT
    p.therapy_area,
    COUNT(DISTINCT p.product_id) AS products_in_category,
    COUNT(DISTINCT s.hcp_id) AS unique_hcps,
    SUM(s.units_sold) AS total_units_sold,
    ROUND(SUM(s.net_sales), 2) AS total_net_sales,
    ROUND(AVG(s.net_sales), 2) AS avg_transaction_value
FROM sales s
JOIN products p
    ON s.product_id = p.product_id
GROUP BY p.therapy_area
ORDER BY total_net_sales DESC;

-- Use this to compare revenue concentration across therapy areas and product categories.


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
    COUNT(*) AS sales_transactions,
    COUNT(DISTINCT s.product_id) AS products_purchased
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
        COUNT(*) AS completed_calls,
        ROUND(AVG(engagement_score), 2) AS avg_engagement_score
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
    COALESCE(rc.completed_calls, 0) AS completed_calls,
    rc.avg_engagement_score,
    ROUND(COALESCE(rs.total_net_sales, 0), 2) AS total_net_sales,
    ROUND(COALESCE(rs.total_net_sales, 0) / NULLIF(rc.completed_calls, 0), 2)
        AS revenue_per_completed_call
FROM medical_reps mr
JOIN territories t
    ON mr.territory_id = t.territory_id
LEFT JOIN rep_calls rc
    ON mr.rep_id = rc.rep_id
LEFT JOIN rep_sales rs
    ON mr.rep_id = rs.rep_id
ORDER BY revenue_per_completed_call DESC NULLS LAST;

-- Higher revenue per call can be used as an efficiency signal, not as proof of call causality.


/*
Query 07: High-Engagement but Low-Sales HCPs
Business question: Which HCPs are engaged but not yet generating high sales?
Why it matters: These HCPs may be good prioritization candidates for focused follow-up.
*/
WITH call_summary AS (
    SELECT
        hcp_id,
        COUNT(*) AS total_calls,
        AVG(engagement_score) AS avg_engagement_score,
        MAX(call_date) AS last_call_date
    FROM hcp_calls
    GROUP BY hcp_id
),
sales_summary AS (
    SELECT
        hcp_id,
        SUM(net_sales) AS total_net_sales
    FROM sales
    GROUP BY hcp_id
),
hcp_metrics AS (
    SELECT
        h.hcp_id,
        h.hcp_name,
        h.specialty,
        h.hcp_tier,
        t.territory_name,
        COALESCE(cs.total_calls, 0) AS total_calls,
        ROUND(cs.avg_engagement_score, 2) AS avg_engagement_score,
        cs.last_call_date,
        ROUND(COALESCE(ss.total_net_sales, 0), 2) AS total_net_sales
    FROM hcps h
    JOIN territories t
        ON h.territory_id = t.territory_id
    LEFT JOIN call_summary cs
        ON h.hcp_id = cs.hcp_id
    LEFT JOIN sales_summary ss
        ON h.hcp_id = ss.hcp_id
),
benchmarks AS (
    SELECT
        AVG(avg_engagement_score) AS engagement_benchmark,
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
    hm.total_calls,
    hm.avg_engagement_score,
    hm.last_call_date,
    hm.total_net_sales
FROM hcp_metrics hm
CROSS JOIN benchmarks b
WHERE hm.avg_engagement_score >= b.engagement_benchmark
  AND hm.total_net_sales <= b.low_sales_threshold
ORDER BY
    hm.avg_engagement_score DESC,
    hm.total_net_sales ASC
LIMIT 25;

-- Treat this as a prioritization signal for follow-up, not as proof that engagement will convert to sales.


/*
Query 08: Campaign Response by Territory
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
    ROUND(SUM(CASE WHEN ce.opened THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(ce.engagement_id), 0) * 100, 2) AS open_rate_percent,
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
Additional Data Review Query: Campaign Engagement Coverage Check
Purpose: Quickly identify campaigns with zero or very low engagement counts before dashboarding.
*/
SELECT
    c.campaign_name,
    t.region,
    t.territory_name,
    COUNT(ce.engagement_id) AS engagements,
    CASE
        WHEN COUNT(ce.engagement_id) = 0 THEN 'NO ENGAGEMENTS'
        WHEN COUNT(ce.engagement_id) < 10 THEN 'LOW ENGAGEMENT'
        ELSE 'OK'
    END AS engagement_status
FROM campaigns c
LEFT JOIN territories t
    ON c.territory_id = t.territory_id
LEFT JOIN campaign_engagement ce
    ON c.campaign_id = ce.campaign_id
GROUP BY
    c.campaign_name,
    t.region,
    t.territory_name
ORDER BY engagements ASC
LIMIT 10;

-- Use this as a diagnostic check only; dashboard views remain separate.


/*
Query 09: Product Margin Contribution
Business question: Which products contribute the most estimated margin?
Why it matters: Revenue alone can hide margin differences across products.
*/
SELECT
    p.product_id,
    p.product_name,
    p.therapy_area,
    p.margin_percent,
    ROUND(SUM(s.net_sales), 2) AS total_net_sales,
    ROUND(SUM(s.net_sales * p.margin_percent / 100), 2) AS estimated_margin_contribution,
    RANK() OVER (
        ORDER BY SUM(s.net_sales * p.margin_percent / 100) DESC
    ) AS margin_rank
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
Query 10: Month-over-Month Revenue Growth
Business question: What is the month-over-month revenue growth rate?
Why it matters: Growth rate shows whether business performance is accelerating or slowing down.
*/
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', sale_date)::DATE AS sales_month,
        SUM(net_sales) AS monthly_net_sales,
        COUNT(DISTINCT hcp_id) AS active_hcps
    FROM sales
    GROUP BY DATE_TRUNC('month', sale_date)::DATE
),
monthly_growth AS (
    SELECT
        sales_month,
        monthly_net_sales,
        active_hcps,
        LAG(monthly_net_sales) OVER (ORDER BY sales_month) AS previous_month_net_sales
    FROM monthly_sales
)
SELECT
    sales_month,
    ROUND(monthly_net_sales, 2) AS monthly_net_sales,
    active_hcps,
    ROUND(previous_month_net_sales, 2) AS previous_month_net_sales,
    ROUND(
        (monthly_net_sales - previous_month_net_sales)
        / NULLIF(previous_month_net_sales, 0) * 100,
        2
    ) AS month_over_month_growth_percent
FROM monthly_growth
ORDER BY sales_month;

-- Positive growth means net sales increased versus the prior month.


/*
Query 11: Top Reps per Territory Using Window Functions
Business question: Who are the highest revenue reps within each territory?
Why it matters: Territory-level rep ranking supports benchmarking and coaching.
*/
WITH rep_territory_sales AS (
    SELECT
        t.territory_id,
        t.territory_name,
        mr.rep_id,
        mr.rep_name,
        COUNT(DISTINCT s.hcp_id) AS active_hcps,
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
    active_hcps,
    total_net_sales,
    territory_revenue_rank
FROM ranked_reps
WHERE territory_revenue_rank <= 3
ORDER BY
    territory_name,
    territory_revenue_rank;

-- RANK compares reps within the same territory instead of comparing all reps globally.


/*
Query 12: Next-Best HCP Candidates Using Rule-Based Scoring
Business question: Which HCPs should reps consider prioritizing for future call planning?
Why it matters: This rule-based scoring approach creates a practical prioritization signal for field teams.
*/
WITH call_summary AS (
    SELECT
        rep_id,
        hcp_id,
        MAX(call_date) AS last_call_date,
        AVG(engagement_score) AS avg_engagement_score,
        COUNT(*) AS total_calls
    FROM hcp_calls
    GROUP BY
        rep_id,
        hcp_id
),
sales_summary AS (
    SELECT
        rep_id,
        hcp_id,
        SUM(net_sales) AS total_net_sales
    FROM sales
    GROUP BY
        rep_id,
        hcp_id
),
hcp_rep_activity AS (
    SELECT
        mr.rep_id,
        mr.rep_name,
        h.hcp_id,
        h.hcp_name,
        h.hcp_tier,
        h.specialty,
        h.patient_volume,
        t.territory_name,
        cs.last_call_date,
        COALESCE(cs.total_calls, 0) AS total_calls,
        ROUND(cs.avg_engagement_score, 2) AS avg_engagement_score,
        ROUND(COALESCE(ss.total_net_sales, 0), 2) AS total_net_sales
    FROM medical_reps mr
    JOIN hcps h
        ON mr.territory_id = h.territory_id
    JOIN territories t
        ON h.territory_id = t.territory_id
    LEFT JOIN call_summary cs
        ON mr.rep_id = cs.rep_id
       AND h.hcp_id = cs.hcp_id
    LEFT JOIN sales_summary ss
        ON mr.rep_id = ss.rep_id
       AND h.hcp_id = ss.hcp_id
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
    total_calls,
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

-- This is rule-based scoring for prioritization, not machine learning and not a causal recommendation model.
