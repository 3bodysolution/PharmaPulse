/*
PharmaPulse PostgreSQL Schema

This script drops child tables first to avoid dependency conflicts from
foreign keys. It then creates parent tables first so child tables can
reference them safely.
*/


-- Drop child tables first, then parent tables.
DROP TABLE IF EXISTS campaign_engagement;
DROP TABLE IF EXISTS hcp_calls;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS hcps;
DROP TABLE IF EXISTS medical_reps;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS territories;


-- territories stores geographic sales territories used across the project.
CREATE TABLE territories (
    territory_id VARCHAR(20) PRIMARY KEY,
    territory_name VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    market_potential NUMERIC(14, 2) NOT NULL CHECK (market_potential >= 0),
    target_hcps INTEGER NOT NULL CHECK (target_hcps >= 0)
);


-- products stores pharma brands and product attributes.
CREATE TABLE products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    therapy_area VARCHAR(100) NOT NULL,
    brand_type VARCHAR(50) NOT NULL,
    launch_date DATE NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    margin_percent NUMERIC(5, 2) NOT NULL CHECK (margin_percent BETWEEN 0 AND 100),
    target_specialty VARCHAR(100) NOT NULL
);


-- hcps stores healthcare professionals and their commercial segments.
CREATE TABLE hcps (
    hcp_id VARCHAR(20) PRIMARY KEY,
    hcp_name VARCHAR(150) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    hcp_tier VARCHAR(20) NOT NULL CHECK (hcp_tier IN ('Tier 1', 'Tier 2', 'Tier 3')),
    territory_id VARCHAR(20) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    affiliated_hospital VARCHAR(150) NOT NULL,
    years_practicing INTEGER NOT NULL CHECK (years_practicing >= 0),
    patient_volume INTEGER NOT NULL CHECK (patient_volume >= 0),
    preferred_channel VARCHAR(50) NOT NULL,
    email_opt_in BOOLEAN NOT NULL,
    CONSTRAINT fk_hcps_territory
        FOREIGN KEY (territory_id)
        REFERENCES territories (territory_id)
        ON DELETE RESTRICT
);


-- medical_reps stores field representatives and their territory assignments.
CREATE TABLE medical_reps (
    rep_id VARCHAR(20) PRIMARY KEY,
    rep_name VARCHAR(150) NOT NULL,
    manager_name VARCHAR(150) NOT NULL,
    territory_id VARCHAR(20) NOT NULL,
    region VARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL,
    experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
    monthly_call_target INTEGER NOT NULL CHECK (monthly_call_target >= 0),
    sales_target NUMERIC(14, 2) NOT NULL CHECK (sales_target >= 0),
    CONSTRAINT fk_medical_reps_territory
        FOREIGN KEY (territory_id)
        REFERENCES territories (territory_id)
        ON DELETE RESTRICT
);


