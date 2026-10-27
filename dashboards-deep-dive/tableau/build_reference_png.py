#!/usr/bin/env python3
"""Build the 'legacy Tableau dashboard' reference page for campaign_performance.twb.

All numbers are computed directly from ../data/campaign_results_detail.csv using the same
definitions as the workbook's calculated fields. The page is written to campaign_performance.html
and then screenshotted with Chrome DevTools to produce campaign_performance.png (1280x760).
"""
import csv
import datetime as dt
import html
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DETAIL = os.path.join(HERE, "..", "data", "campaign_results_detail.csv")
OUT_HTML = os.path.join(HERE, "campaign_performance.html")

rows = list(csv.DictReader(open(DETAIL, newline="")))
for r in rows:
    r["converted"] = int(r["converted"])
    r["conversion_value"] = float(r["conversion_value"])
    r["contact_cost"] = float(r["contact_cost"])
    r["opened"] = int(r["opened"]) if r["opened"] != "" else None

# ---- KPIs (calculated-field definitions) --------------------------------------------------
# Headline KPIs and channel/crosstab views are Target-audience only (worksheet-level filter in the workbook).
tgt = [r for r in rows if r["audience_group"] == "Target"]
contacts = len(tgt)                                             # COUNT([household_id]) on Target rows
conversions = sum(r["converted"] for r in tgt)                  # SUM([converted])
cvr = conversions / contacts                                    # SUM(converted)/COUNT(household_id)
net_value = sum(r["conversion_value"] for r in tgt) - sum(r["contact_cost"] for r in tgt)

def money_m(v):
    return f"${v / 1e6:.2f}M"

# ---- Conversion rate by campaign x audience_group --------------------------------------------
CAMPAIGNS = sorted({r["campaign_name"] for r in rows})
cell = defaultdict(lambda: [0, 0])  # (campaign, group) -> [converted, contacts]
for r in rows:
    k = (r["campaign_name"], r["audience_group"])
    cell[k][0] += r["converted"]
    cell[k][1] += 1
cvr_by_camp_group = {k: v[0] / v[1] for k, v in cell.items()}
lift_pts = (
    sum(r["converted"] for r in rows if r["audience_group"] == "Target")
    / sum(1 for r in rows if r["audience_group"] == "Target")
    - sum(r["converted"] for r in rows if r["audience_group"] == "Holdout")
    / sum(1 for r in rows if r["audience_group"] == "Holdout")
)

# ---- Weekly conversions (Tableau DATETRUNC('week') = Sunday start), Target rows only ----------
def week_start(d):
    return d - dt.timedelta(days=(d.weekday() + 1) % 7)

weekly = defaultdict(lambda: defaultdict(int))  # week -> campaign -> conversions
for r in rows:
    if not r["send_date"]:  # holdout rows have no send_date and drop out of the time series
        continue
    d = dt.date.fromisoformat(r["send_date"])
    weekly[week_start(d)][r["campaign_name"]] += r["converted"]
WEEKS = sorted(weekly)

# ---- Net value by channel ----------------------------------------------------------------------
nv_by_channel = defaultdict(float)
for r in tgt:
    nv_by_channel[r["channel"]] += r["conversion_value"] - r["contact_cost"]
CHANNELS = sorted(nv_by_channel, key=lambda c: -nv_by_channel[c])

# ---- Segment x campaign conversion rate ----------------------------------------------------------
seg_cell = defaultdict(lambda: [0, 0])
for r in tgt:
    k = (r["segment"], r["campaign_name"])
    seg_cell[k][0] += r["converted"]
    seg_cell[k][1] += 1
SEGMENTS = ["Mass Market", "Mass Affluent", "Affluent", "High Net Worth", "Ultra HNW"]
SEGMENTS = [s for s in SEGMENTS if any(k[0] == s for k in seg_cell)]
seg_cvr = {k: (v[0] / v[1] if v[1] else None) for k, v in seg_cell.items()}

# ---- SVG helpers -------------------------------------------------------------------------------
PALETTE = ["#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#76B7B2", "#EDC948"]
GROUP_COLORS = {"Target": "#4E79A7", "Holdout": "#BAB0AC"}
CAMP_COLORS = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(CAMPAIGNS)}


