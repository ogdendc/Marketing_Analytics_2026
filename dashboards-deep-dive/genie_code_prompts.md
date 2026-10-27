# Genie Code prompt library: AI/BI dashboards deep dive

Copy-paste prompts for each module. Open a new dashboard (**New → Dashboard**) and use the
**Genie Code** panel. Genie Code asks for approval before it creates or changes anything:
click **Allow** (or **Always allow** for the session) and review what it built.

Conventions used below:
- `@table_name` tells Genie Code exactly which table to use. Type `@` and pick from the list.
- Replace `your_catalog.your_schema` if Genie Code asks where the tables live.
- **Keep the browser tab open while Genie Code is working.** Switching tabs stops the agent.

Each module has a **main prompt**, **refinement prompts**, and a **Your turn** challenge.
"✅ You should see" lists the numbers to check against.

---

## Module 1 · Zero to dashboard in one prompt

**Main prompt**
```
Build a dashboard called "Campaign Performance" using @campaign_results_detail.
Our marketing team runs campaigns with a Target group (contacted) and a Holdout group
(not contacted, used as a control). Include:
1. KPI tiles for Target contacts, conversions, conversion rate and net value
   (conversion_value minus contact_cost), Target audience only.
2. A bar chart of conversion rate by campaign_name, split by audience_group so Target and
   Holdout sit side by side.
3. A line chart of weekly conversions by send_date, one line per campaign_name.
4. A bar chart of net value by channel (Target only).
Add a filter for campaign_name and region that applies to all charts.
```

✅ You should see: **3,725** Target contacts, **167** conversions, **4.5%** conversion rate,
net value about **$1.57M**.

**Refinement prompts**
```
Format conversion rate as a percentage with 1 decimal and net value as currency in compact form ($1.6M).
```
```
Add a short text header at the top explaining that Holdout households were not contacted,
so the gap between Target and Holdout is the lift the campaign caused.
```
```
Beautify this dashboard.
```

**Talking points:** Genie Code plans first, then writes each dataset's SQL. Open a dataset and
read the SQL it wrote. Ask "why did you filter to Target here?" if a number looks off.

**Your turn**
```
Add a chart of conversion rate by region for the Target audience. Which region converts best?
```
✅ Southeast (about **5.1%**); Midwest is lowest (about **3.9%**).

---

## Module 2 · Data modeling: define the metrics once

**Main prompt: custom calculations**
```
On the dataset behind this dashboard, add custom calculations:
- Conversion Rate = conversions / contacts
- Net Value = SUM(conversion_value) - SUM(contact_cost)
- Cost per Conversion = SUM(contact_cost) / SUM(converted), Target only
Then update every widget to use these calculations instead of its own formulas.
```

**Main prompt: lift, the metric that matters**
```
Add a custom calculation called Lift = Target conversion rate minus Holdout conversion rate,
and a bar chart of Lift by campaign_name. Sort descending.
```
✅ Annual Wealth Review Invitation about **+7 pts**, Spring Retirement Readiness about **+4 pts**,
Rollover Retargeting about **0** (slightly negative).

**Main prompt: metric view (semantic layer)**
```
Create a metric view from @campaign_results_detail with dimensions campaign_name, channel,
segment, region, audience_group and send_date, and measures Contacts, Conversions,
Conversion Rate, Conversion Value, Campaign Cost and Net Value. Then rebuild the KPI tiles
on top of the metric view.
```

**Main prompt: relationships (Public Preview)**
```
Add @households as a second dataset and create a relationship to campaign_results_detail on
household_id. Then add a chart of conversion rate by tenure_years bucket (0-5, 6-10, 11-20, 20+).
```

**Talking points:** custom calculations and metric views mean "conversion rate" is defined
once, not re-typed in every chart. A dashboard metric view can be promoted to Unity Catalog
so Genie, notebooks and other dashboards all use the same definition.

**Your turn**
```
Add a measure for Open Rate = opened / delivered. Why is it blank for Direct Mail?
```
✅ Direct Mail has no open tracking, so `opened` is empty. Good moment to discuss nulls.

---

## Module 3 · Interactivity: filters, parameters, cross-filtering, pages

