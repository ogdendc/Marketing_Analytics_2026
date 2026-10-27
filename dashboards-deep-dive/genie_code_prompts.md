# Genie Code prompt library: AI/BI dashboards deep dive

Copy-paste prompts for each module. Open a new dashboard (**New → Dashboard**) and use the
**Genie Code** panel.

Conventions used below:
- Replace `your_catalog.your_schema` with the catalog and schema where you created the tables
  (see Module 0 in the [README](README.md)).
- **Set Genie Code to Auto** before you start, so it doesn't stop for approval at every step.
  Otherwise click **Allow** (or **Always allow** for the session) when it asks.
- **Keep the browser tab open while Genie Code is working.** Switching tabs stops the agent.

Each module has prompts to paste, "✅ You should see" numbers to check against, and a
**Your turn** challenge.

---

## Module 1 · Zero to dashboard in one prompt

**Main prompt**
```
Build a dashboard called "Campaign Performance" using the table
your_catalog.your_schema.campaign_results_detail.
Our marketing team runs campaigns with a Target group (contacted) and a Holdout group
(not contacted, used as a control). Include:
1. KPI tiles for Target contacts, conversions, conversion rate and net value
   (conversion_value minus contact_cost), Target audience only.
2. A bar chart of conversion rate by campaign_name, split by audience_group so Target and
   Holdout sit side by side.
3. A line chart of weekly conversions by send_date, one line per campaign_name.
4. A bar chart of net value by channel (Target only).
5. Add global filters for campaign_name and region that applies to all charts.
Name this first page "Key Stats".
```

✅ You should see: **3,725** Target contacts, **167** conversions, **4.5%** conversion rate,
net value about **$1.57M**. Target vs Holdout conversion rate: Annual Wealth Review 7.8% vs 0.75%;
Spring Retirement 6.0% vs 2.0%; Rollover Retargeting 2.1% vs 2.2%.

**Refinement prompts** (one at a time)
```
Format conversion rate as a percentage with 1 decimal and net value as currency in compact form ($1.6M).
```
```
Add a short text header at the top explaining that Holdout households were not contacted, so the gap between Target and Holdout is the lift the campaign caused.
```
```
Beautify this dashboard.
```

**Talking points:** Genie Code plans first, then writes each dataset's SQL. Open a dataset and
check it filtered to Target for the KPIs.

**Your turn**
```
Add a chart of conversion rate by region for the Target audience.
Which region converts best?
```
✅ Southeast (about **5.1%**); Midwest is lowest (about **3.9%**).

**If a number looks off:** KPIs that come out too low (e.g. 4.1% conversion rate, 4,381 contacts)
mean Target and Holdout were blended. Ask:
```
Show me the SQL for the KPI tiles. They should be filtered to audience_group = 'Target'.
```

---

## Module 2 · Data modeling: define the metrics once

**Custom calculations**
```
On the dataset behind this dashboard, confirm these custom calculations:
- Conversion Rate = conversions / contacts
- Net Value = SUM(conversion_value) - SUM(contact_cost)
- Cost per Conversion = SUM(contact_cost) / SUM(converted), Target only
Then ensure every widget uses these calculations instead of its own formulas.
```

**Cost per conversion**
```
Add a chart that shows cost per conversion by channel.
```

**Lift, the metric that matters**
```
Add a custom calculation called Lift = Target conversion rate minus Holdout conversion rate, and a bar chart of Lift by campaign_name. Sort descending.
```
✅ Annual Wealth Review Invitation about **+7 pts**, Spring Retirement Readiness about **+4 pts**,
Rollover Retargeting about **0** (slightly negative).

**Metric view (semantic layer)**
```
Confirm this dashboard is using a metric view from your_catalog.your_schema.campaign_results_detail with dimensions campaign_name, channel, segment, region, audience_group and send_date, and measures Contacts, Conversions, Conversion Rate, Conversion Value, Campaign Cost and Net Value. Then ensure all visualizations in this dashboard are on top of the metric view.
```

**Relationships (Public Preview)**
```
Add your_catalog.your_schema.households as a second dataset and create a relationship to campaign_results_detail on household_id. Then add a chart of conversion rate by tenure_years bucket (0-5, 6-10, 11-20, 20+).
```

**Talking points:** conversion rate is now defined once instead of re-typed in every chart.
A dashboard metric view can be promoted to Unity Catalog so Genie, notebooks and other
dashboards all use the same definition.

**Your turn**
```
Add a measure for Open Rate = opened / delivered. Show Open Rate by Channel.
Why is it blank for Direct Mail?
```
✅ Direct Mail has no open tracking, so `opened` is empty. Good moment to discuss nulls.

---

## Module 3 · Interactivity: filters, parameters, cross-filtering, pages

**Global date filter**
```
Add a date range filter on send_date to the global filters so it applies to every page.
```
Then ask Genie Code:
```
What are the min and max send dates in the data?
```
Pick a date range and notice that the **Lift by Campaign** chart goes empty.
Why: Holdout households were never contacted, so they have no `send_date`. A date filter drops
every row without a date, so the Holdout group disappears and lift can't be calculated.

