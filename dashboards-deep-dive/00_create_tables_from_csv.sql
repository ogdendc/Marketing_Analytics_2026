-- ============================================================================
--  AI/BI Dashboards Deep Dive  ·  Create the gold tables from the CSV files
-- ----------------------------------------------------------------------------
--  Run this whole file in the SQL editor (Run all) to turn the five CSVs in
--  data/ into tables. It's the scripted alternative to uploading each file
--  with New → Add or upload data.
--
--  Before running:
--    1. Upload the five CSVs from data/ to a Unity Catalog volume folder.
--    2. Find-and-replace:
--         your_catalog.your_schema   → where the tables should go
--         /Volumes/your_catalog/your_schema/files/dashboards_deep_dive
--                                    → the volume folder holding the CSVs
--  Safe to re-run: every table is CREATE OR REPLACE. (_rescued_data is a
--  column read_files adds for malformed values; it is dropped to keep the tables clean.)
-- ============================================================================

-- CREATE SCHEMA IF NOT EXISTS your_catalog.your_schema;   -- uncomment if you can create schemas

-- Main fact table: one row per household per campaign (Target + Holdout).
CREATE OR REPLACE TABLE your_catalog.your_schema.campaign_results_detail
COMMENT 'One row per household per campaign, with household and campaign attributes'
AS SELECT * EXCEPT (_rescued_data) FROM read_files(
  '/Volumes/your_catalog/your_schema/files/dashboards_deep_dive/campaign_results_detail.csv',
  format => 'csv', header => true,
  schemaHints => 'household_aum BIGINT, send_date DATE, opened INT, clicked INT');

-- Daily send performance, Target audience only (trends and AI Forecast).
CREATE OR REPLACE TABLE your_catalog.your_schema.campaign_daily_performance
COMMENT 'Daily send performance by campaign (Target audience only)'
AS SELECT * EXCEPT (_rescued_data) FROM read_files(
  '/Volumes/your_catalog/your_schema/files/dashboards_deep_dive/campaign_daily_performance.csv',
  format => 'csv', header => true,
  schemaHints => 'send_date DATE, opens BIGINT, clicks BIGINT');

-- Headline lift and ROI by campaign and segment.
CREATE OR REPLACE TABLE your_catalog.your_schema.campaign_lift_roi
COMMENT 'Target-vs-Holdout lift, incremental value and ROI by campaign and segment'
AS SELECT * EXCEPT (_rescued_data) FROM read_files(
  '/Volumes/your_catalog/your_schema/files/dashboards_deep_dive/campaign_lift_roi.csv',
  format => 'csv', header => true);

-- Household dimension (relationships exercise).
-- value_tier codes like T1 look like times to the CSV reader, so pin them to STRING.
CREATE OR REPLACE TABLE your_catalog.your_schema.households
COMMENT 'One row per household (firm data)'
AS SELECT * EXCEPT (_rescued_data) FROM read_files(
  '/Volumes/your_catalog/your_schema/files/dashboards_deep_dive/households.csv',
  format => 'csv', header => true,
  schemaHints => 'value_tier STRING');

-- Campaign reference table.
CREATE OR REPLACE TABLE your_catalog.your_schema.campaigns
COMMENT 'One row per campaign'
AS SELECT * EXCEPT (_rescued_data) FROM read_files(
  '/Volumes/your_catalog/your_schema/files/dashboards_deep_dive/campaigns.csv',
  format => 'csv', header => true);

-- Check: expect 4381, 81, 7, 2972, 3.
SELECT 'campaign_results_detail' AS table_name, COUNT(*) AS row_count FROM your_catalog.your_schema.campaign_results_detail
UNION ALL SELECT 'campaign_daily_performance', COUNT(*) FROM your_catalog.your_schema.campaign_daily_performance
UNION ALL SELECT 'campaign_lift_roi', COUNT(*) FROM your_catalog.your_schema.campaign_lift_roi
UNION ALL SELECT 'households', COUNT(*) FROM your_catalog.your_schema.households
UNION ALL SELECT 'campaigns', COUNT(*) FROM your_catalog.your_schema.campaigns;