def grouped_bars():
    W, H = 600, 218
    pad_l, pad_b, pad_t = 46, 34, 14
    plot_w, plot_h = W - pad_l - 10, H - pad_b - pad_t
    vmax = max(cvr_by_camp_group.values()) * 1.15
    out = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Arial,sans-serif">']
    for k in range(5):
        v = vmax * k / 4
        y = pad_t + plot_h - plot_h * k / 4
        out.append(f'<line x1="{pad_l}" x2="{W - 10}" y1="{y:.1f}" y2="{y:.1f}" stroke="#eee"/>')
        out.append(f'<text x="{pad_l - 6}" y="{y + 3:.1f}" font-size="10" fill="#888" text-anchor="end">{v * 100:.0f}%</text>')
    group_w = plot_w / len(CAMPAIGNS)
    bar_w = 46
    for i, camp in enumerate(CAMPAIGNS):
        gx = pad_l + i * group_w + group_w / 2
        for j, grp in enumerate(["Target", "Holdout"]):
            v = cvr_by_camp_group[(camp, grp)]
            h = plot_h * v / vmax
            x = gx - bar_w - 3 + j * (bar_w + 6)
            y = pad_t + plot_h - h
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{GROUP_COLORS[grp]}"/>')
            out.append(f'<text x="{x + bar_w / 2:.1f}" y="{y - 4:.1f}" font-size="10" fill="#333" text-anchor="middle">{v * 100:.1f}%</text>')
        label = html.escape(camp)
        out.append(f'<text x="{gx:.1f}" y="{H - 14}" font-size="10" fill="#555" text-anchor="middle">{label}</text>')
    out.append("</svg>")
    return "".join(out)


def line_chart():
    W, H = 600, 218
    pad_l, pad_b, pad_t = 40, 34, 14
    plot_w, plot_h = W - pad_l - 14, H - pad_b - pad_t
    vmax = max(max(d.values()) for d in weekly.values()) * 1.15
    n = len(WEEKS)
    xs = [pad_l + (plot_w * i / (n - 1)) for i in range(n)]
    out = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Arial,sans-serif">']
    for k in range(4):
        v = vmax * k / 3
        y = pad_t + plot_h - plot_h * k / 3
        out.append(f'<line x1="{pad_l}" x2="{W - 14}" y1="{y:.1f}" y2="{y:.1f}" stroke="#eee"/>')
        out.append(f'<text x="{pad_l - 6}" y="{y + 3:.1f}" font-size="10" fill="#888" text-anchor="end">{v:.0f}</text>')
    for camp in CAMPAIGNS:
        pts = []
        for i, w in enumerate(WEEKS):
            v = weekly[w].get(camp, 0)
            pts.append((xs[i], pad_t + plot_h - plot_h * v / vmax))
        d = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
        out.append(f'<path d="{d}" fill="none" stroke="{CAMP_COLORS[camp]}" stroke-width="2"/>')
        for x, y in pts:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="{CAMP_COLORS[camp]}"/>')
    for i, w in enumerate(WEEKS):
        if i % 2 == 0:
            out.append(f'<text x="{xs[i]:.1f}" y="{H - 14}" font-size="9" fill="#888" text-anchor="middle">{w.strftime("%b %d")}</text>')
    out.append("</svg>")
    return "".join(out)


