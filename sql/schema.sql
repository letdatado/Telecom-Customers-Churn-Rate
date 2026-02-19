-- =========================
-- Dimension: Customer
-- =========================
CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT UNIQUE,
    gender TEXT,
    senior_citizen INTEGER,
    partner TEXT,
    dependents TEXT,
    country TEXT,
    state TEXT
);

-- =========================
-- Dimension: Contract
-- =========================
CREATE TABLE dim_contract (
    contract_key INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_type TEXT,
    paperless_billing TEXT,
    payment_method TEXT
);

-- =========================
-- Dimension: Services
-- =========================
CREATE TABLE dim_services (
    services_key INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_service TEXT,
    multiple_lines TEXT,
    internet_service TEXT,
    online_security TEXT,
    online_backup TEXT,
    device_protection TEXT,
    tech_support TEXT,
    streaming_tv TEXT,
    streaming_movies TEXT
);

-- =========================
-- Fact: Customer Snapshot
-- =========================
CREATE TABLE fact_customer_snapshot (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_key INTEGER,
    contract_key INTEGER,
    services_key INTEGER,

    tenure_months INTEGER,
    monthly_charges REAL,
    total_charges REAL,
    cltv REAL,

    churn_label TEXT,
    snapshot_date TEXT,

    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    FOREIGN KEY (contract_key) REFERENCES dim_contract(contract_key),
    FOREIGN KEY (services_key) REFERENCES dim_services(services_key)
);
