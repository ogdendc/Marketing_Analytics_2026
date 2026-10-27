# Vega-Lite Custom Viz gallery for AI/BI dashboards (marketing analytics)

Five Vega-Lite specs that cover chart types the built-in AI/BI visualizations do not handle well. Each one is paired with its dataset SQL, a Fields mapping, and a Genie Code prompt.

Placeholders: all SQL uses `your_catalog.your_schema`. Replace it with your catalog and schema before you run the queries.

Feature status: Custom Viz is in Public Preview. Specs use the Vega-Lite v6 `$schema`, as in the current docs. The docs also show v5 examples. The renderer's Vega-Lite version in the workspace is not documented, so re-check the preview PNGs against the dashboard if you change the schema version.

## Source tables

| Table | Grain | Used by |
|---|---|---|
| `campaign_results_detail` | one row per household x campaign (4,381 rows) | charts 1, 2, 4 |
| `campaign_lift_roi` | campaign x segment (7 rows) | charts 3, 5 |

Campaigns: Spring Retirement Readiness (Email), Annual Wealth Review Invitation (Direct Mail), Rollover Retargeting (Digital).

## How to use any spec

1. In an AI/BI dashboard, add a **dataset** from the SQL in the chart's section below. Use **Add SQL dataset**.
2. Add a visualization, pick the dataset, and choose **Custom Viz** under **Advanced**.
3. In **Fields**, add each field listed for the chart and set its **Name** to the exact name in the table. Each Name must match a column alias in the SQL, and specs reference fields by these names.
4. Paste the contents of the chart's `.json` into the **Vega-Lite specification** editor.

For charts 1 to 4 and 5, the Fields section maps name to expression as shown. Use plain column references (for example, `campaign_name` maps to `campaign_name`). The SQL already does the aggregation.

---

## 1. Bullet: Target CVR vs Holdout CVR per campaign

File: `01_bullet_cvr_target_vs_holdout.json` · Preview: `01_bullet_cvr_target_vs_holdout.preview.png`

**What it shows.** One row per campaign. The dark bar is the Target conversion rate. The red tick is the Holdout conversion rate, drawn as the reference. Where the tick sits past the bar, the campaign is underperforming its control. Tooltips show both rates.

**Dataset SQL** (`sql/01_bullet_target_vs_holdout_cvr.sql`)
```sql
SELECT
  campaign_name,
  CAST(SUM(CASE WHEN audience_group = 'Target' THEN converted END) AS DOUBLE)
    / SUM(CASE WHEN audience_group = 'Target' THEN 1 END) AS target_cvr,
  CAST(SUM(CASE WHEN audience_group = 'Holdout' THEN converted END) AS DOUBLE)
    / SUM(CASE WHEN audience_group = 'Holdout' THEN 1 END) AS holdout_cvr
FROM your_catalog.your_schema.campaign_results_detail
GROUP BY campaign_name
ORDER BY campaign_name
```

**Fields**

| Name | Expression |
|---|---|
| `campaign_name` | `campaign_name` |
| `target_cvr` | `target_cvr` |
| `holdout_cvr` | `holdout_cvr` |

**Genie Code prompt.** "Write a Vega-Lite v6 Custom Viz spec for a bullet chart with one row per campaign. Use the field `campaign_name` for the category and `target_cvr` for a dark bar and `holdout_cvr` for a red reference tick. Format both as percentages. Use `"data": {"name": "databricks_query"}`, `"width": "container"`, `"height": "container"`, and autosize fit."

---

## 2. Marketing funnel per campaign (Target audience only)

File: `02_funnel_target_stages.json` · Preview: `02_funnel_target_stages.preview.png`

**What it shows.** Funnel stages delivered, opened, clicked, responded, converted for the Target audience, one panel per campaign (facet). The bars are centered on a common axis, so drop-off reads from the width. Direct Mail has no open or click tracking (NULL in the data), so its opened and clicked rows are omitted, not drawn as zero. The spec drops NULL stages with `filter: datum.count != null`.

**Dataset SQL** (`sql/02_funnel_target_stages.sql`)
```sql
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
```

**Fields**

| Name | Expression |
|---|---|
| `campaign_name` | `campaign_name` |
| `delivered` | `delivered` |
| `opened` | `opened` |
| `clicked` | `clicked` |
| `responded` | `responded` |
| `converted` | `converted` |

**Genie Code prompt.** "Write a Vega-Lite v6 Custom Viz spec for a centered funnel per campaign. Fold the columns delivered, opened, clicked, responded, converted into stage and count. Drop null counts. Facet by `campaign_name` in rows. Center each stage bar on zero by computing bar_left and bar_right from count. Use `data.name` `databricks_query`."

---

## 3. Waterfall: net value by campaign (with a negative Digital step)

File: `03_waterfall_net_by_campaign.json` · Preview: `03_waterfall_net_by_campaign.preview.png`

**What it shows.** Each campaign's net is incremental value minus cost. The bars are ordered by net, and a running total is built with a Vega window transform. Positive steps are green, negative steps are red, and the final Total is navy. The Total row is produced in SQL. Rollover Retargeting (Digital) is the red negative step.

**Scale caveat.** The bars are linear. Direct Mail's net (about $1.23M) is about 350 times larger than Digital's net (about -$3.5K), so the red step is only a thin sliver. The value is labelled (-$3,535) so it still reads. A symlog scale made the step no more visible in testing, so the spec uses linear. To emphasize the negative campaign, show a separate chart of net by campaign, or use ROI instead of dollars.

