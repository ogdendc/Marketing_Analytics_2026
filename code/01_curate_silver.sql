-- ============================================================================
--  Marketing Analytics Workshop  ·  Step 1 — Curate (Silver): join external
--  campaign data to firm data
-- ----------------------------------------------------------------------------
--  This is the heart of "does the outside data add value?": we take the uploaded
--  campaign results and enrich each row with what the firm already knows about
--  the household (segment, region, AUM, preferred channel, engagement) and the
--  campaign (name, channel, objective, unit cost).
--
--  Tip: ask Genie Code (the assistant) to write this join for you — describe it
--  in plain English and review the SQL it produces.
--
--  Find-and-replace your_catalog / your_schema before running.
-- ============================================================================

CREATE OR REPLACE TABLE your_catalog.your_schema.campaign_results_silver AS
SELECT
  cr.campaign_id,
  c.campaign_name,
  c.channel,
  c.objective,
  c.cost_per_contact,
  cr.household_id,
  cr.audience_group,                 -- 'Target' (contacted) or 'Holdout' (control)
  h.segment,
  h.value_tier,
  h.region,
  h.primary_channel AS preferred_channel,
  h.household_aum,
  h.engagement_score,
  h.advisor_id,
  cr.send_date,
  cr.delivered,
  cr.opened,                         -- null for channels without open tracking (e.g. Direct Mail)
  cr.clicked,
  cr.responded,
  cr.converted,
  cr.conversion_value,
  cr.contact_cost
FROM your_catalog.your_schema.campaign_results_bronze cr
JOIN your_catalog.your_schema.households h ON cr.household_id = h.household_id
JOIN your_catalog.your_schema.campaigns  c ON cr.campaign_id = c.campaign_id;

SELECT * FROM your_catalog.your_schema.campaign_results_silver LIMIT 20;
