"""Step 1: data construction (no outcome model). Builds the monthly "in <place>" series for every place term exactly as in
byelection-attention (variants added, prefix subtraction) and applies the precision factors of Mentioned in the House;
the seat-name indicator for every place and year from Who Won Here?; the shock indicators (by-elections and disasters);
and the disaster to town mapping. Outputs: data/places.csv, data/place_years.csv, data/hansard_monthly_clean.csv.gz,
data/disaster_towns.csv, data/byelection_links.csv, SCR/mats.npz, SCR/r_data.json."""
import collections
import numpy as np, pandas as pd
from common import *

H = jload(f"{RAW}/hansard_monthly.json")
P = pd.read_csv(f"{HP}/places.csv")
C = pd.read_csv(f"{ELEC}/contests.csv", dtype={"election": str})
OV = pd.read_csv(f"{BA}/code/overrides.csv").fillna("")

VARIANTS = {"Barrow in Furness": "Barrow-in-Furness", "Ashton in Makerfield": "Ashton-in-Makerfield", "Bishops Stortford": "Bishop's Stortford",
            "Kirkby in Ashfield": "Kirkby-in-Ashfield", "Newark on Trent": "Newark-on-Trent", "Newcastle under Lyme": "Newcastle-under-Lyme",
            "Lytham St Annes": "Lytham St Anne's", "Saint Andrews": "St Andrews", "Saint Neots": "St Neots", "Cwmbrân": "Cwmbran",
            "Abingdon-on-Thames": "Abingdon", "Droitwich Spa": "Droitwich", "Letchworth Garden City": "Letchworth",
            "Ellesmere Port Town": "Ellesmere Port", "Staines-upon-Thames": "Staines", "Londonderry County Borough": "Londonderry",
            "Manchester City Centre": "Manchester", "Brighton and Hove": "Brighton", "Amersham on the Hill": "Amersham",
            "Blaydon-on-Tyne": "Blaydon", "Royal Sutton Coldfield": "Sutton Coldfield", "Derry": "Londonderry",
            "Royal Leamington Spa": "Leamington", "Royal Tunbridge Wells": "Tunbridge Wells", "Royal Wootton Bassett": "Wootton Bassett"}


def series(d):
    a = np.zeros(NT)
    for k, v in d.items():
        i = mi(k)
        if 0 <= i < NT:
            a[i] += v
    return a


RAWS = {t: series(v) for t, v in H["inp"].items()}
_n = lambda x: re.sub(r"[^a-z0-9 ]", " ", x.lower()).split()
TOK = {t: _n(t) for t in RAWS}
PREFIX = collections.defaultdict(list)
for a, na in TOK.items():
    for b, nb in TOK.items():
        if len(nb) > len(na) and nb[:len(na)] == na:
            PREFIX[a].append(b)
Y, YNP = {}, {}
for t, a in RAWS.items():
    if t in VARIANTS:
        continue
    y = a.copy()
    for b in PREFIX.get(t, []):
        y = np.maximum(0, y - RAWS[b])
    var = sum((RAWS[v] for v, m in VARIANTS.items() if m == t and v in RAWS), np.zeros(NT))
    Y[t] = y + var
    YNP[t] = a + var
PL = P.set_index("term")
for r in OV[OV.kind == "point"].itertuples():
    la, lo = (float(x) for x in r.value.split(";"))
    PL.loc[r.term, "lat"], PL.loc[r.term, "lon"] = la, lo
# correction after the first run (whole-list audit of the top 200 places): "in Erskine" is almost always "in Erskine May",
# the Commons procedure manual, not the Renfrewshire town; left out like the other flagged names
EXCLUDE = {"Erskine": "\"in Erskine May\" (the procedure manual)"}
CLEAN = sorted(t for t in Y if t in PL.index and not isinstance(PL.loc[t, "flag"], str) and t not in EXCLUDE)
FACTOR = {t: float(PL.loc[t, "factor"]) for t in CLEAN}
IDX = {t: i for i, t in enumerate(CLEAN)}
NP_ = len(CLEAN)
YM = np.vstack([Y[t] * FACTOR[t] for t in CLEAN])            # main: prefix-subtracted, precision-scaled
YM_noscale = np.vstack([Y[t] for t in CLEAN])
YM_noprefix = np.vstack([YNP[t] * FACTOR[t] for t in CLEAN])
YEARS = np.arange(Y0, Y1 + 1)


