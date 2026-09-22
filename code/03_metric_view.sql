-- ============================================================================
--  Marketing Analytics Workshop  ·  Step 3 — Metric view (semantic layer)
-- ----------------------------------------------------------------------------
--  A metric view defines governed dimensions and measures ONCE, so every
--  dashboard, Genie space, and query uses the same definition of "Conversion
--  Rate", "ROI", etc. Query it with the MEASURE() function (see bottom).
--
--  Find-and-replace your_catalog / your_schema before running.
-- ============================================================================

CREATE OR REPLACE VIEW your_catalog.your_schema.marketing_performance_metrics
WITH METRICS
LANGUAGE YAML
COMMENT 'Semantic layer for marketing campaign performance: governed dimensions + measures reused by dashboards and Genie.'
AS $$
version: 0.1
source: your_catalog.your_schema.campaign_results_silver
dimensions:
  - name: Campaign
    expr: campaign_name
  - name: Channel
    expr: channel
  - name: Segment
    expr: segment
  - name: Region
    expr: region
  - name: Audience Group
    expr: audience_group
  - name: Send Date
    expr: send_date
measures:
  - name: Contacts
    expr: COUNT(*)
  - name: Conversions
    expr: SUM(converted)
  - name: Conversion Rate
    expr: SUM(converted) / COUNT(*)
  - name: Conversion Value
    expr: SUM(conversion_value)
  - name: Campaign Cost
    expr: SUM(contact_cost)
  - name: Net Value
    expr: SUM(conversion_value) - SUM(contact_cost)
  - name: Cost per Conversion
    expr: SUM(contact_cost) / NULLIF(SUM(converted), 0)
$$;

-- Query a metric view with MEASURE(). Dimensions/measures are referenced by name.
SELECT `Channel`,
       MEASURE(`Conversions`)                 AS conversions,
       ROUND(MEASURE(`Conversion Rate`), 4)   AS conversion_rate,
       ROUND(MEASURE(`Net Value`), 0)         AS net_value
FROM your_catalog.your_schema.marketing_performance_metrics
WHERE `Audience Group` = 'Target'
GROUP BY `Channel`
ORDER BY net_value DESC;
