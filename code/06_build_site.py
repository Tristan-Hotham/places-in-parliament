"""Step 6: page data (data/site.json: one record per place; data/monthly.json: sparse monthly counts per place for the
place explorer) and index.html from code/page_template.html + code/page.css + the full-screen snippet, filled from
data/results.json. 10.5281/zenodo.24103127, https://doi.org/10.5281/zenodo.24103127 and https://blog.tristanhotham.com/2026/10/31/places-in-parliament/ are left for the publisher."""
import numpy as np, pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
Z = np.load(f"{SCR}/mats.npz", allow_pickle=False)
YM = Z["YM"]; TERMS = list(Z["terms"]); SEAT = Z["SEAT"]; YEARS = Z["years"]
PL = pd.read_csv(f"{DATA}/places.csv")
PY = pd.read_csv(f"{DATA}/place_years.csv")
BL = pd.read_csv(f"{DATA}/byelection_links.csv")
SE = pd.read_csv(f"{DATA}/shock_events.csv").fillna({"town": ""})
early = PL.term.map(PY[PY.year.between(1910, 1944)].groupby("term").in_mentions.sum()).fillna(0)
late = PL.term.map(PY[PY.year.between(1980, 2025)].groupby("term").in_mentions.sum()).fillna(0)
PL["lr"] = np.log2((late / late.sum() + 2e-5) / (early / early.sum() + 2e-5))
NT_ = YM.shape[1]
decs = []
for d in DECADES:
    a = mi(f"{d}-01"); b = mi(f"{min(d + 9, Y1)}-12") + 1
    decs.append(YM[:, a:b].sum(1))
decs.append(YM[:, mi(f"{Y0}-01"):mi(f"{Y1}-12") + 1].sum(1))     # index 12 = all years
DM = np.vstack(decs).T
dec_tot = DM.sum(0)
P = []
for i, t in enumerate(TERMS):
    r = PL.iloc[i]; assert r.term == t
    by = [[b.date[:7], b.seat, int(b.changed), int(b.main)] for b in BL[BL.term == t].sort_values("date").itertuples()]
    ds = [[s.date[:7], s.event, None if s.deaths != s.deaths else int(s.deaths), float(s.km), int(s.main)] for s in SE[SE.town == t].sort_values("date").itertuples()]
    rec = {"n": t, "la": round(float(r.lat), 4), "lo": round(float(r.lon), 4), "nat": r.nation, "pop": None if r["pop"] != r["pop"] else int(r["pop"]),
           "d": [round(float(x), 1) for x in DM[i]], "lr": round(float(PL.lr.iloc[i]), 3) if early.iloc[i] + late.iloc[i] >= 20 else None,
           "seat": int((SEAT[i] > 0).any()), "seatnow": int(SEAT[i, -1] > 0)}
    if by: rec["by"] = by
    if ds: rec["ds"] = ds
    P.append(rec)
site = {"decades": [f"{d}s" if d < 2020 else "2020 to 2025" for d in DECADES] + [f"{Y0} to {Y1}"], "dec_tot": [round(float(x)) for x in dec_tot], "p": P,
        "m0": "1909-01", "nm": int(NT_)}
jsave(site, f"{DATA}/site.json")
# monthly: per place [first month index, then (gap, value) pairs] in tenths
mon = {"m0": "1909-01", "nm": int(NT_), "tot": [round(float(x), 1) for x in YM.sum(0)], "p": {}}
for i, t in enumerate(TERMS):
    nz = np.nonzero(YM[i])[0]
    arr, last = [], -1
    for k in nz:
        arr += [int(k - last), round(float(YM[i, k]), 1)]; last = k
    mon["p"][t] = arr
jsave(mon, f"{DATA}/monthly.json")
print("site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB; monthly.json", os.path.getsize(f"{DATA}/monthly.json") // 1024, "KB")

KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{CSS}}", open(os.path.join(ROOT, "code", "page.css"), encoding="utf-8").read())
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "2026a")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
sj = json.dumps(site, ensure_ascii=False)
assert "—" not in sj and "–" not in sj
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
