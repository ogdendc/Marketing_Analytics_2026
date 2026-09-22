# Genie Agent (Genie space) setup & curation

Give business users a plain-English way to query the curated marketing data. The value isn't
just creating the space — it's *teaching* it, which is the loop below.

## Create the space
1. In Catalog Explorer, browse to your `campaign_results_silver` table.
2. **Create → Genie space**.
3. Add the related tables so it can answer ROI/lift questions:
   `campaign_lift_roi`, `marketing_performance`, `households`, `campaigns`.
4. **Settings** → give it a title and description:
   - **Title:** `Marketing Campaign Performance`
   - **Description:** *Self-service analytics on marketing campaign performance. Ask about
     conversion rates, campaign ROI, incremental lift vs. holdout, cost per conversion, and how
     results break down by campaign, channel, customer segment, and region.*

## Seed sample questions
- `Which campaign had the highest ROI?`
- `Show conversion rate by channel for the targeted audience`
- `For the Rollover Retargeting campaign, what was the lift versus the holdout?`
- `Which customer segment responded best to the Annual Wealth Review direct mail campaign?`

## Teach it (the curation loop)
Genie gets smarter as you add **Instructions**. Add these **Text instructions**:

```
- conversion_rate = conversions / contacts.
- "Lift" = Target group's conversion rate minus the Holdout (control) group's rate. Always
  compare Target vs Holdout for incremental results. ROI, lift, incremental conversions and
  incremental value are pre-computed per campaign and segment in campaign_lift_roi.
- Use campaign_results_silver for household-level detail and funnel steps
  (delivered, opened, clicked, responded, converted).
- audience_group is 'Target' (contacted) or 'Holdout' (control). For overall performance
  unless asked otherwise, filter to Target.
- Segments, high to low value: Ultra HNW, High Net Worth, Affluent, Mass Affluent, Mass Market.
- household_aum and conversion_value are US dollars; format money with $ and thousands separators.
```

**A teaching moment to demo live:**
1. Ask `which campaign should we cut?` — see how it reasons about ROI/lift.
2. If the answer is fuzzy, add a **Sample SQL query** (Instructions → SQL) with a description like
   *"use this to rank campaigns by incremental ROI"* pointing at `campaign_lift_roi`.
3. Re-ask — the answer sharpens. This shows the iterative, admin-curated nature of a good space.

## Before you share it
- Review the **Monitoring** tab (what people asked, thumbs up/down).
- Consider an **evaluation set** of known-good questions.
- In the **Data** tab, note you can add synonyms / a value dictionary, and even upload a small
  CSV or Excel lookup for ad-hoc joins.
