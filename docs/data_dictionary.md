# PharmaPulse Data Dictionary

## How to Read This Data Dictionary

Table purpose explains what the table represents. Data type follows the PostgreSQL schema. Business meaning explains how the field is used in analysis. Example value shows a representative sample value.

## territories

Purpose: Stores geographic sales territories used for HCP assignment, medical rep coverage, sales reporting, and campaign analysis.

| Column Name | Data Type | Business Meaning | Example Value |
|---|---|---|---|
| territory_id | VARCHAR(20) | Unique identifier for a sales territory. | T001 |
| territory_name | VARCHAR(100) | Business-friendly name of the sales territory. | Pune Central |
| region | VARCHAR(50) | Broader geographic region used for rollup reporting. | West |
| state | VARCHAR(50) | State where the territory is located. | Maharashtra |
| city | VARCHAR(50) | Primary city represented by the territory. | Pune |
| market_potential | NUMERIC(14, 2) | Estimated commercial opportunity for the territory. | 29455603.00 |
| target_hcps | INTEGER | Planned number of HCPs to cover in the territory. | 38 |

## products

Purpose: Stores pharma product attributes used for sales, margin, therapy-area, and campaign analysis.

| Column Name | Data Type | Business Meaning | Example Value |
|---|---|---|---|
| product_id | VARCHAR(20) | Unique identifier for a pharma product. | PROD001 |
| product_name | VARCHAR(100) | Product or brand name. | Cardiovance |
| therapy_area | VARCHAR(100) | Therapeutic category associated with the product. | Cardiology |
| brand_type | VARCHAR(50) | Product classification such as branded, generic, or specialty. | Generic |
| launch_date | DATE | Date when the product was launched. | 2020-11-04 |
| unit_price | NUMERIC(10, 2) | Selling price per unit. | 1626.87 |
| margin_percent | NUMERIC(5, 2) | Estimated product margin percentage used for margin contribution analysis. | 48.02 |
| target_specialty | VARCHAR(100) | Primary HCP specialty targeted for the product. | Cardiologist |

## hcps

Purpose: Stores healthcare professional attributes used for segmentation, engagement analysis, sales attribution, and call planning.

| Column Name | Data Type | Business Meaning | Example Value |
|---|---|---|---|
| hcp_id | VARCHAR(20) | Unique identifier for a healthcare professional. | HCP0001 |
| hcp_name | VARCHAR(150) | Name of the healthcare professional. | Dr. Aryan Maharaj |
| specialty | VARCHAR(100) | Medical specialty of the HCP. | Dermatologist |
| hcp_tier | VARCHAR(20) | Commercial priority segment assigned to the HCP. | Tier 2 |
| territory_id | VARCHAR(20) | Territory where the HCP is assigned. | T001 |
| city | VARCHAR(50) | City where the HCP practices. | Pune |
| state | VARCHAR(50) | State where the HCP practices. | Maharashtra |
| affiliated_hospital | VARCHAR(150) | Hospital or institution associated with the HCP. | Kapoor and Sons Hospital |
| years_practicing | INTEGER | Number of years the HCP has been practicing. | 30 |
| patient_volume | INTEGER | Estimated patient volume associated with the HCP. | 683 |
| preferred_channel | VARCHAR(50) | Preferred engagement channel for communication. | Phone |
| email_opt_in | BOOLEAN | Indicates whether the HCP has opted in for email communication. | TRUE |

## medical_reps

Purpose: Stores medical representative information, territory assignments, managers, and performance targets.

| Column Name | Data Type | Business Meaning | Example Value |
|---|---|---|---|
| rep_id | VARCHAR(20) | Unique identifier for a medical representative. | REP001 |
| rep_name | VARCHAR(150) | Name of the medical representative. | Tanish Grover |
| manager_name | VARCHAR(150) | Name of the manager responsible for the rep. | George Narula |
| territory_id | VARCHAR(20) | Territory assigned to the medical representative. | T001 |
| region | VARCHAR(50) | Region where the rep operates. | West |
| hire_date | DATE | Date when the rep joined the organization. | 2019-01-29 |
| experience_years | INTEGER | Years of field or commercial experience. | 10 |
| monthly_call_target | INTEGER | Monthly target for HCP calls. | 110 |
| sales_target | NUMERIC(14, 2) | Revenue target assigned to the medical representative. | 1272325.00 |

## campaigns

Purpose: Stores commercial campaign details linked to products and territories.

