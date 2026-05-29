# PharmaPulse Project Walkthrough

PharmaPulse is an end-to-end pharma commercial analytics platform for HCP engagement, medical rep performance, territory revenue, campaign effectiveness, product margin contribution, ML-based HCP scoring, and Streamlit decision support. This walkthrough is useful for a technical reviewer, hiring manager, or teammate who wants to understand the project design, technical flow, and business reasoning behind the platform.

## 1. Walkthrough Purpose and Project Context

The purpose of this walkthrough is to explain how PharmaPulse moves from generated commercial data to usable analytics outputs. The project is built around pharma commercial concepts such as HCP tier, medical rep target achievement, call planning, engagement score, therapy area performance, campaign response, and product margin contribution.

Unlike the shorter [README.md](../README.md), this document goes deeper into why each layer exists. It connects the scripts, SQL model, Power BI dashboard, ML outputs, and Streamlit app into one workflow so a reader can follow the project from raw synthetic data through business-facing decision support.

## 2. Project Objective

The objective of PharmaPulse is to simulate how a pharma commercial analytics team might organize data for HCP engagement and sales planning. The project creates 8 commercial datasets, validates 69 data-quality checks, loads the cleaned outputs into an 8-table PostgreSQL model, and then builds SQL, dashboard, ML, and app layers on top.

The project is not intended to claim real-world commercial impact. It is designed to show a realistic analytics workflow where metrics such as net sales, engagement score, revenue per call, target achievement, and days since last call are used as directional signals for review.

## 3. Business Problem

Commercial pharma teams often evaluate HCP engagement, medical rep performance, territory revenue, campaign response, and product margin contribution in separate views. That separation makes it harder to answer practical planning questions, such as which HCPs need follow-up, which reps are near target, which territories are efficient, and which products produce stronger margin contribution.

PharmaPulse brings those signals together so business users can review HCP tier, call activity, sales outcomes, therapy area, campaign behavior, and product economics in one connected flow. The project treats these metrics as proxies and planning signals, not proof that any single activity directly drives sales.

## 4. End-to-End Architecture

![PharmaPulse Architecture](architecture.png)

The architecture starts with synthetic data generation because the project needs a complete pharma commercial dataset without using private or regulated commercial data. The generated data includes territories, products, HCPs, medical reps, campaigns, HCP calls, sales, and campaign engagement, which gives the later analytics layers enough business context to be meaningful.

Cleaning and validation happen before database loading because PostgreSQL should receive data that already has consistent dates, IDs, required fields, and relationship integrity. In this project, 69 validation checks passed with 0 failures, giving the database and dashboard layers a cleaner foundation.

PostgreSQL is used instead of only flat files because the project has connected commercial entities. Tables such as `hcps`, `medical_reps`, `territories`, `sales`, and `hcp_calls` need foreign key relationships so territory, rep, product, and HCP activity can be analyzed reliably.

The SQL layer sits between the database and dashboard because business questions are easier to review when logic is explicit. The 12 SQL analysis queries answer questions such as territory revenue, rep target achievement, campaign response, product margin contribution, and next-best HCP candidates.

SQL views are used before Power BI because dashboard visuals should not repeat complex joins or accidentally multiply rows across calls, sales, and campaign engagement. The 5 dashboard-ready views pre-aggregate key measures so Power BI can focus on reporting rather than rebuilding business logic.

The ML and Streamlit layers are separated from the SQL dashboard layer because they support a different workflow. Power BI summarizes commercial performance, while Streamlit gives users an interactive way to review HCP segmentation, risk monitoring, next-best-action scoring, and the sales forecast baseline from processed ML outputs.

## 5. Dataset Design

The dataset is organized around 8 commercial entities that map to the PostgreSQL tables: `territories`, `products`, `hcps`, `medical_reps`, `campaigns`, `hcp_calls`, `sales`, and `campaign_engagement`. This structure supports common commercial analytics questions across geography, brand, field force, HCP activity, revenue, and campaign response.

The core activity tables are intentionally rich enough to support multiple views. The project includes 19,751 HCP calls, 17,967 sales records, and 1,710 campaign engagement records. Those records connect to 500 HCPs, 40 medical reps, 12 territories, 25 products, and 60 campaigns.

Several fields are designed around pharma commercial use cases. `hcp_tier` supports account prioritization, `engagement_score` supports call quality review, `sales_target` supports rep target achievement, `therapy_area` supports portfolio analysis, and `margin_percent` supports product margin contribution analysis.

## 6. Data Pipeline: Generation, Cleaning, and Validation

The data pipeline begins with synthetic data generation for 8 commercial datasets. This gives PharmaPulse enough scale to produce realistic variation across HCP calls, territory revenue, product sales, and campaign engagement without relying on confidential field data.

Cleaning prepares the generated CSVs for analysis by standardizing structure and creating consistent outputs under `data/cleaned`. This matters because downstream steps such as PostgreSQL loading, EDA notebooks, SQL views, and ML feature engineering all depend on stable column names and reliable relationships.