def annual(M):
    out = np.zeros((M.shape[0], len(YEARS)))
    for j, y in enumerate(YEARS):
        a = mi(f"{y}-01"); out[:, j] = M[:, a:a + 12].sum(1)
    return out


A = annual(YM); A_ns = annual(YM_noscale); A_np = annual(YM_noprefix)

# ---------------------------------------------------------------- seat names at each year (general election in force on 1 July)
NAMES = {}
for t in Y:
    NAMES[norm(t)] = t
for v, m in VARIANTS.items():
    NAMES.setdefault(norm(v), m)
SEAT_ALIAS = {"the hartlepools": "hartlepool", "kingston upon hull": "hull",
              "cities of london": "city of london"}   # correction after the first run: the seat names the City, not London
SEAT_ALIAS.update({norm(r.seat): norm(r.term) for r in OV[OV.kind == "alias"].itertuples()})
CANDS = sorted(NAMES, key=lambda n: -len(n.split()))


def places_in(seat):
    s = norm(seat)
    for a, b in SEAT_ALIAS.items():
        s = s.replace(a, b)
    w = s.split()
    used, found = [False] * len(w), []
    for n in CANDS:
        nw = n.split(); L = len(nw)
        for i in range(len(w) - L + 1):
            if w[i:i + L] == nw and not any(used[i:i + L]):
                found.append(NAMES[n]); used[i:i + L] = [True] * L
    return sorted(set(found))


GE = C.groupby("date").constituency.apply(list).sort_index()
GE = GE[GE.index >= "1900-01-01"]
seat_count = {}
for d, seats in GE.items():
    cnt = collections.Counter()
    for s in seats:
        if "Universit" in s:
            continue
        for t in places_in(s):
            cnt[t] += 1
    seat_count[d] = cnt
SEAT = np.zeros((NP_, len(YEARS)), int)      # number of seats whose name contains the place
for j, y in enumerate(YEARS):
    d = max(x for x in GE.index if x <= f"{y}-07-01")
    for t, n in seat_count[d].items():
        if t in IDX:
            SEAT[IDX[t], j] = n

# ---------------------------------------------------------------- shocks: by-elections and disasters per place-year
E = pd.read_csv(f"{BA}/data/event_places.csv")
BL = E[(E.far == 0) & E.term.isin(CLEAN)][["id", "seat", "date", "term", "year", "main", "changed", "cause_group", "era"]].copy()
BL.to_csv(f"{DATA}/byelection_links.csv", index=False)
SH_BY = np.zeros((NP_, len(YEARS)), int)
for r in BL.itertuples():
    for dy in (0, 1):
        j = r.year + dy - Y0
        if 0 <= j < len(YEARS):
            SH_BY[IDX[r.term], j] = 1
D = pd.read_csv(f"{DA}/events.csv")
D = D[D.main == 1].copy()
pl_lat = np.array([PL.loc[t, "lat"] for t in CLEAN]); pl_lon = np.array([PL.loc[t, "lon"] for t in CLEAN])
rows = []
for r in D.itertuples():
    if r.kind == "in" and r.term in IDX:
        town, dist, how = r.term, 0.0, "event term is a Hansard town"
    else:
        dd = np.array([km(r.lat, r.lon, a, b) for a, b in zip(pl_lat, pl_lon)])
        i = int(np.argmin(dd))
        town, dist, how = (CLEAN[i], float(dd[i]), "nearest Hansard town") if dd[i] <= DIS_KM else ("", float(dd[i]), "no Hansard town within 10 km")
    rows.append({"id": r.id, "event": r.event, "date": r.date, "year": r.year, "deaths": r.deaths, "typegrp": r.typegrp,
                 "da_term": r.term, "da_kind": r.kind, "town": town, "km": round(dist, 1), "how": how, "lat": r.lat, "lon": r.lon,
                 "nation": r.nation})
