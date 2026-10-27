#!/usr/bin/env python3
"""
Generate a mock "legacy" Tableau dashboard for the Databricks "Import BI files using
Genie Code" hands-on exercise. Tableau .twb files are plain XML, so no Tableau license
is needed.

Outputs (all in this script's directory):
  - campaign_performance.twb    hand-authored workbook (upload this to Genie Code)
  - campaign_performance.twbx   packaged workbook (twb + campaign_results_detail.csv extract)

Structure mirrors the earlier BI-import demo workbook (which imported successfully): datasource with a Databricks connection + metadata-records +
column definitions, worksheets with datasource-dependencies and encoded rows/cols
shelves, panes/marks, and a dashboard with zones.

The connection points at placeholder names (your_catalog.your_schema.campaign_results_detail).
"""

import csv
import os
import zipfile
import xml.dom.minidom as minidom
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
DETAIL_CSV = os.path.join(DATA_DIR, "campaign_results_detail.csv")

# --- Databricks connection (placeholders; mirror of the prior kit's connection block) ----
DBX_SERVER = "your-workspace.cloud.databricks.com"
DBX_HTTP_PATH = "/sql/1.0/warehouses/your_warehouse_id"
CATALOG = "your_catalog"
SCHEMA = "your_schema"
TABLE = "campaign_results_detail"

DS_NAME = "databricks.campaign_results_detail"
DS_CAPTION = "campaign_results_detail (Databricks)"
DASHBOARD = "Campaign Performance"


def attr(s):
    """XML-escape a value for use inside a single-quoted attribute (incl. & and ')."""
    return escape(str(s), {"'": "&apos;", '"': "&quot;"})


# --- Raw columns: (name, caption, local_type, remote_type, role, type, aggregation) -------
COLS = [
    ("campaign_id",       "Campaign ID",       "string",  130, "dimension", "nominal",      "Count"),
    ("campaign_name",     "Campaign Name",     "string",  130, "dimension", "nominal",      "Count"),
    ("channel",           "Channel",           "string",  130, "dimension", "nominal",      "Count"),
    ("objective",         "Objective",         "string",  130, "dimension", "nominal",      "Count"),
    ("household_id",      "Household ID",      "string",  130, "dimension", "nominal",      "Count"),
    ("audience_group",    "Audience Group",    "string",  130, "dimension", "nominal",      "Count"),
    ("segment",           "Segment",           "string",  130, "dimension", "nominal",      "Count"),
    ("region",            "Region",            "string",  130, "dimension", "nominal",      "Count"),
    ("preferred_channel", "Preferred Channel", "string",  130, "dimension", "nominal",      "Count"),
    ("household_aum",     "Household AUM",     "integer", 20,  "measure",   "quantitative", "Sum"),
    ("aum_band",          "AUM Band",          "string",  130, "dimension", "nominal",      "Count"),
    ("engagement_score",  "Engagement Score",  "integer", 20,  "measure",   "quantitative", "Sum"),
    ("engagement_band",   "Engagement Band",   "string",  130, "dimension", "nominal",      "Count"),
    ("advisor_id",        "Advisor ID",        "string",  130, "dimension", "nominal",      "Count"),
    ("send_date",         "Send Date",         "date",    7,   "dimension", "ordinal",      "Year"),
    ("delivered",         "Delivered",         "integer", 20,  "measure",   "quantitative", "Sum"),
    ("opened",            "Opened",            "integer", 20,  "measure",   "quantitative", "Sum"),
    ("clicked",           "Clicked",           "integer", 20,  "measure",   "quantitative", "Sum"),
    ("responded",         "Responded",         "integer", 20,  "measure",   "quantitative", "Sum"),
    ("converted",         "Converted",         "integer", 20,  "measure",   "quantitative", "Sum"),
    ("conversion_value",  "Conversion Value",  "real",    5,   "measure",   "quantitative", "Sum"),
    ("contact_cost",      "Contact Cost",      "real",    5,   "measure",   "quantitative", "Sum"),
]

# --- Calculated fields: (name, caption, formula, datatype) -------------------------------
# Tableau-authored logic that Genie Code should translate into metric-view measures.
CALCS = [
    ("Calculation_Contacts",       "Contacts",                  "COUNT([household_id])",                       "integer"),
    ("Calculation_Conversions",    "Conversions",               "SUM([converted])",                            "integer"),
    ("Calculation_ConversionRate", "Conversion Rate",           "SUM([converted])/COUNT([household_id])",      "real"),
    ("Calculation_NetValue",       "Net Value",                 "SUM([conversion_value]) - SUM([contact_cost])", "real"),
    ("Calculation_CostPerConv",    "Cost per Conversion",       "SUM([contact_cost]) / SUM([converted])",      "real"),
    ("Calculation_OpenRate",       "Open Rate",                 "SUM([opened]) / COUNT([opened])",             "real"),
    ("Calculation_TargetLift",     "Target vs Holdout Lift",
     "SUM(IIF([audience_group] = 'Target', [converted], 0)) / SUM(IIF([audience_group] = 'Target', 1, 0))"
     " - SUM(IIF([audience_group] = 'Holdout', [converted], 0)) / SUM(IIF([audience_group] = 'Holdout', 1, 0))",
     "real"),
    ("Calculation_CampaignCVR",    "Campaign Conversion Rate (FIXED)",
     "{FIXED [campaign_name] : SUM([converted]) / COUNT([household_id])}",            "real"),
    ("Calculation_SendWeek",       "Send Week",                 "DATETRUNC('week', [send_date])",              "date"),
]


