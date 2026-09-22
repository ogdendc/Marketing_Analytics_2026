# Marketing Analytics on Databricks — Hands-on Workshop (2026)

A 90-minute, SQL-first introduction to analyzing marketing data on Databricks, built for
business analysts. It follows one continuous story: **an analyst receives a campaign-results
file from outside the data platform, joins it to the firm's own household data, and proves
whether each campaign actually paid off** — using SQL, Genie, AI/BI dashboards, and a metric
view, with the assistant (**Genie Code**) writing most of the SQL.

> Scenario: a fictional wealth-management firm ran three marketing campaigns. Marketing has the
> results in a spreadsheet. Did the campaigns drive **incremental** business, and where should
> the next dollar go?

---

## What you'll work with

**Firm data (already in the lakehouse):**
- `households` — 2,972 households: segment (Mass Market → Ultra HNW), region, AUM, tenure,
  product holdings, preferred channel, engagement score, opt-in, advisor.

**External upload (the "outside the platform" data):**
- `campaigns` — 3 campaigns (Email / Direct Mail / Digital) with objective, dates, unit cost.
- `campaign_results` — 4,381 rows, one per household per campaign, split into **Target**
  (contacted) and **Holdout** (control). This holdout is what lets us measure true *lift*.

The three files are in [`files/`](files/). They're synthetic — safe to share and re-run.

---

## The punchline (what the analysis reveals)

| Campaign | Channel | Lift vs. holdout | Verdict |
|---|---|---|---|
| Annual Wealth Review | Direct Mail | large in **HNW / Ultra HNW** | **Scale** — the expensive channel is justified by high-value segments |
| Spring Retirement Readiness | Email | solid across Affluent / Mass Affluent | **Scale** — cheap channel, strong lift |
| Rollover Retargeting | Digital | **≈ zero** | **Cut / reallocate** — it spent budget but drove no incremental conversions |

The Digital campaign *looks* fine on raw conversions — until you compare it to its holdout and
see the conversions would have happened anyway. That comparison is the whole point.

---

## Prerequisites

- A Databricks workspace with a **SQL warehouse** and Unity Catalog.
- A catalog + schema you can write to, e.g. `main.marketing_analytics`.
- Permission to create a **Volume** and upload files.

**Setup (once):**
```sql
CREATE SCHEMA IF NOT EXISTS main.marketing_analytics;
CREATE VOLUME IF NOT EXISTS main.marketing_analytics.files;
```
Then upload the three CSVs from [`files/`](files/) to that Volume (Catalog Explorer → the
Volume → **Upload**), and in the SQL files **find-and-replace** `your_catalog` → your catalog
and `your_schema` → your schema.

---

## Modules (mirrors the live agenda)

Live session is presenter-led (~90 min); the ⏱ notes show suggested pacing and whether a
topic is a **deep** demo or a **lightning** show. Self-paced, do the steps in order.

### 1 · Platform & workspace orientation  ⏱ ~15 min · talk
Lakehouse + Unity Catalog + the three Genie surfaces you'll use:
- **Genie One** — the conversational, business-user entry point.
- **Genie Code** — the assistant that writes SQL / builds dashboards & pipelines for you.
- **Genie Agents** — a curated Genie space over a specific dataset (Module 6).

### 2 · Getting data in  ⏱ ~10 min · **deep** (file upload)
- *Source systems* (mention): how firm/household data normally arrives (managed ingestion).
- *Upload the external file* (**deep**): load the campaign CSVs. Run
  [`code/00_load_from_files.sql`](code/00_load_from_files.sql). Talk through Catalog Explorer:
  AI-generated table & column descriptions, sample data, permissions.

### 3 · Curate the data — SQL first  ⏱ ~18 min · **deep**
The audience's home turf. Let **Genie Code** draft each step; you read and tweak.
- Silver join (external ↔ firm): [`code/01_curate_silver.sql`](code/01_curate_silver.sql)
- Gold (funnel + **lift/ROI**): [`code/02_curate_gold.sql`](code/02_curate_gold.sql)
- Then the alternatives, as quick shows:
  - **Declarative pipeline** (same result, adds data-quality + auto-lineage):
    [`code/05_declarative_pipeline.sql`](code/05_declarative_pipeline.sql) — lightning
  - **Low-code / visual**: Lakeflow Designer — see
    [`docs/lakeflow_designer_recipe.md`](docs/lakeflow_designer_recipe.md) — lightning
  - **Notebooks**: mention as the Python option.

### 4 · Analyze — is it working?  ⏱ ~8 min · **deep**
Run [`code/04_analysis.sql`](code/04_analysis.sql): funnel, the **lift reveal**, ROI, where to
scale, where to cut, and a plain-English recommendation (optional `ai_query`).

### 5 · Metric views & the semantic layer  ⏱ ~6 min · show
Define KPIs once, reuse everywhere: [`code/03_metric_view.sql`](code/03_metric_view.sql).
Query it with `MEASURE()`; it also powers dashboards and Genie consistently.

### 6 · Genie Agents (self-service)  ⏱ ~12 min · **deep**
Create a Genie space over the curated tables and *teach* it. See
[`docs/genie_space_setup.md`](docs/genie_space_setup.md) for the build + the
instruction-and-sample-SQL curation loop, plus monitoring.

### 7 · AI/BI Dashboards — built by Genie Code  ⏱ ~10 min · **deep**
Don't hand-build it. Use the prompts in
[`docs/dashboard_with_genie_code.md`](docs/dashboard_with_genie_code.md) to have Genie Code
generate the campaign ROI / lift / channel dashboard, then refine interactively.

### 8 · Jobs & orchestration  ⏱ ~4 min · lightning
Stitch the curation SQL into a scheduled multi-task **Job** (SQL file tasks, run in order,
then refresh the dashboard). Recipe + importable definition in
[`code/job_definition.json`](code/job_definition.json).

### 9 · Sharing & collaboration  ⏱ ~4 min · lightning
Publish/share the dashboard and Genie space, permissions, and the Genie One consumer view.

### 10 · Where to go next  ⏱ ~3 min · talk
Jobs on a schedule, AI functions, Agent Bricks, Databricks Apps, and the resources below.

---

## Repo layout

```
files/   households.csv, campaigns.csv, campaign_results.csv   (upload these)
code/    00_load_from_files.sql → 04_analysis.sql              (SQL-first path)
         05_declarative_pipeline.sql                           (pipeline alternative)
         job_definition.json                                   (orchestration)
         generate_campaign_files.py                            (how the data was made)
docs/    genie_space_setup.md, dashboard_with_genie_code.md, lakeflow_designer_recipe.md,
         data_dictionary.md
```

## Resources
- Databricks documentation, Databricks Academy, and the in-product **Assistant / Genie Code**.