**Fix it**
```
The Lift by Campaign chart goes empty when I set a send_date range, because Holdout households have no send_date. Keep the send_date filter for the other charts, but make the Lift by Campaign chart ignore it.
```
```
Add a short description to the Lift by Campaign chart that this chart is not filtered by send date and why.
```

**Parameter**
```
Add a parameter called "Minimum AUM" (default 0) and use it to filter households by household_aum on every dataset that has that column.
```

**Cross-filtering (on by default):** click a bar in the **Net Value by Channel** chart and watch
the rest of the page filter to that channel. No setup needed.

**Second page**
```
Add a second page called "Segment Detail" with a pivot table of conversion rate by segment (rows) and campaign_name (columns), with conditional formatting: green above 5%, red below 2%.
```
(If the pivot leaves empty space, ask Genie Code to widen the campaign columns to fill it.)

**Talking points:** filters can be global, page or widget scoped, and they only affect datasets
that have that column. That's why one wide dataset beats many narrow ones. Parameters change the
SQL itself; filters change what's displayed.

**Your turn**
```
Add a page-level filter (not a global filter) to the Segment Detail page for engagement_band.
```
Filter to High engagement households and observe.

---

## Module 4 · Beyond the built-in charts: Vega-Lite custom visualizations (Public Preview)

Custom Viz lets a dashboard widget render a Vega-Lite spec
(**Add visualization → Advanced → Custom Viz**). Ready-made, tested specs are in
[`vega-lite/`](vega-lite/). Each has its dataset SQL, field mapping and spec.

**Prompts** (one at a time)
```
Add a third page called "Vega-Lite" and add a custom Vega-Lite visualization: a bullet chart that shows, for each campaign_name, the Target conversion rate as a bar and the Holdout conversion rate as a tick mark, so I can see the lift at a glance. Use a dataset with one row per campaign.
```
```
Add a custom Vega-Lite funnel for the Target audience: delivered → opened → clicked → responded → converted, one row per stage, with the step-to-step conversion percentage as a label.
```

**Talking points:** use a built-in chart when one exists: it's faster and follows the theme.
Reach for Vega-Lite when the story needs a shape the built-ins don't have. Cross-filtering works
through a selection named `databricks_mark_selection`. If Genie Code's spec misbehaves, paste
the tested spec from `vega-lite/`.

**Your turn**
```
Add a dumbbell chart of Target vs Holdout conversion rate by segment, colored green where the lift is positive and red where it isn't.
```
Note that the prompt doesn't say "custom viz" or "Vega-Lite": Genie Code works out that a
dumbbell needs one.
```
Make the bullet chart cross-filter this dashboard page when I click a campaign.
```

---

## Module 5 · Migrating a Tableau dashboard

Put [`tableau/campaign_performance.twb`](tableau/) in a Unity Catalog volume folder (or upload it
in the Genie Code chat), and keep `campaign_performance.png` on your laptop for the refinement step.

**Main prompt** (new dashboard → Genie Code)
```
/importBI /Volumes/your_catalog/your_schema/files/dashboards_deep_dive/campaign_performance.twb. use your_catalog.your_schema.campaign_results_detail data.
```

✅ You should see the same Target KPIs as Module 1 (3,725 · 167 · 4.5% · $1.57M), conversion
rate by campaign with Target and Holdout bars, a weekly line, net value by channel
(Direct Mail ≈ $1.26M, Email ≈ $256K, Digital ≈ $56K) and a segment × campaign crosstab.

**Refine with the screenshot**

Import BI gives better results with a screenshot of the original dashboard. Pointing Genie Code
at a PNG in a volume doesn't work: click **+** in the Genie Code chat and upload
`campaign_performance.png` there, then:
```
Compare the KPI values with the screenshot and fix any that don't match. Try to adjust the look of the dashboard to be more consistent with the original (see screenshot).
```
This can take several minutes. Leave the tab open while it works.
```
Add a 2nd version of the conversion rate heatmap (keeping the current version for comparison) that is a custom Vega-Lite viz that better matches the original (e.g. no legend).
```

**Talking points:** no Tableau license is needed, only the file. The workbook's calculated
fields (Conversion Rate, Net Value, Cost per Conversion, Open Rate, a Lift calculation and a
FIXED LOD) become governed metric-view measures, so the migration also builds you a semantic
layer. Power BI templates (`.pbit`) work the same way.

**Gross vs incremental:** "net value by channel" shows Digital at about +$56K because it counts
every Target conversion, including ones that would have happened anyway. Lift shows Digital's
incremental value at about −$3.5K. Both are right; they answer different questions.

---

## Module 6 · Publish and share

These are settings and publish-time choices, done by hand:
1. In the dashboard settings, enable the **Genie Agent** (Ask Genie) so viewers can ask follow-up
   questions. Discuss the auto-generated agent vs. a more curated Genie Agent.
2. Set a **custom thumbnail**.
3. **Publish** and choose **embed credentials** (viewers see data through your access) vs.
   **don't embed** (each viewer needs their own access). Discuss which fits which audience.
4. **Schedule** a weekly subscription (PDF by email; Slack and Teams also supported once a
   workspace admin sets up a notification destination).
5. Open the dashboard in **Genie One** to see the business-user view.

---

## Tips for writing your own prompts
See [prompt_anatomy.md](prompt_anatomy.md).