**Main prompts**
```
Add a date range filter on send_date to the global filters so it applies to every page.
```
```
Add a parameter called "Minimum AUM" (default 0) and use it to filter households by household_aum
on every dataset that has that column.
```
```
Make the "conversion rate by campaign" chart cross-filter the rest of the page when I click a bar.
```
```
Add a second page called "Segment Detail" with a pivot table of conversion rate by segment (rows)
and campaign_name (columns), with conditional formatting: green above 5%, red below 2%.
```
```
Add a drill-through from the campaign bars on page 1 to the Segment Detail page, filtered to the
campaign I clicked.
```

**Talking points:** filter scope (global, page, widget); filters only affect datasets that have
the field. That's why one wide dataset beats many narrow ones. Parameters change the SQL
itself, while filters change what's displayed.

**Your turn**
```
Add a filter for aum_band and engagement_band. Does the Email campaign still win for
High engagement households over $1M?
```

---

## Module 4 · Beyond the built-in charts: Vega-Lite custom visualizations (Public Preview)

Custom Viz lets you paste a Vega-Lite spec into a dashboard widget
(**Add visualization → Advanced → Custom Viz**). Ready-made, tested specs are in
[`vega-lite/`](vega-lite/). Each has its dataset SQL, field mapping and spec.

**Main prompt: let Genie Code write the spec**
```
Add a custom Vega-Lite visualization: a bullet chart that shows, for each campaign_name, the
Target conversion rate as a bar and the Holdout conversion rate as a black tick mark, so I can
see the lift at a glance. Use a dataset with one row per campaign.
```
```
Add a custom Vega-Lite funnel for the Target audience: delivered → opened → clicked → responded
→ converted, one row per stage, with the step-to-step conversion percentage as a label.
```
```
Add a custom Vega-Lite waterfall: incremental value by campaign, then minus total cost, ending in
net incremental value. Color negative steps red.
```
```
Make the bullet chart cross-filter the dashboard when I click a campaign.
```

**Talking points:** use a built-in chart when one exists (faster, themed, accessible).
Reach for Vega-Lite when the story needs a shape the built-ins don't have: bullet,
dumbbell, waterfall-with-subtotals, annotated layers. Fallback if Genie Code's spec
misbehaves: paste the tested spec from `vega-lite/`.

**Your turn**
```
Add a dumbbell chart of Target vs Holdout conversion rate by segment, colored green where the
lift is positive and red where it isn't.
```

---

## Module 5 · Migrating a Tableau dashboard

Upload [`tableau/campaign_performance.twb`](tableau/) (and the matching screenshot) with
Genie Code's **Import BI** flow.

**Main prompt**
```
/importBI Convert this Tableau workbook into an AI/BI dashboard. Point it at
@campaign_results_detail. Use the attached screenshot to match the layout and check the numbers.
```
(Attach `campaign_performance.twb` and `campaign_performance.png`.)

**Refinement prompts**
```
Compare the KPI values with the screenshot and fix any that don't match.
```
```
List the Tableau calculated fields you translated and show me the metric view measure for each.
```

**Talking points:** no Tableau license is needed, only the file. Tableau calculated fields become
governed metric-view measures, so the migration also gives you a semantic layer. The same
flow works for Power BI templates (`.pbit`).

---

## Module 6 · Polish, publish and share

```
Apply a consistent color theme: Target in teal, Holdout in gray, and red for anything negative.
```
```
Turn the weekly conversions line chart into a forecast for the next 4 weeks.
```
(AI Forecast is Public Preview; it needs a date x-axis and one numeric measure.)

Then do these by hand, since they're publish-time settings:
1. **Publish** and choose **embed credentials** (viewers see data through your access) vs.
   **don't embed** (each viewer needs their own access). Discuss which fits which audience.
2. Turn on **Ask Genie** so viewers can ask follow-up questions about the dashboard data.
3. **Schedule** a weekly subscription (PDF by email; Slack or Teams also supported).
4. Open the dashboard in **Genie One** to see the business-user view.

---

## Tips for writing your own prompts
See [prompt_anatomy.md](prompt_anatomy.md).
