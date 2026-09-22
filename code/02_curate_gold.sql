-- ============================================================================
--  Marketing Analytics Workshop  ·  Step 2 — Curate (Gold): the answer tables
-- ----------------------------------------------------------------------------
--  Two gold tables:
--    marketing_performance  — the funnel + conversion metrics, aggregated
--    campaign_lift_roi      — incremental LIFT vs. the holdout, and ROI
--
--  Key idea: a campaign only "adds value" if the Target group converts MORE than
--  the Holdout (control) group. That difference is the LIFT. Multiply the lift by
--  the number targeted and the average conversion value to get incremental value,
--  then compare to cost for ROI.
--
--  Find-and-replace your_catalog / your_schema before running.
-- ============================================================================

-- ---- Gold 1: funnel + conversion metrics by campaign x segment x audience group
CREATE OR REPLACE TABLE your_catalog.your_schema.marketing_performance AS
SELECT
  campaign_id, campaign_name, channel, segment, audience_group,
  COUNT(*)                          AS contacts,
  SUM(delivered)                    AS delivered,
  SUM(COALESCE(opened, 0))          AS opens,
  SUM(COALESCE(clicked, 0))         AS clicks,
  SUM(responded)                    AS responses,
  SUM(converted)                    AS conversions,
  ROUND(SUM(conversion_value), 2)   AS conversion_value,
  ROUND(SUM(contact_cost), 2)       AS cost,
  ROUND(SUM(converted) / COUNT(*), 4) AS conversion_rate
FROM your_catalog.your_schema.campaign_results_silver
GROUP BY campaign_id, campaign_name, channel, segment, audience_group;

-- ---- Gold 2: lift vs. holdout + ROI, by campaign x segment
CREATE OR REPLACE TABLE your_catalog.your_schema.campaign_lift_roi AS
WITH agg AS (
  SELECT campaign_id, campaign_name, channel, segment, audience_group,
         COUNT(*) n, SUM(converted) conv, SUM(conversion_value) val, SUM(contact_cost) cost
  FROM your_catalog.your_schema.campaign_results_silver
  GROUP BY campaign_id, campaign_name, channel, segment, audience_group
),
t AS (SELECT * FROM agg WHERE audience_group = 'Target'),
h AS (SELECT campaign_id, segment, n AS hn, conv AS hconv FROM agg WHERE audience_group = 'Holdout')
SELECT
  t.campaign_id, t.campaign_name, t.channel, t.segment,
  t.n                                                     AS target_contacts,
  t.conv                                                  AS target_conversions,
  ROUND(t.conv / t.n, 4)                                  AS target_cvr,
  h.hn                                                    AS holdout_contacts,
  ROUND(COALESCE(h.hconv / NULLIF(h.hn, 0), 0), 4)        AS holdout_cvr,
  ROUND(t.conv / t.n - COALESCE(h.hconv / NULLIF(h.hn, 0), 0), 4)               AS lift,
  ROUND((t.conv / t.n - COALESCE(h.hconv / NULLIF(h.hn, 0), 0)) * t.n)          AS incremental_conversions,
  ROUND(t.val / NULLIF(t.conv, 0), 2)                     AS avg_conversion_value,
  ROUND((t.conv / t.n - COALESCE(h.hconv / NULLIF(h.hn, 0), 0)) * t.n
        * (t.val / NULLIF(t.conv, 0)), 2)                 AS incremental_value,
  ROUND(t.cost, 2)                                        AS cost,
  ROUND(((t.conv / t.n - COALESCE(h.hconv / NULLIF(h.hn, 0), 0)) * t.n
         * (t.val / NULLIF(t.conv, 0)) - t.cost) / NULLIF(t.cost, 0), 2)        AS roi
FROM t LEFT JOIN h ON t.campaign_id = h.campaign_id AND t.segment = h.segment;

SELECT campaign_name, channel, segment, lift, incremental_value, cost, roi
FROM your_catalog.your_schema.campaign_lift_roi
ORDER BY roi DESC;
