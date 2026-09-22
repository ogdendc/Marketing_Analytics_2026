-- ============================================================================
--  Marketing Analytics Workshop  ·  Step 0 — Get data in (load from files)
-- ----------------------------------------------------------------------------
--  Loads three files:
--    households.csv          -> firm-side household master ("firm data")
--    campaigns.csv           -> campaign dimension        (external upload)
--    campaign_results.csv    -> campaign results / fact   (external upload)
--
--  In practice your household/firm data already lives in the lakehouse; here we
--  load it from a file so the workshop is self-contained. The campaign files are
--  the "outside the platform" data an analyst uploads to analyze alongside it.
--
--  SETUP (do once):
--    1. Create a schema to work in, e.g.:  CREATE SCHEMA IF NOT EXISTS main.marketing_analytics;
--    2. Create a Volume for the files:      CREATE VOLUME IF NOT EXISTS main.marketing_analytics.files;
--    3. Upload the 3 CSVs (Catalog Explorer > your Volume > Upload) OR the UI
--       "Add data > Create or modify table" flow.
--    4. Find-and-replace  your_catalog  and  your_schema  below with your values.
-- ============================================================================

-- Firm data: one row per household
CREATE OR REPLACE TABLE your_catalog.your_schema.households AS
SELECT * FROM read_files(
  '/Volumes/your_catalog/your_schema/files/households.csv',
  format => 'csv', header => true, schemaEvolutionMode => 'none');

-- External upload: campaign dimension (one row per campaign)
CREATE OR REPLACE TABLE your_catalog.your_schema.campaigns AS
SELECT * FROM read_files(
  '/Volumes/your_catalog/your_schema/files/campaigns.csv',
  format => 'csv', header => true, schemaEvolutionMode => 'none');

-- External upload: campaign results (fact) — Target + Holdout, one row per household per campaign
CREATE OR REPLACE TABLE your_catalog.your_schema.campaign_results_bronze AS
SELECT * FROM read_files(
  '/Volumes/your_catalog/your_schema/files/campaign_results.csv',
  format => 'csv', header => true, schemaEvolutionMode => 'none');

-- Sanity check
SELECT 'households'              AS table_name, count(*) AS rows FROM your_catalog.your_schema.households
UNION ALL SELECT 'campaigns',               count(*) FROM your_catalog.your_schema.campaigns
UNION ALL SELECT 'campaign_results_bronze', count(*) FROM your_catalog.your_schema.campaign_results_bronze;