Validation is a formal checkpoint before the database layer. The project runs 69 validation checks covering data quality, referential consistency, and business-rule expectations; all 69 passed and 0 failed. That result supports confidence that the 19,751 call records, 17,967 sales records, and 1,710 campaign engagement records can be used safely in analysis.

The same cleaned data also supports reproducibility outside the database. The ML pipeline reads cleaned CSVs directly, which means HCP segmentation, disengagement risk scoring, the sales forecast baseline, and next-best-action scoring can run locally without requiring a live PostgreSQL connection.

## 7. PostgreSQL Database Design

The PostgreSQL schema uses 8 relational tables with primary keys, foreign keys, and basic constraints. This structure reflects how commercial data is usually connected: HCPs belong to territories, reps are assigned to territories, calls link reps to HCPs and products, sales link HCPs to products and reps, and campaign engagement links campaign response back to HCPs and territories.

PostgreSQL is useful here because the business questions require relationship-aware analysis. For example, rep target achievement needs `medical_reps` and `sales`, territory revenue needs `territories` and `sales`, and campaign response needs `campaigns`, `campaign_engagement`, `products`, and `territories`.

The database model also reduces ambiguity for dashboard reporting. Instead of relying on separate CSV joins inside every analysis layer, the database centralizes the commercial relationships and lets SQL define repeatable business logic.

For field definitions and table-level context, see [docs/data_dictionary.md](data_dictionary.md).

## 8. SQL Analysis Layer

The SQL analysis layer contains 12 business-focused queries. They cover total net sales, revenue by territory, therapy area performance, top HCPs by revenue, medical rep target achievement, revenue per HCP call, high-engagement low-sales HCPs, campaign response, product margin contribution, month-over-month revenue growth, top reps by territory, and next-best HCP candidates.

Keeping the business logic in SQL means a reviewer can inspect how rep target achievement is calculated, how product margin contribution is estimated, and how high-engagement low-sales HCPs are identified before those definitions appear in dashboards or reports.

The SQL queries also bridge technical analysis and commercial interpretation. For example, revenue per completed call is treated as an efficiency signal, product margin contribution is used to avoid over-weighting volume alone, and HCP prioritization is framed as a planning proxy rather than a causal recommendation.

## 9. Power BI Dashboard Layer

The Power BI dashboard is supported by 5 dashboard-ready SQL views. These views summarize territory revenue, medical rep performance, HCP engagement, campaign effectiveness, and product margin contribution.

The views pre-aggregate source tables before joining them because sales, calls, and campaign engagement can create row multiplication if joined directly at transaction grain. This design keeps dashboard measures aligned with SQL analysis and supports cleaner visuals across the 4 Power BI pages.

The 4 dashboard pages cover executive performance, territory and rep performance, HCP engagement, and product and campaign performance. The screenshots in `dashboard/screenshots/` show how the reporting layer surfaces total net sales, target achievement, engagement behavior, campaign response, and margin contribution.

## 10. ML and Decision-Support Layer

The ML layer is designed for decision support, not automated prediction. Its outputs help users review HCP segments, risk signals, forecast baseline ranges, and next-best-action priorities, but they are not validated against real commercial outcomes or holdout field data.

HCP segmentation uses K-Means clustering with 3 clusters. The features are total net sales, total calls, average engagement score, and days since last call. These features were selected because they combine commercial value, field activity, engagement quality, and recency. A silhouette score is printed during the pipeline run to give a rough measure of cluster separation quality.

Disengagement risk scoring uses transparent rules because there are no historical churn labels in the synthetic dataset. The rules use days since last call and average engagement score, with a numeric risk score that also considers call activity and revenue signals. This makes the risk output explainable for HCP follow-up review.

The sales forecast is a baseline directional range, not a prediction. It aggregates monthly net sales and creates a simple 3-month forecast with upper and lower planning bands, which is useful for dashboarding but not appropriate for accuracy claims.

Next-best-action scoring combines revenue rank, recency, engagement rank, and segment value into a prioritization score. In business terms, the score helps identify HCPs where value, follow-up need, engagement, and segment assignment suggest a stronger planning priority.

The pipeline writes several processed outputs, including `hcp_segments.csv`, `hcp_churn_scores.csv`, `sales_forecast.csv`, `next_best_action.csv`, and `hcp_master_scores.csv`. The `hcp_master_scores.csv` file is the unified HCP intelligence table used by the Streamlit app.

## 11. Streamlit App Layer