def metadata_record(name, local_type, remote_type, ordinal, aggregation):
    extra = "<precision>15</precision>" if local_type == "real" else ""
    return f"""          <metadata-record class='column'>
            <remote-name>{attr(name)}</remote-name>
            <remote-type>{remote_type}</remote-type>
            <local-name>[{attr(name)}]</local-name>
            <parent-name>[{TABLE}]</parent-name>
            <remote-alias>{attr(name)}</remote-alias>
            <ordinal>{ordinal}</ordinal>
            <local-type>{local_type}</local-type>
            <aggregation>{aggregation}</aggregation>
            {extra}
            <contains-null>true</contains-null>
          </metadata-record>"""


meta_records = "\n".join(
    metadata_record(c[0], c[2], c[3], i + 1, c[6]) for i, c in enumerate(COLS)
)

col_defs = []
for name, caption, ltype, rtype, role, ttype, agg in COLS:
    col_defs.append(
        f"      <column caption='{attr(caption)}' datatype='{ltype}' name='[{attr(name)}]' role='{role}' type='{ttype}' />"
    )
for name, caption, formula, dt in CALCS:
    role = "dimension" if dt == "date" else "measure"
    ttype = "ordinal" if dt == "date" else "quantitative"
    col_defs.append(
        f"""      <column caption='{attr(caption)}' datatype='{dt}' name='[{name}]' role='{role}' type='{ttype}'>
        <calculation class='tableau' formula='{attr(formula)}' />
      </column>"""
    )
col_defs_xml = "\n".join(col_defs)

datasource_xml = f"""    <datasource caption='{attr(DS_CAPTION)}' inline='true' name='{DS_NAME}' version='18.1'>
      <connection class='databricks' server='{DBX_SERVER}' dbname='{CATALOG}' schema='{SCHEMA}' http-path='{DBX_HTTP_PATH}' authentication='oauth' port='443'>
        <relation name='{TABLE}' table='[{SCHEMA}].[{TABLE}]' type='table' />
        <metadata-records>
{meta_records}
        </metadata-records>
      </connection>
{col_defs_xml}
      <layout dim-ordering='alphabetic' dim-percentage='0.5' measure-ordering='alphabetic' measure-percentage='0.5' show-structure='true' />
    </datasource>"""


# --- instances / dependencies --------------------------------------------------------------
D = f"[{DS_NAME}]"
DERIV = {"None": "none", "Sum": "sum", "CountD": "ctd", "TruncWeek": "twk", "Year": "yr"}


def col_dep(name, dt, role, ttype):
    return f"            <column datatype='{dt}' name='[{name}]' role='{role}' type='{ttype}' />"


def col_instance(col, derivation, kind):
    """Returns (instance_name, column-instance xml). kind: nk=nominal, ok=ordinal, qk=quantitative."""
    pref = DERIV[derivation]
    inst_name = f"[{pref}:{col}:{kind}]"
    ttype = {"nk": "nominal", "ok": "ordinal", "qk": "quantitative"}[kind]
    return inst_name, (f"            <column-instance column='[{col}]' derivation='{derivation}' "
                       f"name='{inst_name}' pivot='key' type='{ttype}' />")


def calc_instance(calc_name, kind="qk"):
    inst_name = f"[none:{calc_name}:{kind}]"
    ttype = {"nk": "nominal", "ok": "ordinal", "qk": "quantitative"}[kind]
    return inst_name, (f"            <column-instance column='[{calc_name}]' derivation='None' "
                       f"name='{inst_name}' pivot='key' type='{ttype}' />")


# base-column meta for dependency blocks
COL_META = {c[0]: (c[2], c[4], c[5]) for c in COLS}
CALC_META = {c[0]: (c[3], "measure" if c[3] != "date" else "dimension",
                    "quantitative" if c[3] != "date" else "ordinal") for c in CALCS}


