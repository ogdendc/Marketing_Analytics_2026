-- ============================================================================
--  Marketing Analytics Workshop  ·  Step 4 — Analysis: is the campaign working?
-- ----------------------------------------------------------------------------
--  A set of SQL you can run and adapt. Try asking Genie Code to modify any of
--  these ("break this out by region", "only show negative-ROI segments", ...).
--
--  Find-and-replace your_catalog / your_schema before running.
-- ============================================================================

-- 1) Conversion funnel by campaign (targeted audience)
SELECT campaign_name, channel,
       SUM(contacts) AS contacts, SUM(delivered) AS delivered,
       SUM(opens) AS opens, SUM(clicks) AS clicks, SUM(conversions) AS conversions,
       ROUND(SUM(conversions) / SUM(contacts), 4) AS conversion_rate
FROM your_catalog.your_schema.marketing_performance
WHERE audience_group = 'Target'
GROUP BY campaign_name, channel
ORDER BY conversion_rate DESC;

-- 2) THE LIFT REVEAL — did the campaign beat its control group?
--    A campaign with lift ~ 0 spent money but changed nothing.
SELECT campaign_name, channel,
       ROUND(AVG(target_cvr), 4)  AS avg_target_cvr,
       ROUND(AVG(holdout_cvr), 4) AS avg_holdout_cvr,
       ROUND(AVG(lift), 4)        AS avg_lift,
       SUM(incremental_conversions) AS incremental_conversions,
       CAST(SUM(cost) AS BIGINT)  AS spend
FROM your_catalog.your_schema.campaign_lift_roi
GROUP BY campaign_name, channel
ORDER BY avg_lift DESC;

-- 3) ROI by campaign — the bottom line
SELECT campaign_name, channel,
       CAST(SUM(incremental_value) AS BIGINT) AS incremental_value,
       CAST(SUM(cost) AS BIGINT)              AS spend,
       ROUND((SUM(incremental_value) - SUM(cost)) / NULLIF(SUM(cost), 0), 1) AS roi
FROM your_catalog.your_schema.campaign_lift_roi
GROUP BY campaign_name, channel
ORDER BY roi DESC;

-- 4) WHERE to double down — best segment x campaign combinations by ROI
SELECT campaign_name, channel, segment,
       target_contacts, lift, roi,
       CAST(incremental_value AS BIGINT) AS incremental_value
FROM your_catalog.your_schema.campaign_lift_roi
ORDER BY roi DESC
LIMIT 10;

-- 5) WHERE to cut — segment x campaign combinations that lost money
SELECT campaign_name, channel, segment, lift, CAST(cost AS BIGINT) AS spend, roi
FROM your_catalog.your_schema.campaign_lift_roi
WHERE roi < 0
ORDER BY roi ASC;

-- 6) Channel economics (targeted) — net value by channel
SELECT channel,
       SUM(conversions) AS conversions,
       ROUND(SUM(conversions) / SUM(contacts), 4) AS conversion_rate,
       CAST(SUM(conversion_value) AS BIGINT) AS gross_value,
       CAST(SUM(cost) AS BIGINT)             AS spend,
       CAST(SUM(conversion_value) - SUM(cost) AS BIGINT) AS net_value
FROM your_catalog.your_schema.marketing_performance
WHERE audience_group = 'Target'
GROUP BY channel
ORDER BY net_value DESC;

-- 7) A recommendation flag per campaign (verdict)
SELECT campaign_name, channel,
       ROUND((SUM(incremental_value) - SUM(cost)) / NULLIF(SUM(cost), 0), 1) AS roi,
       CASE
         WHEN (SUM(incremental_value) - SUM(cost)) / NULLIF(SUM(cost), 0) >= 1  THEN 'SCALE — strong positive ROI'
         WHEN (SUM(incremental_value) - SUM(cost)) / NULLIF(SUM(cost), 0) > 0   THEN 'KEEP — modest positive ROI'
         ELSE 'CUT / REALLOCATE — no incremental value'
       END AS recommendation
FROM your_catalog.your_schema.campaign_lift_roi
GROUP BY campaign_name, channel
ORDER BY roi DESC;

-- 8) (Optional) AI in SQL — have a model draft a plain-English recommendation.
--    Uncomment to run; uses a built-in foundation model, no setup required.
-- SELECT ai_query(
--   'databricks-meta-llama-3-3-70b-instruct',
--   CONCAT('In two sentences, give a marketing manager a recommendation for this campaign. ',
--          'Campaign: ', campaign_name, ' (', channel, '). ROI: ', CAST(roi AS STRING), '. ',
--          'Best segment: ', segment, '.')
-- ) AS recommendation
-- FROM your_catalog.your_schema.campaign_lift_roi
-- ORDER BY roi DESC LIMIT 3;
