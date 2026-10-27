# Anatomy of a good dashboard prompt

Genie Code builds what you describe, so the more of the following a prompt covers, the less
back-and-forth you'll need.

| Ingredient | Why it matters | Example |
|---|---|---|
| **Data** (`@table`) | Removes guessing about which table to use | `using @campaign_results_detail` |
| **Business context** | Lets it pick sensible filters and definitions | `Holdout households were not contacted (a control group)` |
| **Metric definitions** | Your definition, not its guess | `net value = conversion_value minus contact_cost` |
| **Scope / filters** | Prevents blended numbers | `Target audience only` |
| **Chart + encoding** | Gets the right shape first time | `bar chart of conversion rate by campaign, split by audience_group` |
| **Format** | Saves a round of polish | `percent with 1 decimal`, `compact currency` |
| **Interactivity** | Filters and their scope | `a filter on region that applies to all charts` |

## Habits that help
- **One big ask, then small refinements.** Build the skeleton in one prompt, then refine one
  thing at a time ("make the bars horizontal", "sort descending").
- **Check a number you already know.** Before trusting a dashboard, compare one KPI to a value
  you know is right.
- **Read the SQL.** Every widget has a dataset. Open it and confirm the filter and grain.
- **Name things the way your stakeholders do.** "Net value", not "sum_conv_minus_cost".
- **Say what NOT to do** when it matters: "don't include Holdout in the KPI tiles".
- **Attach a picture** (a sketch, a screenshot of an old report) when layout matters.

## Common fixes
| Symptom | Follow-up prompt |
|---|---|
| Numbers look too low or high | `Show me the SQL for this widget. Is it filtered to Target?` |
| Too many colors / categories | `Group anything outside the top 5 into "Other".` |
| Chart is the wrong type | `Change this to a horizontal bar chart sorted by value.` |
| Filter doesn't affect a chart | `Make the region filter apply to this widget too.` (the dataset needs the field) |
