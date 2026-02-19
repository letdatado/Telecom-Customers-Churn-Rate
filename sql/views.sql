DROP VIEW IF EXISTS vw_churn_training_dataset;

CREATE VIEW vw_churn_training_dataset AS
SELECT
    dc.customer_id,

    -- Customer dimension
    dc.gender,
    dc.senior_citizen,
    dc.partner,
    dc.dependents,
    dc.country,
    dc.state,

    -- Contract dimension
    dcon.contract_type,
    dcon.paperless_billing,
    dcon.payment_method,

    -- Services dimension
    ds.phone_service,
    ds.multiple_lines,
    ds.internet_service,
    ds.online_security,
    ds.online_backup,
    ds.device_protection,
    ds.tech_support,
    ds.streaming_tv,
    ds.streaming_movies,

    -- Fact metrics
    f.tenure_months,
    f.monthly_charges,
    f.total_charges,
    f.cltv,

    -- Target
    CASE WHEN f.churn_label = 'Yes' THEN 1 ELSE 0 END AS churn_target,

    -- Snapshot metadata
    f.snapshot_date

FROM fact_customer_snapshot f
JOIN dim_customer dc ON dc.customer_key = f.customer_key
JOIN dim_contract dcon ON dcon.contract_key = f.contract_key
JOIN dim_services ds ON ds.services_key = f.services_key;
