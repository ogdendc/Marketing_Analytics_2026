# Data dictionary

All data is synthetic. Money values are US dollars.

## `households` (firm data — `files/households.csv`)
One row per household.

| Column | Type | Notes |
|---|---|---|
| household_id | string | Primary key, e.g. `HH_000001` |
| segment | string | Mass Market · Mass Affluent · Affluent · High Net Worth · Ultra HNW |
| value_tier | string | T1–T5 (T1 = Mass Market … T5 = Ultra HNW) |
| region | string | Midwest · Northeast · South · Southeast · West |
| dma_code | int | Designated Market Area code |
| client_count | int | Clients in the household |
| household_aum | bigint | Assets under management ($) |
| tenure_years | int | Years as a client |
| product_count | int | Distinct products held |
| primary_channel | string | Preferred contact channel |
| acquisition_channel | string | How the household was acquired |
| engagement_score | int | 0–100 relationship engagement |
| email_opt_in | boolean | Consent to email marketing |
| advisor_id | string | Servicing advisor, e.g. `ADV_0026` |

## `campaigns` (external upload — `files/campaigns.csv`)
One row per campaign.

| Column | Type | Notes |
|---|---|---|
| campaign_id | string | e.g. `CMP_001` |
| campaign_name | string | Display name |
| channel | string | Email · Direct Mail · Digital |
| objective | string | Campaign goal |
| start_date / end_date | date | Campaign window |
| cost_per_contact | double | Unit send cost ($) |
| budget | double | Approx. planned spend ($) |

## `campaign_results` (external upload — `files/campaign_results.csv`)
One row per household per campaign.

| Column | Type | Notes |
|---|---|---|
| campaign_id | string | FK → campaigns |
| household_id | string | FK → households |
| audience_group | string | **Target** (contacted) or **Holdout** (control, not contacted) |
| send_date | date | Empty for Holdout |
| delivered | int | 1/0 (0 for Holdout) |
| opened / clicked | int | Engagement; empty where the channel has no such tracking (e.g. Direct Mail) or Holdout |
| responded | int | 1/0 |
| converted | int | 1/0 — the outcome |
| conversion_value | double | Incremental value if converted, else 0 |
| contact_cost | double | Send cost for Target; 0 for Holdout |

## Curated tables (built by the SQL / pipeline)
- `campaign_results_silver` — results joined to household + campaign attributes.
- `marketing_performance` — funnel + conversion metrics by campaign × segment × audience_group.
- `campaign_lift_roi` — Target-vs-Holdout **lift**, incremental value, and **ROI** by campaign × segment.
- `marketing_performance_metrics` — metric view (semantic layer) with governed measures.
