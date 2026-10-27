-- Dataset for chart 3 (waterfall): per-campaign net = incremental value - cost, plus a Total row
WITH per_campaign AS (
  SELECT
    campaign_name,
    CAST(SUM(incremental_value) AS DOUBLE) AS incremental_value,
    CAST(SUM(cost) AS DOUBLE)              AS cost
  FROM your_catalog.your_schema.campaign_lift_roi
  GROUP BY campaign_name
),
steps AS (
  SELECT
    campaign_name,
    incremental_value,
    cost,
    incremental_value - cost AS net_value,
    'step' AS bar_type,
    ROW_NUMBER() OVER (ORDER BY incremental_value - cost DESC) AS step_order
  FROM per_campaign
),
total AS (
  SELECT
    'Total' AS campaign_name,
    SUM(incremental_value) AS incremental_value,
    SUM(cost) AS cost,
    SUM(incremental_value - cost) AS net_value,
    'total' AS bar_type,
    99 AS step_order
  FROM per_campaign
)
SELECT * FROM steps
UNION ALL
SELECT * FROM total
ORDER BY step_order