The Streamlit app provides an interactive decision-support layer on top of the processed ML outputs. It is deployed at [https://pharmapulse-analytics.streamlit.app/](https://pharmapulse-analytics.streamlit.app/) and can also run locally from `streamlit_app/app.py`.

Streamlit is used here because the ML outputs are best explored through filters, tables, and interactive charts rather than static dashboard pages alone. The app includes Executive Overview, HCP Segments, Risk Monitoring, Next-Best Action, Sales Forecast, and HCP Master Table sections.

The Executive Overview surfaces KPI cards and segment distributions. HCP Segments shows the K-Means clustering output with an interactive scatter plot. Risk Monitoring surfaces the highest-priority disengagement signals. Next-Best Action ranks HCPs by prioritization score with recommended actions. Sales Forecast shows the baseline trend with a directional planning band. HCP Master Table gives a filterable and downloadable view of all 500 HCPs with their scores.

The app does not require a live PostgreSQL connection. It reads processed CSVs such as `hcp_master_scores.csv`, `next_best_action.csv`, and `sales_forecast.csv`, which makes it lightweight enough for local use and public deployment.

## 12. Key Findings

Pune Central generated ₹204.5M net sales from 42 unique HCPs and 1,972 calls, equal to approximately ₹103.7K revenue per call. Gurgaon Corporate generated lower total revenue at ₹153.6M, but had the highest revenue per call at approximately ₹109.0K. Commercially, this suggests that territory planning should compare total sales with call efficiency; the action is to review territory-level revenue, HCP coverage, call volume, and revenue per call together before changing field allocation.

Rep target achievement ranges from 70.5% to 147.9%, which creates clear coaching segments. Dalbir Sodhi delivered ₹42.7M net sales against a ₹28.9M target, reaching 147.9%, while Aahana Chokshi delivered ₹39.4M against a ₹55.9M target, reaching 70.5%. Commercially, this indicates that target achievement and revenue per call should be reviewed together; the action is to segment reps for coaching, recognition, and territory support rather than using one performance measure alone.

PainAway generated ₹216.3M net sales and ₹146.2M estimated margin contribution with a 67.61% margin. SugarNorm sold more units at 58,872 and generated ₹172.0M net sales, but produced lower estimated margin contribution at ₹90.2M; GlucoRight sold 53,893 units and generated ₹64.1M net sales, but its 23.2% margin translated to only ₹14.9M estimated margin contribution. Commercially, this suggests volume alone is an incomplete portfolio signal; the action is to combine units, revenue, margin percent, and therapy area context when setting product priorities.

Tier 1 HCPs averaged ₹5.33M revenue per HCP, compared with ₹3.71M for Tier 2 and ₹2.41M for Tier 3. Average engagement scores were similar across tiers, ranging from 50.41 to 50.55, and the recency check found 17 Tier 1 HCPs above the high-revenue threshold of ₹4.28M with at least 19 days since last call. Dr. Dev Shetty in Mumbai Metro is one example: a Tier 1 HCP with ₹9.85M net sales, 47 calls, a 51.32 engagement score, and 22 days since last call. Commercially, this suggests tier value and call recency both matter; the action is to prioritize HCP follow-up using revenue, tier, engagement score, and days since last call.

Respiratory generated ₹322.3M net sales across 2,275 calls, or approximately ₹141.7K revenue per call. Neurology generated ₹91.2M across 2,031 calls, or approximately ₹44.9K per call, while average engagement scores were directionally similar at 49.80 for Respiratory and 51.52 for Neurology. Commercially, this indicates that engagement score alone may not explain therapy area performance; the action is to compare therapy areas using revenue, call volume, engagement, and revenue per call before changing brand emphasis.

Campaign engagement coverage appears healthy because the lowest campaign engagement count was 18 and no campaigns were flagged as `NO ENGAGEMENTS` or `LOW ENGAGEMENT`. Field Event had the highest average click rate at 31.45%, while Email had the lowest average open rate at 69.23%; response scores were relatively stable across campaign types, so they are a secondary signal. Commercially, this suggests channel behavior is more useful than response score alone; the action is to review open rate, click rate, attendance rate, and response score together when refining campaign content.

For the full business brief, see [docs/insights_report.md](insights_report.md).

## 13. Limitations

The PharmaPulse dataset is synthetic, so the findings are directional patterns rather than real commercial conclusions. Numbers such as ₹204.5M territory revenue, 147.9% target achievement, and 31.45% click rate are useful for demonstrating the workflow, but they should not be interpreted as real market evidence.

The ML outputs are not validated against holdout real-world data, so accuracy claims are not appropriate. K-Means segmentation, rule-based risk scoring, the sales forecast baseline, and next-best-action scoring are explainable decision-support tools, not production-validated predictive models.

Engagement score and response score are proxies for simulated behavior. They do not capture actual prescribing behavior, formulary status, market access, competitive activity, or field-force capacity, all of which would be important in a real pharma commercial deployment.

## 14. Future Improvements

A dbt transformation layer could make the SQL model more modular by separating staging, intermediate, and dashboard-ready models for the 8 relational tables and 5 dashboard views. This would make metric definitions such as revenue per call, target achievement, and margin contribution easier to maintain.

An automated refresh workflow could regenerate data, run 69 validation checks, load PostgreSQL, rebuild ML outputs, and refresh the Streamlit-ready CSVs in a repeatable sequence. That would make the project closer to an operational analytics workflow while preserving the current transparent logic.

Future versions could integrate CRM or commercial activity data, add forecasting by territory and therapy area, and test territory optimization logic for call planning.