DT = pd.DataFrame(rows)
DT.to_csv(f"{DATA}/disaster_towns.csv", index=False)
SH_DI = np.zeros((NP_, len(YEARS)), int)
for r in DT[DT.town != ""].itertuples():
    for dy in (0, 1):
        j = r.year + dy - Y0
        if 0 <= j < len(YEARS):
            SH_DI[IDX[r.town], j] = 1

# ---------------------------------------------------------------- outputs
pop = np.array([PL.loc[t, "pop"] for t in CLEAN], float)
nation = [PL.loc[t, "nation"] for t in CLEAN]
dlon = np.array([km(CHARING[0], CHARING[1], a, b) for a, b in zip(pl_lat, pl_lon)])
np.savez_compressed(f"{SCR}/mats.npz", YM=YM, YM_noscale=YM_noscale, YM_noprefix=YM_noprefix, A=A, A_ns=A_ns, A_np=A_np,
                    SEAT=SEAT, SH_BY=SH_BY, SH_DI=SH_DI, pop=pop, lat=pl_lat, lon=pl_lon, dlon=dlon,
                    terms=np.array(CLEAN), nation=np.array(nation), years=YEARS)
PO = pd.DataFrame({"term": CLEAN, "lat": pl_lat, "lon": pl_lon, "nation": nation, "pop": pop, "pop_src": [PL.loc[t, "pop_src"] for t in CLEAN],
                   "factor": [FACTOR[t] for t in CLEAN], "km_charing_cross": dlon.round(1),
                   "in_1910_2025": A.sum(1).round(1)})
for d in DECADES:
    j0, j1 = d - Y0, min(d + 9, Y1) - Y0
    PO[f"in_{d}s"] = A[:, j0:j1 + 1].sum(1).round(1)
PO["seat_years"] = (SEAT > 0).sum(1)
PO["byelection_years"] = SH_BY.sum(1)
PO["disaster"] = (SH_DI.sum(1) > 0).astype(int)
PO.to_csv(f"{DATA}/places.csv", index=False)
py = []
for i, t in enumerate(CLEAN):
    for j, y in enumerate(YEARS):
        if A[i, j] > 0 or SEAT[i, j] > 0 or SH_BY[i, j] or SH_DI[i, j]:
            py.append((t, y, round(A[i, j], 2), SEAT[i, j], SH_BY[i, j], SH_DI[i, j]))
pd.DataFrame(py, columns=["term", "year", "in_mentions", "seats_named", "byelection_shock", "disaster_shock"]).to_csv(f"{DATA}/place_years.csv", index=False)
with gzip.open(f"{DATA}/hansard_monthly_clean.csv.gz", "wt", encoding="utf-8") as f:
    f.write("term,month,contributions\n")
    for i, t in enumerate(CLEAN):
        for k in np.nonzero(YM[i])[0]:
            f.write(f"\"{t}\",{ym(k)},{round(YM[i, k], 2):g}\n")
r = {"n_terms": len(P), "n_clean": NP_, "excluded_by_audit": EXCLUDE, "n_flag": int(len(P) - NP_), "n_variants": len(VARIANTS),
     "n_prefix_terms": int(sum(1 for t in CLEAN if PREFIX.get(t))), "n_scaled": int(sum(1 for t in CLEAN if FACTOR[t] < 1)),
     "years": [Y0, Y1], "total_1910_2025": round(float(A.sum())), "total_months": int(NT),
     "with_pop": int(np.isfinite(pop).sum()), "seat_places_ever": int((SEAT.sum(1) > 0).sum()),
     "byelection_links": int(len(BL)), "byelection_places": int(BL.term.nunique()), "byelection_place_years": int(SH_BY.sum()),
     "disasters_main": int(len(DT)), "disasters_mapped": int((DT.town != "").sum()),
     "disasters_term": int((DT.how == "event term is a Hansard town").sum()), "disaster_places": int(DT[DT.town != ""].town.nunique())}
jsave(r, f"{SCR}/r_data.json", indent=1)
print(json.dumps(r, indent=1))
print(DT[["event", "da_term", "town", "km", "how"]].to_string())
