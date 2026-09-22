"""Generate synthetic marketing-campaign files (external 'outside the platform' data)
that join to the firm household table. Deterministic (seeded) so the repo files are stable.
Outputs: files/campaigns.csv (dim), files/campaign_results.csv (fact w/ Target + Holdout)."""
import csv, random, datetime, os

random.seed(42)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = os.path.join(HERE, "files")

# --- load firm households ---
hh = []
with open("/tmp/households.csv") as f:
    for row in csv.DictReader(f):
        row["engagement_score"] = int(row["engagement_score"])
        row["email_opt_in"] = row["email_opt_in"].lower() == "true"
        hh.append(row)

# --- campaign definitions ---
campaigns = [
    dict(campaign_id="CMP_001", campaign_name="Spring Retirement Readiness", channel="Email",
         objective="Cross-sell retirement products", start="2026-03-02", end="2026-03-31",
         cost_per_contact=0.50, eligible=lambda h: h["segment"] in ("Mass Affluent","Affluent") and h["email_opt_in"]),
    dict(campaign_id="CMP_002", campaign_name="Annual Wealth Review Invitation", channel="Direct Mail",
         objective="Book advisor reviews and deepen relationships", start="2026-04-06", end="2026-04-30",
         cost_per_contact=4.50, eligible=lambda h: h["segment"] in ("Affluent","High Net Worth","Ultra HNW")),
    dict(campaign_id="CMP_003", campaign_name="Rollover Retargeting", channel="Digital",
         objective="Capture held-away rollover assets", start="2026-05-04", end="2026-05-29",
         cost_per_contact=1.20, eligible=lambda h: h["segment"] in ("Mass Market","Mass Affluent")),
]

BASE = {"Mass Market":0.010,"Mass Affluent":0.015,"Affluent":0.020,"High Net Worth":0.025,"Ultra HNW":0.030}
# additive lift (target only) by campaign x segment — designed story:
LIFT = {
    "CMP_001": {"Mass Affluent":0.050,"Affluent":0.060},                                  # email cross-sell: great, cheap
    "CMP_002": {"Affluent":0.030,"High Net Worth":0.090,"Ultra HNW":0.110},               # mail: pays off HNW+, marginal Affluent
    "CMP_003": {"Mass Market":0.012,"Mass Affluent":0.020},                               # digital: weak lift, story = reallocate
}
VALRANGE = {"Mass Market":(150,800),"Mass Affluent":(800,3000),"Affluent":(3000,10000),
            "High Net Worth":(10000,40000),"Ultra HNW":(40000,150000)}
OPEN_RATE = {"Email":0.38,"Digital":0.30}

def ddate(start,end):
    s=datetime.date.fromisoformat(start); e=datetime.date.fromisoformat(end)
    return (s+datetime.timedelta(days=random.randint(0,(e-s).days))).isoformat()

rows=[]; summ={}
for c in campaigns:
    elig=[h for h in hh if c["eligible"](h)]
    for h in elig:
        seg=h["segment"]; grp = "Target" if random.random()<0.85 else "Holdout"
        eng_mult = 0.5 + h["engagement_score"]/100.0
        chan_match = 1.2 if h["primary_channel"]==c["channel"] else 1.0
        p = BASE[seg]
        if grp=="Target":
            p += LIFT[c["id"] if False else c["campaign_id"]].get(seg,0.0) * eng_mult * chan_match
        # funnel
        if grp=="Target":
            delivered = 1 if random.random()<(0.99 if c["channel"]=="Direct Mail" else 0.97) else 0
            send_date = ddate(c["start"],c["end"]); cost=c["cost_per_contact"]
            if c["channel"] in OPEN_RATE and delivered:
                opened = 1 if random.random()<(OPEN_RATE[c["channel"]]*eng_mult) else 0
                clicked = 1 if (opened and random.random()<0.28) else 0
            else:
                opened=clicked=None   # direct mail: no open/click tracking
        else:
            delivered=0; send_date=""; cost=0.0; opened=clicked=None
        converted = 1 if (delivered or grp=="Holdout") and random.random()<p else 0
        if grp=="Holdout":  # holdout can convert organically at base rate
            converted = 1 if random.random()<BASE[seg] else 0
        responded = 1 if converted or (clicked==1) or (opened==1 and random.random()<0.3) else 0
        if grp=="Holdout": responded=0
        lo,hivar=VALRANGE[seg]; cval = round(random.uniform(lo,hivar),2) if converted else 0.0
        rows.append([c["campaign_id"],h["household_id"],grp,send_date,delivered,
                     "" if opened is None else opened,"" if clicked is None else clicked,
                     responded,converted,cval,round(cost,2)])
        s=summ.setdefault((c["campaign_id"],grp),[0,0,0.0,0.0])
        s[0]+=1; s[1]+=converted; s[2]+=cval; s[3]+=cost

# write files
with open(os.path.join(FILES,"campaigns.csv"),"w",newline="") as f:
    w=csv.writer(f); w.writerow(["campaign_id","campaign_name","channel","objective","start_date","end_date","cost_per_contact","budget"])
    for c in campaigns:
        n_t=summ.get((c["campaign_id"],"Target"),[0])[0]
        w.writerow([c["campaign_id"],c["campaign_name"],c["channel"],c["objective"],c["start"],c["end"],
                    f'{c["cost_per_contact"]:.2f}', round(n_t*c["cost_per_contact"]*1.1,2)])
with open(os.path.join(FILES,"campaign_results.csv"),"w",newline="") as f:
    w=csv.writer(f); w.writerow(["campaign_id","household_id","audience_group","send_date","delivered","opened","clicked","responded","converted","conversion_value","contact_cost"])
    w.writerows(rows)

print(f"campaign_results rows: {len(rows)}")
print(f"{'campaign':10} {'group':8} {'n':>6} {'conv':>5} {'cvr%':>6} {'value':>12} {'cost':>10}")
for (cid,grp),s in sorted(summ.items()):
    cvr = 100*s[1]/s[0] if s[0] else 0
    print(f"{cid:10} {grp:8} {s[0]:6d} {s[1]:5d} {cvr:6.2f} {s[2]:12.0f} {s[3]:10.0f}")
