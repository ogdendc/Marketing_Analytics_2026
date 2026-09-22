-- ============================================================================
--  Marketing Analytics Workshop  ·  Declarative pipeline (alternative to 01+02)
-- ----------------------------------------------------------------------------
--  Same silver/gold curation as 01_curate_silver.sql + 02_curate_gold.sql, but
--  expressed DECLARATIVELY as a Lakeflow pipeline. You describe the target tables;
--  the engine manages dependencies, incremental refresh, and lineage — and you can
--  attach DATA-QUALITY expectations (see CONSTRAINT below).
--
--  How to run: Workflows → create a Lakeflow / DLT pipeline → point it at this file
--  → set the target catalog & schema → Start. (Bronze tables from 00_load_from_files.sql
--  must already exist.)
--
--  Find-and-replace your_catalog / your_schema before running.
-- ============================================================================

-- Silver: enriched, with a data-quality expectation
CREATE OR REFRESH MATERIALIZED VIEW campaign_results_silver
  (CONSTRAINT valid_audience EXPECT (audience_group IN ('Target','Holdout')) ON VIOLATION DROP ROW)
COMMENT 'Campaign results joined to firm household + campaign data.'
AS
SELECT
  cr.campaign_id, c.campaign_name, c.channel, c.objective, c.cost_per_contact,
  cr.household_id, cr.audience_group,
  h.segment, h.value_tier, h.region, h.primary_channel AS preferred_channel,
  h.household_aum, h.engagement_score, h.advisor_id,
  cr.send_date, cr.delivered, cr.opened, cr.clicked, cr.responded,
  cr.converted, cr.conversion_value, cr.contact_cost
FROM your_catalog.your_schema.campaign_results_bronze cr
JOIN your_catalog.your_schema.households h ON cr.household_id = h.household_id
JOIN your_catalog.your_schema.campaigns  c ON cr.campaign_id = c.campaign_id;

-- Gold: funnel + conversion metrics
CREATE OR REFRESH MATERIALIZED VIEW marketing_performance
COMMENT 'Funnel + conversion metrics by campaign, segment, and audience group.'
AS
SELECT campaign_id, campaign_name, channel, segment, audience_group,
       COUNT(*) AS contacts, SUM(delivered) AS delivered,
       SUM(COALESCE(opened,0)) AS opens, SUM(COALESCE(clicked,0)) AS clicks,
       SUM(responded) AS responses, SUM(converted) AS conversions,
       ROUND(SUM(conversion_value),2) AS conversion_value,
       ROUND(SUM(contact_cost),2) AS cost,
       ROUND(SUM(converted)/COUNT(*),4) AS conversion_rate
FROM LIVE.campaign_results_silver
GROUP BY campaign_id, campaign_name, channel, segment, audience_group;

-- Gold: lift vs holdout + ROI
CREATE OR REFRESH MATERIALIZED VIEW campaign_lift_roi
COMMENT 'Incremental lift vs holdout and ROI, by campaign and segment.'
AS
WITH agg AS (
  SELECT campaign_id, campaign_name, channel, segment, audience_group,
         COUNT(*) n, SUM(converted) conv, SUM(conversion_value) val, SUM(contact_cost) cost
  FROM LIVE.campaign_results_silver
  GROUP BY campaign_id, campaign_name, channel, segment, audience_group
),
t AS (SELECT * FROM agg WHERE audience_group='Target'),
h AS (SELECT campaign_id, segment, n hn, conv hconv FROM agg WHERE audience_group='Holdout')
SELECT t.campaign_id, t.campaign_name, t.channel, t.segment,
       t.n AS target_contacts, t.conv AS target_conversions,
       ROUND(t.conv/t.n,4) AS target_cvr,
       ROUND(COALESCE(h.hconv/NULLIF(h.hn,0),0),4) AS holdout_cvr,
       ROUND(t.conv/t.n - COALESCE(h.hconv/NULLIF(h.hn,0),0),4) AS lift,
       ROUND((t.conv/t.n - COALESCE(h.hconv/NULLIF(h.hn,0),0))*t.n) AS incremental_conversions,
       ROUND((t.conv/t.n - COALESCE(h.hconv/NULLIF(h.hn,0),0))*t.n*(t.val/NULLIF(t.conv,0)),2) AS incremental_value,
       ROUND(t.cost,2) AS cost,
       ROUND(((t.conv/t.n - COALESCE(h.hconv/NULLIF(h.hn,0),0))*t.n*(t.val/NULLIF(t.conv,0)) - t.cost)/NULLIF(t.cost,0),2) AS roi
FROM t LEFT JOIN h ON t.campaign_id=h.campaign_id AND t.segment=h.segment;
