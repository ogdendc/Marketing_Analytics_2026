# Build the dashboard with Genie Code (no hand-building)

Instead of dragging widgets one by one, describe the dashboard you want and let **Genie Code**
generate it, then refine. Below are prompts that work well against the curated tables.

## Starter prompt
> Create an AI/BI dashboard for marketing campaign performance using
> `your_catalog.your_schema.campaign_lift_roi` and `your_catalog.your_schema.marketing_performance`.
> Include:
> 1. A bar chart of **ROI by campaign** (from campaign_lift_roi, aggregated by campaign_name).
> 2. A grouped bar of **target vs. holdout conversion rate** by campaign (the "lift" view).
> 3. **Net value by channel** (marketing_performance, audience_group = 'Target').
> 4. A table of **segment-level ROI** (campaign_name, segment, lift, roi, incremental_value),
>    sorted by ROI descending.
> Add a dashboard filter on **campaign_name**.

## Refinement prompts
- > Add a big-number tile for total incremental value and total spend across all campaigns.
- > Format ROI as a number with 1 decimal and incremental_value as currency.
- > Add a bar chart of ROI by segment for the Rollover Retargeting campaign only, and title it
  >  "Digital retargeting: no incremental return".
- > Color the ROI bars red when ROI is negative.

## Talking points while it builds
- Genie Code writes the datasets (SQL) and lays out the widgets — you review the SQL it used.
- Point the dashboard's datasets at the **metric view** (`marketing_performance_metrics`) where
  possible, so KPIs match everywhere.
- Publish with an embedded Genie space so viewers can ask follow-up questions (Module 9).

## If you want a guaranteed fallback
Keep [`code/04_analysis.sql`](../code/04_analysis.sql) open — each query there maps to one of the
widgets above and can be pasted into a dashboard dataset directly if you'd rather not rely on the
live generation during the session.