class Sheet:
    """Collects dependency columns + instances and returns the field refs needed for shelves."""

    def __init__(self):
        self.deps = {}
        self.insts = {}

    def base(self, col, derivation="None", kind=None):
        ltype, role, ttype = COL_META[col]
        if kind is None:
            kind = "nk" if ttype == "nominal" else ("ok" if ttype == "ordinal" else "qk")
        self.deps[col] = col_dep(col, ltype, role, ttype)
        iname, ix = col_instance(col, derivation, kind)
        self.insts[iname] = ix
        return f"{D}.{iname}"

    def calc(self, calc_name):
        dt, role, ttype = CALC_META[calc_name]
        self.deps[calc_name] = col_dep(calc_name, dt, role, ttype)
        iname, ix = calc_instance(calc_name, "nk" if ttype == "ordinal" else "qk")
        self.insts[iname] = ix
        return f"{D}.{iname}"

    def deps_xml(self):
        return "\n".join(self.deps.values())

    def insts_xml(self):
        return "\n".join(self.insts.values())


def dims_filter(sheet, fields):
    """Quick-filter field refs (Campaign, Region) so every chart can be filtered from the dashboard."""
    refs = []
    for f in fields:
        refs.append(sheet.base(f, "None", "nk"))
    return refs


QUICK_FILTERS = ["campaign_name", "region"]


def filter_xml(field_ref_list):
    out = []
    for ref in field_ref_list:
        level = ref.split(".")[-1]  # e.g. [none:campaign_name:nk]
        out.append(
            f"          <filter class='categorical' column='{ref}'>\n"
            f"            <groupfilter function='level-members' level='{level}' />\n"
            f"          </filter>"
        )
    return "\n".join(out)


def worksheet(name, sheet, mark, rows, cols, color=None, text=None, sort="", target_only=True):
    """rows/cols/color/text are field refs (strings) already registered on `sheet`.
    target_only: worksheet-level member filter audience_group = 'Target' (not a quick filter)."""
    qf_refs = dims_filter(sheet, QUICK_FILTERS)
    filters = filter_xml(qf_refs)
    if target_only:
        aud = sheet.base("audience_group", "None", "nk")
        aud_level = aud.split(".")[-1]
        filters += ("\n          <filter class='categorical' column='" + aud + "'>\n"
                    "            <groupfilter function='member' level='" + aud_level + "' member='&quot;Target&quot;' />\n"
                    "          </filter>")
    encodings = []
    if color:
        encodings.append(f"            <color column='{color}' />")
    if text:
        encodings.append(f"            <text column='{text}' />")
    enc_xml = ("\n          <encodings>\n" + "\n".join(encodings) + "\n          </encodings>") if encodings else ""
    return f"""    <worksheet name='{attr(name)}'>
      <table>
        <view>
          <datasources>
            <datasource caption='{attr(DS_CAPTION)}' name='{DS_NAME}' />
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
{sheet.deps_xml()}
{sheet.insts_xml()}
          </datasource-dependencies>
{filters}{sort}
          <aggregation value='true' />
        </view>
        <style />
        <panes>
          <pane>
            <view><breakdown value='auto' /></view>
            <mark class='{mark}' />{enc_xml}
          </pane>
        </panes>
        <rows>{rows}</rows>
        <cols>{cols}</cols>
      </table>
    </worksheet>"""


def sort_desc(sheet_dim_ref, using_ref):
    return (f"\n          <sort class='computed' column='{sheet_dim_ref}' direction='DESC' "
            f"using='{using_ref}' />")


worksheets = []

# ---- 4 KPI text tiles -------------------------------------------------------------------
for ws_name, calc in [("KPI Contacts", "Calculation_Contacts"),
                      ("KPI Conversions", "Calculation_Conversions"),
                      ("KPI Conversion Rate", "Calculation_ConversionRate"),
                      ("KPI Net Value", "Calculation_NetValue")]:
    sh = Sheet()
    m = sh.calc(calc)
    worksheets.append(worksheet(ws_name, sh, "Text", rows="", cols=m, text=m))

# ---- Conversion rate by campaign split by audience group (grouped bars) ----------------
sh = Sheet()
camp = sh.base("campaign_name")
aud = sh.base("audience_group")
cvr = sh.calc("Calculation_ConversionRate")
worksheets.append(worksheet("Conversion Rate by Campaign and Audience", sh, "Bar",
                            rows=cvr, cols=camp, color=aud, target_only=False))

# ---- Conversions over time by send week, colored by campaign (line) -------------------
sh = Sheet()
week = sh.base("send_date", "TruncWeek", "qk")
conv_sum = sh.base("converted", "Sum", "qk")
campc = sh.base("campaign_name")
worksheets.append(worksheet("Weekly Conversions by Campaign", sh, "Line",
                            rows=conv_sum, cols=week, color=campc))

