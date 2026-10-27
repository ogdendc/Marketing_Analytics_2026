-- Dataset for chart 1 (bullet): conversion rate per campaign, Target vs Holdout
SELECT
  campaign_name,
  CAST(SUM(CASE WHEN audience_group = 'Target' THEN converted END) AS DOUBLE)
    / SUM(CASE WHEN audience_group = 'Target' THEN 1 END) AS target_cvr,
  CAST(SUM(CASE WHEN audience_group = 'Holdout' THEN converted END) AS DOUBLE)
    / SUM(CASE WHEN audience_group = 'Holdout' THEN 1 END) AS holdout_cvr
FROM your_catalog.your_schema.campaign_results_detail
GROUP BY campaign_name
ORDER BY campaign_name