def net_value_bars():
    W, H = 600, 218
    pad_l, pad_b, pad_t = 56, 34, 14
    plot_w, plot_h = W - pad_l - 10, H - pad_b - pad_t
    step = 500_000
    vmax = -(-max(nv_by_channel.values()) * 1.15 // step) * step  # round up to $500K
    n = len(CHANNELS)
    slot = plot_w / n
    out = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Arial,sans-serif">']
    for k in range(4):
        v = vmax * k / 3
        y = pad_t + plot_h - plot_h * k / 3
        out.append(f'<line x1="{pad_l}" x2="{W - 10}" y1="{y:.1f}" y2="{y:.1f}" stroke="#eee"/>')
        lbl = "$0" if v == 0 else (f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:.0f}K")
        out.append(f'<text x="{pad_l - 6}" y="{y + 3:.1f}" font-size="10" fill="#888" text-anchor="end">{lbl}</text>')
    for i, ch in enumerate(CHANNELS):
        v = nv_by_channel[ch]
        h = plot_h * v / vmax
        x = pad_l + i * slot + slot * 0.25
        w = slot * 0.5
        y = pad_t + plot_h - h
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="#4E79A7"/>')
        out.append(f'<text x="{x + w / 2:.1f}" y="{y - 4:.1f}" font-size="10" fill="#333" text-anchor="middle">${v / 1e3:,.0f}K</text>')
        out.append(f'<text x="{x + w / 2:.1f}" y="{H - 14}" font-size="10" fill="#555" text-anchor="middle">{html.escape(ch)}</text>')
    out.append("</svg>")
    return "".join(out)


def heat_table():
    def shade(v):
        if v is None:
            return "#fff"
        t = min(v / 0.12, 1.0)  # 0 -> white, 12% -> full blue
        r = int(255 - (255 - 78) * t)
        g = int(255 - (255 - 121) * t)
        b = int(255 - (255 - 167) * t)
        return f"rgb({r},{g},{b})"

    head = "".join(f"<th>{html.escape(c)}</th>" for c in CAMPAIGNS)
    body = []
    for s in SEGMENTS:
        tds = []
        for c in CAMPAIGNS:
            v = seg_cvr.get((s, c))
            txt = "–" if v is None else f"{v * 100:.1f}%"
            color = "#fff" if (v or 0) > 0.07 else "#222"
            tds.append(f'<td style="background:{shade(v)};color:{color}">{txt}</td>')
        body.append(f"<tr><th class='rowh'>{html.escape(s)}</th>{''.join(tds)}</tr>")
    return f"<table class='xt'><tr><th></th>{head}</tr>{''.join(body)}</table>"


# ---- page -----------------------------------------------------------------------------------------
kpi_tiles = [
    ("Contacts", f"{contacts:,}", "#4E79A7"),
    ("Conversions", f"{conversions:,}", "#59A14F"),
    ("Conversion Rate", f"{cvr * 100:.1f}%", "#F28E2B"),
    ("Net Value", money_m(net_value), "#B07AA1"),
]
kpi_html = "".join(
    f'<div class="kpi" style="border-top-color:{c}"><div class="lab">{l}</div><div class="val">{v}</div></div>'
    for l, v, c in kpi_tiles
)

sent = sorted(r["send_date"] for r in rows if r["send_date"])
first_wk = dt.date.fromisoformat(sent[0]).strftime("%b %d")
last_wk = dt.date.fromisoformat(sent[-1]).strftime("%b %d, %Y")

CSS = """
* { box-sizing: border-box; }
html, body { margin:0; width:1280px; height:760px; overflow:hidden; }
body { font-family: Arial, 'Helvetica Neue', sans-serif; background:#e6e6e6; color:#333; }
.toolbar { height:30px; background:#f3f3f3; border-bottom:1px solid #ccc; display:flex; align-items:center; padding:0 12px; gap:18px; font-size:12px; color:#666; }
.toolbar .brand { font-weight:700; color:#1f3b57; }
.canvas { background:#fff; height:668px; padding:10px 16px 0; }
.title { display:flex; align-items:baseline; justify-content:space-between; }
.title h1 { margin:0; font-size:20px; color:#2b2b2b; }
.title .sub { font-size:11px; color:#888; }
.filters { display:flex; gap:12px; margin:8px 0 6px; font-size:11px; color:#555; }
.fbox { border:1px solid #ccc; padding:3px 8px; min-width:200px; background:#fafafa; }
.fbox b { font-weight:600; margin-right:6px; color:#333; }
.kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:8px; }
.kpi { border:1px solid #e0e0e0; border-top:3px solid #4e79a7; background:#fafafa; padding:6px 12px; height:64px; }
.kpi .lab { font-size:10px; text-transform:uppercase; letter-spacing:.6px; color:#888; }
.kpi .val { font-size:24px; font-weight:700; color:#2b2b2b; margin-top:2px; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.panel { border:1px solid #e0e0e0; padding:6px 10px 2px; height:252px; overflow:hidden; }
.panel h3 { margin:0 0 4px; font-size:12px; color:#444; font-weight:700; }
.panel h3 span { font-weight:400; color:#999; font-size:10px; margin-left:6px; }
.xt { border-collapse:collapse; font-size:12px; width:100%; margin-top:6px; }
.xt th, .xt td { border:1px solid #fff; padding:9px 6px; text-align:center; font-variant-numeric:tabular-nums; }
.xt th { background:#f3f3f3; font-weight:600; color:#555; font-size:11px; }
.xt th.rowh { text-align:right; }
.tabs { height:30px; background:#e6e6e6; border-top:1px solid #ccc; display:flex; align-items:flex-end; gap:2px; padding:0 8px; font-size:11px; }
.tab { padding:5px 14px; background:#d6d6d6; color:#555; border:1px solid #c8c8c8; border-bottom:none; }
.tab.active { background:#fff; color:#1f3b57; font-weight:700; }
"""

legend = (
    '<span style="color:#4E79A7">&#9632; Target</span> '
    '<span style="color:#BAB0AC">&#9632; Holdout</span>'
)
camp_legend = " ".join(
    f'<span style="color:{CAMP_COLORS[c]}">&#9632; {html.escape(c)}</span>' for c in CAMPAIGNS
)
chan_note = " · ".join(f"{html.escape(c)} {nv_by_channel[c] / 1e3:,.0f}K" for c in CHANNELS)

page = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Campaign Performance</title><style>{CSS}</style></head>
<body>
  <div class="toolbar">
    <span class="brand">Tableau Desktop</span>
    <span>File</span><span>Data</span><span>Worksheet</span><span>Dashboard</span><span>Analysis</span>
    <span style="margin-left:auto;color:#999">Connected to: Databricks &middot; your_catalog.your_schema.campaign_results_detail</span>
  </div>
  <div class="canvas">
    <div class="title">
      <h1>Campaign Performance</h1>
      <div class="sub">Sends {first_wk} &ndash; {last_wk} &middot; Target audience (Holdout shown for comparison in the conversion-rate chart)</div>
    </div>
    <div class="filters">
      <div class="fbox"><b>Campaign</b>All</div>
      <div class="fbox"><b>Region</b>All</div>
    </div>
    <div class="kpis">{kpi_html}</div>
    <div class="grid">
      <div class="panel">
        <h3>Conversion Rate by Campaign <span>{legend}</span></h3>
        {grouped_bars()}
      </div>
      <div class="panel">
        <h3>Conversions by Send Week <span>{camp_legend}</span></h3>
        {line_chart()}
      </div>
      <div class="panel">
        <h3>Net Value by Channel <span>{chan_note}</span></h3>
        {net_value_bars()}
      </div>
      <div class="panel">
        <h3>Conversion Rate: Segment &times; Campaign</h3>
        {heat_table()}
      </div>
    </div>
  </div>
  <div class="tabs">
    <div class="tab active">Campaign Performance</div>
    <div class="tab">Conversion Rate by Campaign and Audience</div>
    <div class="tab">Weekly Conversions by Campaign</div>
    <div class="tab">Net Value by Channel</div>
  </div>
</body></html>"""

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(page)

print(f"wrote {OUT_HTML}")
print(f"contacts={contacts} conversions={conversions} cvr={cvr:.4%} net_value={net_value:,.2f} ({money_m(net_value)})")
print(f"target-vs-holdout lift={lift_pts * 100:.2f} pts")
for camp in CAMPAIGNS:
    print(f"  {camp}: target={cvr_by_camp_group[(camp, 'Target')]:.4%} holdout={cvr_by_camp_group[(camp, 'Holdout')]:.4%}")
for ch in CHANNELS:
    print(f"  net value {ch}: {nv_by_channel[ch]:,.2f}")
