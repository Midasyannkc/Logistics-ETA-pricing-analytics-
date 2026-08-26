-- Gold-layer views in BigQuery, built on top of the Delta table exported
-- from Databricks (gold.eta_pricing_features). Tableau connects directly
-- to `kpi_eta_accuracy` and `kpi_pricing_elasticity`; Omni's semantic
-- layer is modeled on top of the same two views so metric definitions
-- can't drift between the two BI tools.

CREATE OR REPLACE VIEW `logistics_analytics.kpi_eta_accuracy` AS
SELECT
  region,
  DATE(requested_at) AS trip_date,
  COUNT(*) AS trips,
  AVG(ABS(actual_eta_minutes - predicted_eta_minutes)) AS mae_minutes,
  SQRT(AVG(POW(actual_eta_minutes - predicted_eta_minutes, 2))) AS rmse_minutes
FROM `logistics_analytics.gold_eta_pricing_features`
GROUP BY region, trip_date;

CREATE OR REPLACE VIEW `logistics_analytics.kpi_pricing_elasticity` AS
SELECT
  CASE
    WHEN surge_multiplier < 1.1 THEN '1.0-1.1'
    WHEN surge_multiplier < 1.3 THEN '1.1-1.3'
    WHEN surge_multiplier < 1.5 THEN '1.3-1.5'
    WHEN surge_multiplier < 1.75 THEN '1.5-1.75'
    WHEN surge_multiplier < 2.0 THEN '1.75-2.0'
    ELSE '2.0-2.5'
  END AS surge_bin,
  COUNT(*) AS trips,
  AVG(CAST(converted AS INT64)) AS conversion_rate
FROM `logistics_analytics.gold_eta_pricing_features`
GROUP BY surge_bin;

CREATE OR REPLACE VIEW `logistics_analytics.kpi_utilization_by_region` AS
SELECT
  region,
  COUNT(*) AS trips,
  AVG(CAST(driver_available AS INT64)) AS driver_availability_rate,
  AVG(CAST(converted AS INT64)) AS conversion_rate
FROM `logistics_analytics.gold_eta_pricing_features`
GROUP BY region;
