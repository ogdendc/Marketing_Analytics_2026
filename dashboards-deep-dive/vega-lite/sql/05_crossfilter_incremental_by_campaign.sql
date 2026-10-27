-- Dataset for chart 5 (clickable campaign bars that drive dashboard cross-filtering)
SELECT
  campaign_name,
  CAST(SUM(incremental_value) AS DOUBLE) AS incremental_value,
  CAST(SUM(cost) AS DOUBLE)              AS cost
FROM your_catalog.your_schema.campaign_lift_roi
GROUP BY campaign_name
ORDER BY campaign_name
