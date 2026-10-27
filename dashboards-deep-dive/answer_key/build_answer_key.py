"""Build the answer-key AI/BI dashboard (campaign_performance.lvdash.json).

Queries use bare table names so the file is portable: when importing, point the
dashboard at the catalog and schema where you uploaded the CSVs.

    python3 build_answer_key.py            # writes campaign_performance.lvdash.json
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
TEAL, GRAY, RED = "#00A3A1", "#9AA5B1", "#E5484D"

PCT = {"type": "number-percent", "decimalPlaces": {"type": "exact", "places": 1}}
USD = {"type": "number-currency", "currencyCode": "USD", "abbreviation": "compact",
       "decimalPlaces": {"type": "max", "places": 2}}
INT = {"type": "number-plain", "decimalPlaces": {"type": "max", "places": 0}}

DATASETS = [
    {"name": "ds_detail", "displayName": "Campaign results (all households)",
     "queryLines": ["SELECT *, conversion_value - contact_cost AS net_value ",
                    "FROM campaign_results_detail"]},
    {"name": "ds_target", "displayName": "Campaign results (Target only)",
     "queryLines": ["SELECT *, conversion_value - contact_cost AS net_value ",
                    "FROM campaign_results_detail ",
                    "WHERE audience_group = 'Target'"]},
    {"name": "ds_lift", "displayName": "Lift by campaign",
     "queryLines": ["SELECT campaign_name, channel, ",
                    "AVG(CASE WHEN audience_group = 'Target' THEN converted END) AS target_cvr, ",
                    "AVG(CASE WHEN audience_group = 'Holdout' THEN converted END) AS holdout_cvr, ",
                    "AVG(CASE WHEN audience_group = 'Target' THEN converted END) ",
                    "- AVG(CASE WHEN audience_group = 'Holdout' THEN converted END) AS lift ",
                    "FROM campaign_results_detail ",
                    "GROUP BY campaign_name, channel ",
                    "ORDER BY lift DESC"]},
    {"name": "ds_roi", "displayName": "Lift and ROI by campaign and segment",
     "queryLines": ["SELECT campaign_name, channel, segment, target_contacts, target_cvr, ",
                    "holdout_cvr, lift, incremental_value, cost, ",
                    "incremental_value - cost AS net_incremental_value, roi ",
                    "FROM campaign_lift_roi ",
                    "ORDER BY roi DESC"]},
]


def text(name, md, x, y, w, h):
    return {"widget": {"name": name, "multilineTextboxSpec": {"lines": md}},
            "position": {"x": x, "y": y, "width": w, "height": h}}


def counter(name, ds, expr_name, expr, title, fmt, x, y):
    return {"widget": {
        "name": name,
        "queries": [{"name": "main_query", "query": {
            "datasetName": ds, "fields": [{"name": expr_name, "expression": expr}],
            "disaggregated": False}}],
        "spec": {"version": 2, "widgetType": "counter",
                 "encodings": {"value": {"fieldName": expr_name, "displayName": title, "format": fmt}},
                 "frame": {"showTitle": True, "title": title}}},
        "position": {"x": x, "y": y, "width": 3, "height": 3}}


def chart(name, ds, fields, wtype, encodings, title, pos, mark=None, disagg=False):
    spec = {"version": 3, "widgetType": wtype, "encodings": encodings,
            "frame": {"showTitle": True, "title": title}}
    if mark:
        spec["mark"] = mark
    return {"widget": {
        "name": name,
        "queries": [{"name": "main_query", "query": {
            "datasetName": ds, "fields": fields, "disaggregated": disagg}}],
        "spec": spec},
        "position": dict(zip(["x", "y", "width", "height"], pos))}


def f(name, expr=None):
    return {"name": name, "expression": expr or f"`{name}`"}


overview = [
    text("title", ["## Campaign Performance",
                   "Target households were contacted; **Holdout** households were not. "
                   "The gap between them is the lift each campaign caused."], 0, 0, 12, 2),
    counter("kpi_contacts", "ds_target", "count(household_id)", "COUNT(`household_id`)",
            "Target contacts", INT, 0, 2),
    counter("kpi_conversions", "ds_target", "sum(converted)", "SUM(`converted`)",
            "Conversions", INT, 3, 2),
    counter("kpi_cvr", "ds_target", "avg(converted)", "AVG(`converted`)",
            "Conversion rate", PCT, 6, 2),
    counter("kpi_net", "ds_target", "sum(net_value)", "SUM(`net_value`)",
            "Net value", USD, 9, 2),
    chart("cvr_by_campaign", "ds_detail",
          [f("campaign_name"), f("audience_group"), f("avg(converted)", "AVG(`converted`)")],
          "bar",
          {"x": {"fieldName": "campaign_name", "scale": {"type": "categorical"}, "displayName": "Campaign"},
           "y": {"fieldName": "avg(converted)", "scale": {"type": "quantitative"},
                 "displayName": "Conversion rate", "format": PCT},
           "color": {"fieldName": "audience_group", "displayName": "Audience",
                     "scale": {"type": "categorical", "mappings": [
                         {"value": "Target", "color": TEAL}, {"value": "Holdout", "color": GRAY}]}},
           "label": {"show": True}},
          "Conversion rate: Target vs Holdout", (0, 5, 6, 6), mark={"layout": "group"}),
    chart("lift_by_campaign", "ds_lift",
          [f("campaign_name"), f("sum(lift)", "SUM(`lift`)")], "bar",
          {"x": {"fieldName": "campaign_name", "scale": {"type": "categorical",
                                                         "sort": {"by": "y-reversed"}},
                 "displayName": "Campaign"},
           "y": {"fieldName": "sum(lift)", "scale": {"type": "quantitative"},
                 "displayName": "Lift (pts)", "format": PCT},
           "label": {"show": True}},
          "Lift by campaign (Target minus Holdout conversion rate)", (6, 5, 6, 6)),
    chart("weekly_conversions", "ds_target",
          [f("weekly(send_date)", 'DATE_TRUNC("WEEK", `send_date`)'), f("campaign_name"),
           f("sum(converted)", "SUM(`converted`)")], "line",
          {"x": {"fieldName": "weekly(send_date)", "scale": {"type": "temporal"}, "displayName": "Week"},
           "y": {"fieldName": "sum(converted)", "scale": {"type": "quantitative"},
                 "displayName": "Conversions"},
           "color": {"fieldName": "campaign_name", "scale": {"type": "categorical"},
                     "displayName": "Campaign"}},
          "Weekly conversions by campaign", (0, 11, 6, 6)),
    chart("net_by_channel", "ds_target",
          [f("channel"), f("sum(net_value)", "SUM(`net_value`)")], "bar",
          {"x": {"fieldName": "channel", "scale": {"type": "categorical",
                                                   "sort": {"by": "y-reversed"}},
                 "displayName": "Channel"},
           "y": {"fieldName": "sum(net_value)", "scale": {"type": "quantitative"},
                 "displayName": "Net value", "format": USD},
           "label": {"show": True}},
          "Net value by channel (Target)", (6, 11, 6, 6)),
]

segment_page = [
    text("seg_title", ["## Segment Detail",
                       "Lift and ROI by campaign and segment. Rollover Retargeting shows no "
                       "incremental return in any segment."], 0, 0, 12, 2),
    chart("cvr_by_region", "ds_target",
          [f("region"), f("avg(converted)", "AVG(`converted`)")], "bar",
          {"x": {"fieldName": "region", "scale": {"type": "categorical", "sort": {"by": "y-reversed"}},
                 "displayName": "Region"},
           "y": {"fieldName": "avg(converted)", "scale": {"type": "quantitative"},
                 "displayName": "Conversion rate", "format": PCT},
           "label": {"show": True}},
          "Target conversion rate by region", (0, 2, 6, 6)),
    chart("cvr_by_engagement", "ds_target",
          [f("engagement_band"), f("campaign_name"), f("avg(converted)", "AVG(`converted`)")], "bar",
          {"x": {"fieldName": "engagement_band", "displayName": "Engagement",
                 "scale": {"type": "categorical",
                           "sort": {"by": "custom-order", "orderedValues": ["Low", "Medium", "High"]}}},
           "y": {"fieldName": "avg(converted)", "scale": {"type": "quantitative"},
                 "displayName": "Conversion rate", "format": PCT},
           "color": {"fieldName": "campaign_name", "scale": {"type": "categorical"},
                     "displayName": "Campaign"}},
          "Target conversion rate by engagement", (6, 2, 6, 6), mark={"layout": "group"}),
    {"widget": {
        "name": "roi_table",
        "queries": [{"name": "main_query", "query": {
            "datasetName": "ds_roi",
            "fields": [f(c) for c in ["campaign_name", "channel", "segment", "target_contacts",
                                      "target_cvr", "holdout_cvr", "lift",
                                      "net_incremental_value", "roi"]],
            "disaggregated": True}}],
        "spec": {"version": 2, "widgetType": "table",
                 "encodings": {"columns": [
                     {"fieldName": "campaign_name", "displayName": "Campaign"},
                     {"fieldName": "channel", "displayName": "Channel"},
                     {"fieldName": "segment", "displayName": "Segment"},
                     {"fieldName": "target_contacts", "displayName": "Targeted"},
                     {"fieldName": "target_cvr", "displayName": "Target CVR", "format": PCT},
                     {"fieldName": "holdout_cvr", "displayName": "Holdout CVR", "format": PCT},
                     {"fieldName": "lift", "displayName": "Lift", "format": PCT},
                     {"fieldName": "net_incremental_value", "displayName": "Net incremental $",
                      "format": USD},
                     {"fieldName": "roi", "displayName": "ROI (x)"}]},
                 "frame": {"showTitle": True, "title": "Lift and ROI by campaign and segment"}}},
     "position": {"x": 0, "y": 8, "width": 12, "height": 7}},
]


def filt(name, wtype, field, title, datasets, x):
    return {"widget": {
        "name": name,
        "queries": [{"name": f"{ds}_{field}", "query": {
            "datasetName": ds, "fields": [f(field)], "disaggregated": False}} for ds in datasets],
        "spec": {"version": 2, "widgetType": wtype,
                 "encodings": {"fields": [{"fieldName": field, "displayName": title,
                                           "queryName": f"{ds}_{field}"} for ds in datasets]},
                 "frame": {"showTitle": True, "title": title}}},
        "position": {"x": x, "y": 0, "width": 2, "height": 2}}


filters = [
    filt("f_campaign", "filter-multi-select", "campaign_name", "Campaign",
         ["ds_detail", "ds_target", "ds_lift", "ds_roi"], 0),
    filt("f_region", "filter-multi-select", "region", "Region", ["ds_detail", "ds_target"], 2),
    filt("f_send_date", "filter-date-range-picker", "send_date", "Send date", ["ds_target"], 4),
]

dashboard = {
    "datasets": DATASETS,
    "pages": [
        {"name": "overview", "displayName": "Campaign Performance", "pageType": "PAGE_TYPE_CANVAS",
         "layoutVersion": "GRID_V1", "layout": overview},
        {"name": "segments", "displayName": "Segment Detail", "pageType": "PAGE_TYPE_CANVAS",
         "layoutVersion": "GRID_V1", "layout": segment_page},
        {"name": "filters", "displayName": "Filters", "pageType": "PAGE_TYPE_GLOBAL_FILTERS",
         "layout": filters},
    ],
    "uiSettings": {"theme": {
        "canvasBackgroundColor": {"light": "#F7F9FA", "dark": "#1F272D"},
        "widgetBackgroundColor": {"light": "#FFFFFF", "dark": "#11171C"},
        "widgetBorderColor": {"light": "#FFFFFF", "dark": "#11171C"},
        "fontColor": {"light": "#11171C", "dark": "#E8ECF0"},
        "selectionColor": {"light": "#2272B4", "dark": "#8ACAFF"},
        "visualizationColors": ["#00A3A1", "#1D425C", "#F59E0B", "#7C5CBF", "#E5484D",
                                "#9AA5B1", "#4E79A7"],
        "widgetHeaderAlignment": "LEFT",
        "widgetCornerRadius": 8}},
}

# Vega-Lite page: datasets come from ../vega-lite/sql (comments stripped, newlines kept,
# bare table names); widget definitions (custom-vega-viz) come from vega_widgets.json.
VEGA_DIR = HERE.parent / "vega-lite"
VEGA = [  # (widget name, dataset name, sql file, title, position)
    ("w_cv_bullet", "ds_bullet", "01_bullet_target_vs_holdout_cvr.sql",
     "Bullet: Target conversion rate vs Holdout (tick)", (0, 2, 6, 6)),
    ("w_cv_dumbbell", "ds_dumbbell", "04_dumbbell_cvr_by_segment.sql",
     "Dumbbell: Target vs Holdout conversion rate by segment", (6, 2, 6, 6)),
    ("w_cv_funnel", "ds_funnel", "02_funnel_target_stages.sql",
     "Funnel: Target audience by campaign", (0, 8, 6, 10)),
    ("w_cv_waterfall", "ds_waterfall", "03_waterfall_net_by_campaign.sql",
     "Waterfall: net incremental value by campaign", (6, 8, 6, 10)),
    ("w_cv_crossfilter", "ds_crossfilter", "05_crossfilter_incremental_by_campaign.sql",
     "Click a bar to cross-filter", (0, 18, 6, 6)),
    ("w_cv_cost_check", "ds_crossfilter", None,
     "Cost by campaign (filtered by the click)", (6, 18, 6, 6)),
]


def sql_lines(path):
    lines = [l for l in path.read_text().splitlines() if not l.strip().startswith("--")]
    return [l.replace("your_catalog.your_schema.", "") + "\n" for l in lines if l.strip()]


def add_vega_page(dash):
    widgets = {w["widget"]["name"]: w for w in json.loads((HERE / "vega_widgets.json").read_text())}
    layout = [text("vega_title", ["## Beyond the built-in charts (Vega-Lite)",
                                  "Custom Viz widgets: each one is a Vega-Lite spec bound to a "
                                  "dataset. Specs and SQL are in the `vega-lite/` folder."],
                   0, 0, 12, 2)]
    for wname, ds, sql_file, title, pos in VEGA:
        if sql_file:
            dash["datasets"].append({"name": ds, "displayName": sql_file[:-4],
                                     "queryLines": sql_lines(VEGA_DIR / "sql" / sql_file)})
        w = json.loads(json.dumps(widgets[wname]))
        w["widget"]["queries"][0]["query"]["datasetName"] = ds
        w["widget"]["spec"]["frame"] = {"showTitle": True, "title": title}
        w["position"] = dict(zip(["x", "y", "width", "height"], pos))
        layout.append(w)
    dash["pages"].insert(2, {"name": "vega", "displayName": "Beyond Built-ins (Vega-Lite)",
                             "pageType": "PAGE_TYPE_CANVAS", "layoutVersion": "GRID_V1",
                             "layout": layout})


add_vega_page(dashboard)

if __name__ == "__main__":
    out = HERE / "campaign_performance.lvdash.json"
    out.write_text(json.dumps(dashboard, indent=2))
    print("wrote", out)