| Column Name | Data Type | Business Meaning | Example Value |
|---|---|---|---|
| campaign_id | VARCHAR(20) | Unique identifier for a campaign. | CAMP0001 |
| campaign_name | VARCHAR(150) | Business name of the campaign. | Cardiovance Recall Campaign |
| product_id | VARCHAR(20) | Product promoted by the campaign. | PROD001 |
| territory_id | VARCHAR(20) | Territory targeted by the campaign. | T001 |
| campaign_type | VARCHAR(50) | Campaign channel or format. | Email |
| start_date | DATE | Campaign start date. | 2026-02-16 |
| end_date | DATE | Campaign end date. | 2026-05-27 |
| budget | NUMERIC(14, 2) | Campaign budget allocated for the activity. | 1018885.00 |
| target_hcp_tier | VARCHAR(20) | HCP tier targeted by the campaign. | All Tiers |
| objective | VARCHAR(255) | Stated business objective of the campaign. | Drive product adoption |

## hcp_calls

Purpose: Stores HCP call activity, including call planning, rep interaction, product discussion, and engagement scoring.

| Column Name | Data Type | Business Meaning | Example Value |
|---|---|---|---|
| call_id | VARCHAR(20) | Unique identifier for an HCP call record. | CALL000001 |
| call_date | DATE | Date when the call occurred. | 2025-01-11 |
| hcp_id | VARCHAR(20) | HCP contacted during the call. | HCP0373 |
| rep_id | VARCHAR(20) | Medical representative who conducted the call. | REP001 |
| territory_id | VARCHAR(20) | Territory associated with the call. | T001 |
| product_id | VARCHAR(20) | Product discussed during the call. | PROD008 |
| call_type | VARCHAR(50) | Type of call interaction. | Planned |
| call_status | VARCHAR(50) | Completion status of the call. | Completed |
| call_duration_minutes | INTEGER | Duration of the call in minutes. | 27 |
| discussion_topic | VARCHAR(255) | Main topic discussed during the call. | Patient affordability |
| sample_dropped | BOOLEAN | Indicates whether a product sample was provided during the call. | TRUE |
| next_call_planned_date | DATE | Planned date for the next follow-up call. | 2025-01-30 |
| engagement_score | INTEGER | Score representing HCP engagement during the interaction. | 91 |

## sales

Purpose: Stores HCP-level product sales transactions used for revenue, territory, rep, HCP, and product performance analysis.

| Column Name | Data Type | Business Meaning | Example Value |
|---|---|---|---|
| sales_id | VARCHAR(20) | Unique identifier for a sales transaction. | SALE000001 |
| sale_date | DATE | Date when the sale was recorded. | 2025-01-09 |
| sale_month | VARCHAR(7) | Month of sale in YYYY-MM format for monthly analysis. | 2025-01 |
| hcp_id | VARCHAR(20) | HCP associated with the sale. | HCP0421 |
| territory_id | VARCHAR(20) | Territory associated with the sale. | T001 |
| rep_id | VARCHAR(20) | Medical representative associated with the sale. | REP001 |
| product_id | VARCHAR(20) | Product sold. | PROD014 |
| units_sold | INTEGER | Number of product units sold. | 82 |
| gross_sales | NUMERIC(14, 2) | Revenue before discounts. | 128985.18 |
| discount_amount | NUMERIC(14, 2) | Discount applied to the transaction. | 14103.99 |
| net_sales | NUMERIC(14, 2) | Revenue after discounts and the primary revenue metric for analysis. | 114881.19 |
| sales_channel | VARCHAR(50) | Channel through which the sale was recorded. | Distributor |

## campaign_engagement

Purpose: Stores HCP interactions with campaigns, including response behavior and engagement scoring.

| Column Name | Data Type | Business Meaning | Example Value |
|---|---|---|---|
| engagement_id | VARCHAR(20) | Unique identifier for a campaign engagement record. | ENG000001 |
| campaign_id | VARCHAR(20) | Campaign associated with the engagement. | CAMP0001 |
| hcp_id | VARCHAR(20) | HCP who engaged with the campaign. | HCP0349 |
| rep_id | VARCHAR(20) | Medical representative associated with the HCP or campaign activity. | REP037 |
| territory_id | VARCHAR(20) | Territory associated with the campaign engagement. | T001 |
| engagement_date | DATE | Date when the engagement occurred. | 2026-05-23 |
| channel | VARCHAR(50) | Channel where the engagement occurred. | Field Event |
| engagement_type | VARCHAR(50) | Type of campaign interaction. | Clicked Link |
| opened | BOOLEAN | Indicates whether the HCP opened campaign content. | TRUE |
| clicked | BOOLEAN | Indicates whether the HCP clicked campaign content. | TRUE |
| attended | BOOLEAN | Indicates whether the HCP attended a campaign event. | FALSE |
| response_score | INTEGER | Score representing the strength of the HCP campaign response. | 87 |
