# Low-code / visual curation with Lakeflow Designer (quick show)

Same silver join as `01_curate_silver.sql`, built visually — for analysts who prefer a canvas
over SQL. Keep this to a few minutes in the live session; it's a "here's another way" beat.

## Build the silver join visually
1. **Create → ETL pipeline → Lakeflow Designer** (visual authoring canvas).
2. Add three **source** nodes:
   - `your_catalog.your_schema.campaign_results_bronze`
   - `your_catalog.your_schema.households`
   - `your_catalog.your_schema.campaigns`
3. Drop a **Join** node:
   - `campaign_results_bronze` ⋈ `households` on `household_id`
   - then ⋈ `campaigns` on `campaign_id`
4. (Optional) add a **Select / rename** node to keep the columns you want and rename
   `households.primary_channel` → `preferred_channel`.
5. Add a **destination** node writing to `campaign_results_silver_visual` (a separate table so it
   doesn't clash with the SQL-built one).
6. **Run**. Open the resulting table and show that its **lineage** was captured automatically,
   just like the SQL path.

## Point to make
The visual pipeline and the SQL you wrote produce the *same* governed table with the *same*
lineage — Databricks meets analysts wherever they're comfortable (SQL, visual, or notebooks),
and Unity Catalog governs the result identically.
