-- 1) Churn rate by contract type
SELECT
  contract_type,
  ROUND(100.0 * AVG(churn_target), 2) AS churn_rate_pct,
  COUNT(*) AS customers
FROM vw_churn_training_dataset
GROUP BY contract_type
ORDER BY churn_rate_pct DESC;

-- 2) Churn rate by tenure band
SELECT
  CASE
    WHEN tenure_months BETWEEN 0 AND 12 THEN '0-12'
    WHEN tenure_months BETWEEN 13 AND 24 THEN '13-24'
    WHEN tenure_months BETWEEN 25 AND 48 THEN '25-48'
    ELSE '49+'
  END AS tenure_band,
  ROUND(100.0 * AVG(churn_target), 2) AS churn_rate_pct,
  COUNT(*) AS customers
FROM vw_churn_training_dataset
GROUP BY tenure_band
ORDER BY tenure_band;

-- 3) Revenue at risk (monthly charges of churners)
SELECT
  churn_target,
  ROUND(SUM(monthly_charges), 2) AS total_monthly_charges,
  ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
  COUNT(*) AS customers
FROM vw_churn_training_dataset
GROUP BY churn_target;

-- 4) Internet service + churn
SELECT
  internet_service,
  ROUND(100.0 * AVG(churn_target), 2) AS churn_rate_pct,
  COUNT(*) AS customers
FROM vw_churn_training_dataset
GROUP BY internet_service
ORDER BY churn_rate_pct DESC;

-- 5) Add-on count (service bundle depth) vs churn
WITH svc AS (
  SELECT
    churn_target,
    (CASE WHEN online_security = 'Yes' THEN 1 ELSE 0 END +
     CASE WHEN online_backup = 'Yes' THEN 1 ELSE 0 END +
     CASE WHEN device_protection = 'Yes' THEN 1 ELSE 0 END +
     CASE WHEN tech_support = 'Yes' THEN 1 ELSE 0 END +
     CASE WHEN streaming_tv = 'Yes' THEN 1 ELSE 0 END +
     CASE WHEN streaming_movies = 'Yes' THEN 1 ELSE 0 END
    ) AS addon_count
  FROM vw_churn_training_dataset
)
SELECT
  addon_count,
  ROUND(100.0 * AVG(churn_target), 2) AS churn_rate_pct,
  COUNT(*) AS customers
FROM svc
GROUP BY addon_count
ORDER BY addon_count;