**Dataset SQL** (`sql/03_waterfall_net_by_campaign.sql`)
```sql
WITH per_campaign AS (
  SELECT
    campaign_name,
    CAST(SUM(incremental_value) AS DOUBLE) AS incremental_value,
    CAST(SUM(cost) AS DOUBLE)              AS cost
  FROM your_catalog.your_schema.campaign_lift_roi
  GROUP BY campaign_name
),
steps AS (
  SELECT
    campaign_name,
    incremental_value,
    cost,
    incremental_value - cost AS net_value,
    'step' AS bar_type,
    ROW_NUMBER() OVER (ORDER BY incremental_value - cost DESC) AS step_order
  FROM per_campaign
),
total AS (
  SELECT
    'Total' AS campaign_name,
    SUM(incremental_value) AS incremental_value,
    SUM(cost) AS cost,
    SUM(incremental_value - cost) AS net_value,
    'total' AS bar_type,
    99 AS step_order
  FROM per_campaign
)
SELECT * FROM steps
UNION ALL
SELECT * FROM total
ORDER BY step_order
```

**Fields**

| Name | Expression |
|---|---|
| `campaign_name` | `campaign_name` |
| `incremental_value` | `incremental_value` |
| `cost` | `cost` |
| `net_value` | `net_value` |
| `bar_type` | `bar_type` |
| `step_order` | `step_order` |

**Genie Code prompt.** "Write a Vega-Lite v6 Custom Viz waterfall. Use a window sum over `net_value` ordered by `step_order` to get a running total. The bar goes from the previous running total to the current one. Rows where `bar_type` is `total` start at zero. Color positive steps green, negative steps red, and the total navy. Label each bar with `net_value` formatted as dollars."

---

## 4. Dumbbell: Target vs Holdout CVR by segment

File: `04_dumbbell_cvr_by_segment.json` · Preview: `04_dumbbell_cvr_by_segment.preview.png`

**What it shows.** One row per household segment. A line joins the Holdout rate (grey dot) to the Target rate (dot). The line and the Target dot are green when lift is above zero and red otherwise. Tooltips show household counts.

**Small-sample caveat.** Ultra HNW has 2 Holdout households and High Net Worth has 29. Their Holdout rates are unstable. Check the holdout count tooltip before quoting a lift for those segments.

**Dataset SQL** (`sql/04_dumbbell_cvr_by_segment.sql`)
```sql
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
```

**Fields**

| Name | Expression |
|---|---|
| `segment` | `segment` |
| `target_cvr` | `target_cvr` |
| `holdout_cvr` | `holdout_cvr` |
| `lift` | `lift` |
| `target_households` | `target_households` |
| `holdout_households` | `holdout_households` |

**Genie Code prompt.** "Write a Vega-Lite v6 Custom Viz dumbbell chart. Y axis is `segment`, sorted by `lift` descending. Draw a rule from `holdout_cvr` to `target_cvr`, colored green when `lift` is above zero and red otherwise. Draw points for both rates, using a fold. Holdout points are grey and Target points take the same lift color. Use percent format."

---

## 5. Clickable campaign bars that drive dashboard cross-filtering

File: `05_crossfilter_campaign_bars.json` · Preview: `05_crossfilter_campaign_bars.preview.png`

**What it shows.** Incremental value by campaign. Clicking a bar makes it the cross-filter source for other widgets on the same dataset. The selection is a point param named exactly `databricks_mark_selection`, on the dimension field `campaign_name`. Unselected bars dim, and the selected bar gets a theme-colored stroke (`colors.markHighlightColor`).

**Dataset SQL** (`sql/05_crossfilter_incremental_by_campaign.sql`)
```sql
SELECT
  campaign_name,
  CAST(SUM(incremental_value) AS DOUBLE) AS incremental_value,
  CAST(SUM(cost) AS DOUBLE)              AS cost
FROM your_catalog.your_schema.campaign_lift_roi
GROUP BY campaign_name
ORDER BY campaign_name
```

**Fields**

| Name | Expression |
|---|---|
| `campaign_name` | `campaign_name` |
| `incremental_value` | `incremental_value` |
| `cost` | `cost` |

**Testing the cross-filter.** Put any other widget on the same dataset (a Custom Viz bar of `cost`, or a built-in table) so there is a filtered target to watch. Other widgets on the same dataset update when you click a bar.

**Genie Code prompt.** "Write a Vega-Lite v6 Custom Viz bar chart. Add a point selection param named exactly `databricks_mark_selection` on the field `campaign_name`. Dim unselected bars with fillOpacity 0.3. Highlight the selected bar with a stroke of `{"expr": "colors.markHighlightColor"}`, strokeWidth 2. Use `data.name` `databricks_query`."

---

## Notes and gotchas

- **Field naming.** Specs reference fields by Name, not by raw column name. Names must match the dataset column aliases exactly.
- **Container sizing.** `"width": "container"` and `"height": "container"` with autosize fit work for single and layered views. Facet charts (chart 2) warn in the console that container sizing applies only to single and layered views. Chart 2 sets a fixed row step height instead.
- **Theme signal.** `colors` (for example, `colors.markHighlightColor`) is injected by Databricks. Plain vega-embed does not define it. The local harness adds a test-only `colors` param. The saved specs do not include that param, so they stay correct for the workspace.
- **Cross-filter.** Only dimension fields belong in `select.fields`. Measures cannot drive a cross-filter. Only `type: "point"` selections work, and only the exact name `databricks_mark_selection` triggers cross-filtering.
- **Images.** No image marks are used. Treemaps are not supported in Vega-Lite and are not used.
- **Campaign mix.** The three campaigns are a small sample. Treat lift values as directional.