# ---- Net value by channel --------------------------------------------------------------
sh = Sheet()
chan = sh.base("channel")
nv = sh.calc("Calculation_NetValue")
worksheets.append(worksheet("Net Value by Channel", sh, "Bar",
                            rows=nv, cols=chan,
                            sort=sort_desc(chan, nv)))

# ---- Segment x campaign crosstab of conversion rate ------------------------------------
sh = Sheet()
seg = sh.base("segment")
camp2 = sh.base("campaign_name")
cvr2 = sh.calc("Calculation_ConversionRate")
worksheets.append(worksheet("Conversion Rate by Segment and Campaign", sh, "Square",
                            rows=seg, cols=camp2, color=cvr2, text=cvr2))

worksheets_xml = "\n".join(worksheets)

# --- dashboard ---------------------------------------------------------------------------
KPI_SHEETS = ["KPI Contacts", "KPI Conversions", "KPI Conversion Rate", "KPI Net Value"]
CHART_BANDS = [
    ["Conversion Rate by Campaign and Audience", "Weekly Conversions by Campaign"],
    ["Net Value by Channel", "Conversion Rate by Segment and Campaign"],
]
TITLE_H, FILTER_H, KPI_H = 7000, 6000, 12000


def dashboard_xml():
    zid = [10]

    def nz():
        zid[0] += 1
        return zid[0]

    zones = []
    y = 0
    zones.append(f"          <zone h='{TITLE_H}' id='{nz()}' type-v2='title' w='100000' x='0' y='{y}' />")
    y += TITLE_H
    # Quick filters: Campaign and Region
    zones.append(f"          <zone h='{FILTER_H}' id='{nz()}' param='{D}.[none:campaign_name:nk]' "
                 f"type-v2='filter' w='50000' x='0' y='{y}' />")
    zones.append(f"          <zone h='{FILTER_H}' id='{nz()}' param='{D}.[none:region:nk]' "
                 f"type-v2='filter' w='50000' x='50000' y='{y}' />")
    y += FILTER_H
    kpi_w = 100000 // len(KPI_SHEETS)
    for i, ws in enumerate(KPI_SHEETS):
        zones.append(f"          <zone h='{KPI_H}' id='{nz()}' name='{attr(ws)}' w='{kpi_w}' x='{i * kpi_w}' y='{y}' />")
    y += KPI_H
    band_h = (100000 - y) // len(CHART_BANDS)
    for bi, band in enumerate(CHART_BANDS):
        w = 100000 // len(band)
        by = y + bi * band_h
        for i, ws in enumerate(band):
            zones.append(f"          <zone h='{band_h}' id='{nz()}' name='{attr(ws)}' w='{w}' x='{i * w}' y='{by}' />")
    zones_xml = "\n".join(zones)
    return f"""    <dashboard name='{attr(DASHBOARD)}'>
      <style />
      <size maxheight='850' maxwidth='1250' minheight='850' minwidth='1250' />
      <zones>
        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>
{zones_xml}
        </zone>
      </zones>
      <devicelayouts />
    </dashboard>"""


dashboards_xml = dashboard_xml()

# --- windows -----------------------------------------------------------------------------
ws_names = KPI_SHEETS + [n for band in CHART_BANDS for n in band]
windows = []
for ws in ws_names:
    windows.append(f"""    <window class='worksheet' name='{attr(ws)}'>
      <cards>
        <edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>
        <edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip></edge>
      </cards>
    </window>""")
windows.append(f"""    <window class='dashboard' name='{attr(DASHBOARD)}'>
      <viewpoints />
      <active id='-1' />
    </window>""")
windows_xml = "\n".join(windows)

twb = f"""<?xml version='1.0' encoding='utf-8' ?>

<!-- Mock legacy Tableau dashboard for Databricks Genie Code BI-import exercise -->
<workbook original-version='18.1' source-build='2024.1.0' source-platform='mac' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-name>Campaign Performance</document-name>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
{datasource_xml}
  </datasources>
  <worksheets>
{worksheets_xml}
  </worksheets>
  <dashboards>
{dashboards_xml}
  </dashboards>
  <windows source-height='30'>
{windows_xml}
  </windows>
</workbook>
"""

# --- write + validate -----------------------------------------------------------------------
minidom.parseString(twb.encode("utf-8"))  # raises if not well-formed
print("twb XML is well-formed OK")

twb_path = os.path.join(HERE, "campaign_performance.twb")
with open(twb_path, "w", encoding="utf-8") as f:
    f.write(twb)
print(f"wrote {twb_path}  ({len(twb)} bytes, {len(worksheets)} worksheets, 1 dashboard)")

twbx_path = os.path.join(HERE, "campaign_performance.twbx")
with zipfile.ZipFile(twbx_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(twb_path, "campaign_performance.twb")
    z.write(DETAIL_CSV, "Data/campaign_results_detail.csv")
print(f"wrote {twbx_path}")