-- campaigns stores commercial campaigns linked to products and territories.
CREATE TABLE campaigns (
    campaign_id VARCHAR(20) PRIMARY KEY,
    campaign_name VARCHAR(150) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    territory_id VARCHAR(20) NOT NULL,
    campaign_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    budget NUMERIC(14, 2) NOT NULL CHECK (budget >= 0),
    target_hcp_tier VARCHAR(20) NOT NULL CHECK (
        target_hcp_tier IN ('Tier 1', 'Tier 2', 'Tier 3', 'All Tiers')
    ),
    objective VARCHAR(255) NOT NULL,
    CONSTRAINT chk_campaign_dates
        CHECK (end_date >= start_date),
    CONSTRAINT fk_campaigns_product
        FOREIGN KEY (product_id)
        REFERENCES products (product_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_campaigns_territory
        FOREIGN KEY (territory_id)
        REFERENCES territories (territory_id)
        ON DELETE RESTRICT
);


-- hcp_calls stores call planning and HCP engagement activity from medical reps.
CREATE TABLE hcp_calls (
    call_id VARCHAR(20) PRIMARY KEY,
    call_date DATE NOT NULL,
    hcp_id VARCHAR(20) NOT NULL,
    rep_id VARCHAR(20) NOT NULL,
    territory_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    call_type VARCHAR(50) NOT NULL,
    call_status VARCHAR(50) NOT NULL,
    call_duration_minutes INTEGER NOT NULL CHECK (call_duration_minutes >= 0),
    discussion_topic VARCHAR(255) NOT NULL,
    sample_dropped BOOLEAN NOT NULL,
    next_call_planned_date DATE NOT NULL,
    engagement_score INTEGER NOT NULL CHECK (engagement_score BETWEEN 1 AND 100),
    CONSTRAINT fk_hcp_calls_hcp
        FOREIGN KEY (hcp_id)
        REFERENCES hcps (hcp_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_hcp_calls_rep
        FOREIGN KEY (rep_id)
        REFERENCES medical_reps (rep_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_hcp_calls_territory
        FOREIGN KEY (territory_id)
        REFERENCES territories (territory_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_hcp_calls_product
        FOREIGN KEY (product_id)
        REFERENCES products (product_id)
        ON DELETE RESTRICT
);


-- sales stores HCP-level product sales. Use net_sales as the main revenue metric.
CREATE TABLE sales (
    sales_id VARCHAR(20) PRIMARY KEY,
    sale_date DATE NOT NULL,
    sale_month VARCHAR(7) NOT NULL,
    hcp_id VARCHAR(20) NOT NULL,
    territory_id VARCHAR(20) NOT NULL,
    rep_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    units_sold INTEGER NOT NULL CHECK (units_sold >= 0),
    gross_sales NUMERIC(14, 2) NOT NULL CHECK (gross_sales >= 0),
    discount_amount NUMERIC(14, 2) NOT NULL CHECK (discount_amount >= 0),
    net_sales NUMERIC(14, 2) NOT NULL CHECK (net_sales >= 0),
    sales_channel VARCHAR(50) NOT NULL,
    CONSTRAINT fk_sales_hcp
        FOREIGN KEY (hcp_id)
        REFERENCES hcps (hcp_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_sales_territory
        FOREIGN KEY (territory_id)
        REFERENCES territories (territory_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_sales_rep
        FOREIGN KEY (rep_id)
        REFERENCES medical_reps (rep_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_sales_product
        FOREIGN KEY (product_id)
        REFERENCES products (product_id)
        ON DELETE RESTRICT
);


-- campaign_engagement stores HCP responses to campaigns.
CREATE TABLE campaign_engagement (
    engagement_id VARCHAR(20) PRIMARY KEY,
    campaign_id VARCHAR(20) NOT NULL,
    hcp_id VARCHAR(20) NOT NULL,
    rep_id VARCHAR(20) NOT NULL,
    territory_id VARCHAR(20) NOT NULL,
    engagement_date DATE NOT NULL,
    channel VARCHAR(50) NOT NULL,
    engagement_type VARCHAR(50) NOT NULL,
    opened BOOLEAN NOT NULL,
    clicked BOOLEAN NOT NULL,
    attended BOOLEAN NOT NULL,
    response_score INTEGER NOT NULL CHECK (response_score BETWEEN 1 AND 100),
    CONSTRAINT fk_campaign_engagement_campaign
        FOREIGN KEY (campaign_id)
        REFERENCES campaigns (campaign_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_campaign_engagement_hcp
        FOREIGN KEY (hcp_id)
        REFERENCES hcps (hcp_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_campaign_engagement_rep
        FOREIGN KEY (rep_id)
        REFERENCES medical_reps (rep_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_campaign_engagement_territory
        FOREIGN KEY (territory_id)
        REFERENCES territories (territory_id)
        ON DELETE RESTRICT
);


-- Indexes for common analysis joins and filters.
CREATE INDEX idx_hcps_territory_id
    ON hcps (territory_id);

CREATE INDEX idx_medical_reps_territory_id
    ON medical_reps (territory_id);

CREATE INDEX idx_campaigns_product_id
    ON campaigns (product_id);

CREATE INDEX idx_campaigns_territory_id
    ON campaigns (territory_id);

CREATE INDEX idx_hcp_calls_hcp_id
    ON hcp_calls (hcp_id);

CREATE INDEX idx_hcp_calls_rep_id
    ON hcp_calls (rep_id);

CREATE INDEX idx_hcp_calls_territory_id
    ON hcp_calls (territory_id);

CREATE INDEX idx_hcp_calls_product_id
    ON hcp_calls (product_id);

CREATE INDEX idx_hcp_calls_call_date
    ON hcp_calls (call_date);

CREATE INDEX idx_sales_hcp_id
    ON sales (hcp_id);

CREATE INDEX idx_sales_rep_id
    ON sales (rep_id);

CREATE INDEX idx_sales_territory_id
    ON sales (territory_id);

CREATE INDEX idx_sales_product_id
    ON sales (product_id);

CREATE INDEX idx_sales_sale_date
    ON sales (sale_date);

CREATE INDEX idx_sales_sale_month
    ON sales (sale_month);

CREATE INDEX idx_campaign_engagement_campaign_id
    ON campaign_engagement (campaign_id);

CREATE INDEX idx_campaign_engagement_hcp_id
    ON campaign_engagement (hcp_id);

CREATE INDEX idx_campaign_engagement_rep_id
    ON campaign_engagement (rep_id);

CREATE INDEX idx_campaign_engagement_territory_id
    ON campaign_engagement (territory_id);
