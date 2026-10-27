-- Dataset for chart 2 (funnel): Target audience only, stage counts per campaign
SELECT
  campaign_name,
  SUM(delivered) AS delivered,
  SUM(opened)    AS opened,
  SUM(clicked)   AS clicked,
  SUM(responded) AS responded,
  SUM(converted) AS converted
FROM your_catalog.your_schema.campaign_results_detail
WHERE audience_group = 'Target'
GROUP BY campaign_name
ORDER BY campaign_name
