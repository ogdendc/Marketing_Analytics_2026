-- Dataset for chart 4 (dumbbell): Target vs Holdout CVR by segment, pooled across campaigns
WITH seg AS (
  SELECT
    segment,
    CAST(SUM(CASE WHEN audience_group = 'Target' THEN converted END) AS DOUBLE)
      / SUM(CASE WHEN audience_group = 'Target' THEN 1 END) AS target_cvr,
    CAST(SUM(CASE WHEN audience_group = 'Holdout' THEN converted END) AS DOUBLE)
      / SUM(CASE WHEN audience_group = 'Holdout' THEN 1 END) AS holdout_cvr,
    SUM(CASE WHEN audience_group = 'Target' THEN 1 ELSE 0 END)  AS target_households,
    SUM(CASE WHEN audience_group = 'Holdout' THEN 1 ELSE 0 END) AS holdout_households
  FROM your_catalog.your_schema.campaign_results_detail
  GROUP BY segment
)
SELECT
  segment,
  ROUND(target_cvr, 4)  AS target_cvr,
  ROUND(holdout_cvr, 4) AS holdout_cvr,
  ROUND(target_cvr - holdout_cvr, 4) AS lift,
  target_households,
  holdout_households
FROM seg
ORDER BY lift DESC
