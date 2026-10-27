# AI/BI Dashboards Deep Dive (hands-on, 90 minutes)

A hands-on follow-up to the [Marketing Analytics workshop](../README.md). Same campaign data,
same story (which campaigns actually drove incremental value?), but this session is all about
**building dashboards**. Most of the building is done by **Genie Code** from plain-English prompts.

You'll learn to:
- build a full dashboard from one prompt, then refine it
- define metrics once (custom calculations, metric views, relationships)
- add filters, parameters, cross-filtering, drill-through and multiple pages
- go beyond the built-in charts with **Vega-Lite** custom visualizations
- migrate a **Tableau** workbook into an AI/BI dashboard
- polish, publish, share, schedule and ask follow-up questions with Genie

## What's in this folder

| Path | What it is |
|---|---|
| `data/` | Dashboard-ready CSVs to upload (see below) |
| [`genie_code_prompts.md`](genie_code_prompts.md) | Copy-paste Genie Code prompts for every module, with "you should see" checks and "your turn" challenges |
| [`prompt_anatomy.md`](prompt_anatomy.md) | One-pager: how to write prompts that work first time |
| `vega-lite/` | Tested Vega-Lite specs (bullet, funnel, waterfall, dumbbell, cross-filter) with dataset SQL |
| `tableau/` | A sample Tableau workbook (`.twb`) and screenshot for the migration exercise |
| `answer_key/` | A finished dashboard (`.lvdash.json`) you can import to compare against, or to use as a fallback |

### The data (`data/`)

| File | Rows | Grain | Used for |
|---|---|---|---|
| `campaign_results_detail.csv` | 4,381 | one row per household per campaign | most exercises (main fact table) |
| `campaign_daily_performance.csv` | 81 | one row per send date per campaign (Target only) | trends, AI Forecast |
| `campaign_lift_roi.csv` | 7 | one row per campaign × segment | headline lift and ROI |
| `households.csv` | 2,972 | one row per household | relationships exercise |
| `campaigns.csv` | 3 | one row per campaign | reference |

All data is synthetic. `audience_group` is **Target** (contacted) or **Holdout** (a control group
that wasn't contacted). The gap between them is the **lift** the campaign caused.

## Before the session (5 minutes)
1. You need: Databricks SQL access, a SQL warehouse you can use, and a schema where you can
   create tables (`USE CATALOG`, `USE SCHEMA`, `CREATE TABLE`).
2. Genie Code requires *partner-powered AI features* to be on for your workspace. Ask your admin
   if the Genie Code panel doesn't appear.
3. Download the `data/` folder.

## Run sheet

| # | Module | Time | Type |
|---|---|---|---|
| 0 | Upload the data | 8 min | hands-on |
| 1 | Zero to dashboard in one prompt | 12 min | hands-on |
| 2 | Data modeling: define metrics once | 15 min | hands-on |
| 3 | Interactivity: filters, parameters, cross-filtering, pages | 13 min | hands-on |
| 4 | Vega-Lite custom visualizations | 15 min | hands-on |
| 5 | Migrating a Tableau dashboard | 12 min | hands-on |
| 6 | Polish, publish and share | 10 min | demo + hands-on |
| 7 | Wrap-up + dashboards as code (take-home) | 5 min | lightning |

### 0 · Upload the data (8 min)
**New → Add or upload data → Create or modify a table.** Drop in each CSV (one table per file),
pick your catalog and schema, keep the suggested table names, and click **Create table**.
Do `campaign_results_detail.csv` first, since every module uses it.

✅ Check: `SELECT COUNT(*) FROM campaign_results_detail` returns **4,381**.

### 1–6 · Build
Follow [`genie_code_prompts.md`](genie_code_prompts.md) module by module. Each module has a main
prompt, refinements, talking points and a "your turn" challenge.

Headline numbers to sanity-check along the way (Target audience):

| Campaign | Channel | Target conv. rate | Holdout conv. rate | Lift | Net incremental value |
|---|---|---|---|---|---|
| Annual Wealth Review Invitation | Direct Mail | 7.8% | 0.75% | ≈ +7 pts | ≈ $1.23M |
| Spring Retirement Readiness | Email | 6.0% | 2.0% | ≈ +4 pts | ≈ $155K |
| Rollover Retargeting | Digital | 2.1% | 2.2% | ≈ 0 | ≈ −$3.5K |

The story: Direct Mail and Email earned their keep; Digital retargeting drove **no** incremental
conversions, so that budget should be reallocated.

### 7 · Wrap-up: dashboards as code (take-home)
Every dashboard is a JSON file (`.lvdash.json`). You can export it, keep it in Git, and deploy it
to other workspaces with Declarative Automation Bundles. Try it with `answer_key/`:
**Dashboards → Create → Import dashboard from file**, then point it at your catalog and schema.

## If something goes wrong
- **Genie Code stops mid-build:** you probably switched browser tabs. Go back and type "continue".
- **A number doesn't match:** ask Genie Code to "show me the SQL for this widget". The usual
  cause is Target and Holdout blended together.
- **Short on time:** import `answer_key/` and explore it instead of building.
