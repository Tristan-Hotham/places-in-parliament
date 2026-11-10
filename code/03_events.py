"""Step 3: analysis F of NOTES.md. One harmonised stacked event study for two kinds of shock, by-elections and
disasters, on the same outcome ("in <town>" contributions), with the same window, bins, matched-control rule,
fixed effects and clustering. Outputs: data/shock_events.csv (every event with its exclusion flags),
data/event_study.csv (monthly estimates by type), SCR/r_events.json, SCR/models_F.csv."""
import collections, warnings
import numpy as np, pandas as pd, pyfixest as pf
from common import *

warnings.filterwarnings("ignore")
Z = np.load(f"{SCR}/mats.npz", allow_pickle=False)
YM = Z["YM"]; TERMS = list(Z["terms"]); IDX = {t: i for i, t in enumerate(TERMS)}
NATION = Z["nation"]; POP = Z["pop"]; LAT = Z["lat"]; LON = Z["lon"]
YNS = Z["YM_noscale"]
P = pd.read_csv(f"{DATA}/places.csv").set_index("term")
BL = pd.read_csv(f"{DATA}/byelection_links.csv")
BE = pd.read_csv(f"{BA}/data/event_places.csv")
DT = pd.read_csv(f"{DATA}/disaster_towns.csv").fillna({"town": ""})
rng = np.random.default_rng(7)
R = {}; ROWS = []
csum = np.concatenate([np.zeros((len(TERMS), 1)), np.cumsum(YM, axis=1)], axis=1)


def ref_mean(i, k0):
    a, b = k0 + REF[0], k0 + REF[1]
    return (csum[i, b + 1] - csum[i, a]) / (b - a + 1)


# months with a shock at each town (for exclusions and control eligibility): every by-election link and every mapped disaster
shock_months = collections.defaultdict(list)
for r in BL.itertuples():
    shock_months[r.term].append(mi(r.date[:7]))
for r in DT[DT.town != ""].itertuples():
    shock_months[r.town].append(mi(r.date[:7]))

# ---------------------------------------------------------------- the two event lists
by = BE[(BE.main == 1)][["id", "term", "date", "changed", "cause_group", "era", "nation"]].copy()
by["type"] = "by-election"; by["k0"] = by.date.str[:7].map(mi); by["deaths"] = np.nan
by["eid"] = "B:" + by.id
dis = DT.copy()
dis["k0"] = dis.date.str[:7].map(mi)
dis["window_ok"] = ((dis.k0 - PRE >= 0) & (dis.k0 + POST <= EVLAST)).astype(int)
dis["mapped"] = (dis.town != "").astype(int)
dis["byel_in_window"] = [int(any(k - PRE <= mi(d[:7]) <= k + POST for d in BL[BL.term == t].date)) if t else 0 for t, k in zip(dis.town, dis.k0)]
dis["ref_mean"] = [ref_mean(IDX[t], k) if t and k + REF[0] >= 0 else np.nan for t, k in zip(dis.town, dis.k0)]
dis["city"] = (dis.ref_mean >= CITY_REF).astype(int)
# two disasters at one town with overlapping windows: keep the one with more deaths
dis["dup"] = 0
for t, g in dis[dis.town != ""].groupby("town"):
    g = g.sort_values("deaths", ascending=False)
    kept = []
    for r in g.itertuples():
        if any(abs(r.k0 - k) <= PRE + POST for k in kept):
            dis.loc[r.Index, "dup"] = 1
        else:
            kept.append(r.k0)
dis["main"] = ((dis.mapped == 1) & (dis.window_ok == 1) & (dis.byel_in_window == 0) & (dis.city == 0) & (dis.dup == 0)).astype(int)
dis["type"] = "disaster"; dis["term"] = dis.town; dis["eid"] = "D:" + dis.id
dis.to_csv(f"{DATA}/shock_events.csv", index=False)
flow = {"disasters": int(len(dis)), "no_town": int((dis.mapped == 0).sum()), "outside_window": int(((dis.mapped == 1) & (dis.window_ok == 0)).sum())}
s = dis[(dis.mapped == 1) & (dis.window_ok == 1)]
flow["byel_in_window"] = int(s.byel_in_window.sum()); s = s[s.byel_in_window == 0]
flow["city"] = int(s.city.sum()); s = s[s.city == 0]
flow["dup"] = int(s.dup.sum()); s = s[s.dup == 0]
flow["main"] = int(len(s)); flow["main_term"] = int((s.how == "event term is a Hansard town").sum())
flow["byelections"] = int(by.id.nunique()); flow["byelection_towns"] = int(len(by))
R["flow"] = flow
DM = dis[dis.main == 1].copy()
EV = pd.concat([by[["eid", "term", "k0", "type", "changed", "cause_group", "deaths", "nation"]],
                DM[["eid", "term", "k0", "type", "deaths", "nation", "how", "typegrp"]]], ignore_index=True)

# ---------------------------------------------------------------- controls and stacks
POOL = np.arange(len(TERMS))
lpop = np.log(np.where(np.isfinite(POP) & (POP > 0), POP, np.nan)); lpop_med = np.nanmedian(lpop); lpop = np.where(np.isfinite(lpop), lpop, lpop_med)


def dist_km(la, lo):
    p1 = np.radians(la); p2 = np.radians(LAT)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(LON - lo) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def pick(rows_, k0, K):
    lo, hi = k0 - PRE, k0 + POST
    elig = np.array([not any(lo - 12 <= m <= hi + 12 for m in shock_months.get(t, [])) for t in TERMS])
    for r in rows_:
        elig &= dist_km(LAT[IDX[r["term"]]], LON[IDX[r["term"]]]) > NEAR_KM
        elig[IDX[r["term"]]] = False
    a, b = k0 + REF[0], k0 + REF[1]
    bm = np.log1p((csum[:, b + 1] - csum[:, a]) / (b - a + 1))
    out, taken = {}, set()
    for r in rows_:
        i = IDX[r["term"]]
        ok = elig & (NATION == NATION[i])
        if ok.sum() < 3 * K:
            ok = elig.copy()
        d = np.sqrt(((bm - bm[i]) / 0.5) ** 2 + ((lpop - lpop[i]) / 1.0) ** 2)
        d[~ok] = np.inf
        for t in taken: d[t] = np.inf
        ch = [j for j in np.argsort(d)[:K] if np.isfinite(d[j])]
        taken.update(ch); out[r["term"]] = ch
    return out


def stack(ev, K=K_CONTROLS, shift=0, Ymat=YM):
    rows = []
    for eid, g in ev.groupby("eid"):
        k0 = int(g.k0.iloc[0]) + shift
        if k0 - PRE < 0 or k0 + POST > EVLAST:
            continue
        rr = g.to_dict("records")
        ctl = pick(rr, k0, K)
        for r in rr:
            for role, j in [(1, IDX[r["term"]])] + [(0, c) for c in ctl[r["term"]]]:
                ys = Ymat[j, k0 - PRE:k0 + POST + 1]
                for q, yv in enumerate(ys):
                    rows.append((eid, r["type"], r["term"], TERMS[j], role, -PRE + q, k0 - PRE + q, yv))
    D = pd.DataFrame(rows, columns=["eid", "type", "tterm", "place", "treated", "k", "t", "y"])
    D["unit"] = D.eid + "|" + D.tterm + "|" + D.place
    D["st"] = D.eid + "|" + D.t.astype(str)
    D["town_cl"] = D.tterm
    return D


TB = [(-12, -4), (-3, -1), (0, 2), (3, 12), (13, 36)]
TBN = ["pre", "runup", "peak", "year1", "lasting"]


def bins(D, types=("by-election", "disaster"), B=TB, N=TBN, by=None):
    cols = []
    for ty in types:
        g = D.type == ty
        for (a, b), n in zip(B, N):
            c = f"{n}__{'B' if ty == 'by-election' else 'D'}"
            D[c] = ((D.treated == 1) & g & D.k.between(a, b)).astype(int); cols.append(c)
    return cols


def fit(D, cols, label, cl="eid", ols=False):
    D = D.copy(); D["cl"] = D[cl]
    if ols:
        D["ly"] = np.log1p(D.y); f = pf.feols("ly ~ " + "+".join(cols) + " | unit + st", data=D, vcov={"CRV1": "cl"})
    else:
        f = pf.fepois("y ~ " + "+".join(cols) + " | unit + st", data=D, vcov={"CRV1": "cl"})
    co, se = f.coef(), f.se()
    out = {c: pc(co[c], se[c]) for c in cols if c in co.index}
    n = {"rows": int(f._N), "events": int(D.eid.nunique()), "clusters": int(D.cl.nunique()),
         "events_B": int(D[D.type == "by-election"].eid.nunique()), "events_D": int(D[D.type == "disaster"].eid.nunique())}
    for c in cols:
        if c in co.index:
            ROWS.append({"model": label, "term": c, **out[c], **n})
    return out, n, f


def contrast(f, a, b):
    co = f.coef(); V = pd.DataFrame(f._vcov, index=co.index, columns=co.index)
    d = co[a] - co[b]; s = math.sqrt(V.loc[a, a] + V.loc[b, b] - 2 * V.loc[a, b])
    return pc(d, s)


def retained(f, typ, draws=4000):
    """share of the peak rise still present in months 13 to 36: (exp(b_lasting)-1)/(exp(b_peak)-1), simulated."""
    co = f.coef(); V = pd.DataFrame(f._vcov, index=co.index, columns=co.index)
    a, b = f"lasting__{typ}", f"peak__{typ}"
    m = co[[a, b]].values; S = V.loc[[a, b], [a, b]].values
    x = rng.multivariate_normal(m, S, draws)
    r = (np.exp(x[:, 0]) - 1) / (np.exp(x[:, 1]) - 1)
    pt = (math.exp(m[0]) - 1) / (math.exp(m[1]) - 1)
    return {"b": round(100 * pt, 1), "lo": round(100 * float(np.quantile(r, .025)), 1), "hi": round(100 * float(np.quantile(r, .975)), 1)}


D = stack(EV)
D.to_pickle(f"{SCR}/panel_F.pkl")
cols = bins(D)
M, n, fM = fit(D, cols, "F1 joint")
R["F1"] = {"n": n, **M}
R["F1"]["contrast"] = {b: contrast(fM, f"{b}__D", f"{b}__B") for b in TBN}
R["F1"]["retained"] = {"B": retained(fM, "B"), "D": retained(fM, "D")}
R["F1"]["panel_rows"] = int(len(D)); R["F1"]["control_places"] = int(D[D.treated == 0].place.nunique())
# absolute scale: mean monthly mentions per treated town, reference months and peak months
for ty, c in (("by-election", "B"), ("disaster", "D")):
    g = D[(D.type == ty) & (D.treated == 1)]
    R["F1"][f"mean_ref_{c}"] = round(float(g[g.k.between(*REF)].y.mean()), 3)
    R["F1"][f"mean_peak_{c}"] = round(float(g[g.k.between(0, 2)].y.mean()), 3)
    R["F1"][f"mean_lasting_{c}"] = round(float(g[g.k.between(13, 36)].y.mean()), 3)
    R["F1"][f"towns_{c}"] = int(g.tterm.nunique())
print("F1", json.dumps({k: (v["b"], v["lo"], v["hi"]) for k, v in M.items()}), R["F1"]["contrast"]["lasting"], R["F1"]["retained"])
# monthly event study by type
es = []
for ty, c in (("by-election", "B"), ("disaster", "D")):
    mcols = []
    for k in range(-PRE, POST + 1):
        if REF[0] <= k <= REF[1]:
            continue
        nm = f"m{k + 100}__{c}"
        D[nm] = ((D.treated == 1) & (D.type == ty) & (D.k == k)).astype(int); mcols.append(nm)
    sub = D[D.type == ty]
    f = pf.fepois("y ~ " + "+".join(mcols) + " | unit + st", data=sub, vcov={"CRV1": "eid"})
    co, se = f.coef(), f.se()
    for nm in mcols:
        if nm in co.index:
            k = int(nm[1:].split("__")[0]) - 100
            es.append({"type": ty, "k": k, **pc(co[nm], se[nm])})
    D.drop(columns=mcols, inplace=True)
pd.DataFrame(es).to_csv(f"{DATA}/event_study.csv", index=False)

# ---------------------------------------------------------------- robustness and placebos
rob = []


def rrow(label, group, out, n):
    rob.append({"label": label, "group": group, "rows": n["rows"], "events_B": n["events_B"], "events_D": n["events_D"],
                **{f"{b}_{t}": out.get(f"{b}__{t}") for b in ("peak", "year1", "lasting") for t in ("B", "D")}})


Dp = stack(EV, shift=-24); Dp = Dp[Dp.k <= 12].copy(); cp = bins(Dp)   # months -24 to +12 around the false date (the real event is at +24)
o, n_, _ = fit(Dp, cp, "P1 dates 24 months earlier"); R["P1"] = {"n": n_, **o}; rrow("Dates moved 24 months earlier (placebo)", "Placebo", o, n_)
o, n_, _ = fit(D, cols, "R cluster town", cl="town_cl"); rrow("Standard errors clustered by town", "Inference", o, n_)
D10 = stack(EV, K=10); c10 = bins(D10)
o, n_, _ = fit(D10, c10, "R 10 controls"); rrow("Ten controls per town", "Specification", o, n_)
o, n_, _ = fit(D, cols, "R OLS", ols=True); rrow("OLS on log(1 + mentions)", "Specification", o, n_)
Dns = stack(EV, Ymat=YNS); cns = bins(Dns)
o, n_, _ = fit(Dns, cns, "R no scaling"); rrow("No precision scaling", "Measurement", o, n_)
sub = D[(D.type == "by-election") | D.eid.isin(DM[DM.how == "event term is a Hansard town"].eid)].copy()
o, n_, _ = fit(sub, cols, "R disaster term towns only"); rrow("Disasters named by their own town only", "Sample", o, n_)
DMn = EV[(EV.type == "by-election") | EV.eid.isin(DM[DM.km <= 5].eid)]
sub = D[D.eid.isin(DMn.eid)].copy()
o, n_, _ = fit(sub, cols, "R disaster town within 5 km"); rrow("Disaster town within 5 km", "Sample", o, n_)
for era_lab, a_, b_ in (("1911 to 1944", 1911, 1944), ("1945 to 1979", 1945, 1979), ("1980 to 2023", 1980, 2023)):
    ids = EV[[(a_ <= M0 + k // 12 <= b_) for k in EV.k0]].eid
    sub = D[~D.eid.isin(ids)].copy()
    o, n_, _ = fit(sub, cols, f"R without {era_lab}"); rrow(f"Without {era_lab}", "Leave one era out", o, n_)
for nat in ("England", "Scotland", "Wales", "Northern Ireland"):
    sub = D[~D.eid.isin(EV[EV.nation == nat].eid)].copy()
    if sub[sub.type == "disaster"].eid.nunique() == 0:
        continue
    o, n_, _ = fit(sub, cols, f"R without {nat}"); rrow(f"Without {nat}", "Leave one nation out", o, n_)
R["robust"] = rob
# exploratory sub-types
sub = D.copy()
chg = set(EV[(EV.type == "by-election") & (EV.changed == 1)].eid); big = set(EV[(EV.type == "disaster") & (EV.deaths >= 50)].eid)
sub["type"] = np.where(sub.type == "by-election", np.where(sub.eid.isin(chg), "B changed", "B held"), np.where(sub.eid.isin(big), "D 50+", "D under 50"))
cs = []
for ty in ("B changed", "B held", "D 50+", "D under 50"):
    for (a, b), nme in zip(TB, TBN):
        c = f"{nme}__{ty.replace(' ', '_').replace('+', 'p')}"
        sub[c] = ((sub.treated == 1) & (sub.type == ty) & sub.k.between(a, b)).astype(int); cs.append(c)
fS = pf.fepois("y ~ " + "+".join(cs) + " | unit + st", data=sub, vcov={"CRV1": "eid"})
co, se = fS.coef(), fS.se()
R["subtypes"] = {ty: {nme: pc(co[f"{nme}__{ty.replace(' ', '_').replace('+', 'p')}"], se[f"{nme}__{ty.replace(' ', '_').replace('+', 'p')}"]) for nme in TBN}
                 | {"events": int(sub[sub.type == ty].eid.nunique())} for ty in ("B changed", "B held", "D 50+", "D under 50")}
for ty in ("B changed", "B held", "D 50+", "D under 50"):
    for nme in TBN:
        c = f"{nme}__{ty.replace(' ', '_').replace('+', 'p')}"
        ROWS.append({"model": "F2 sub-types (exploratory)", "term": c, **pc(co[c], se[c]), "rows": int(fS._N)})
# events per town (for the map and page): treated peak and lasting excess against own controls
ex = []
for (eid, tt), g in D.groupby(["eid", "tterm"]):
    tr = g[g.treated == 1]; ct = g[g.treated == 0]
    def m(x, a, b): return float(x[x.k.between(a, b)].y.mean())
    nctl = max(ct.place.nunique(), 1)
    ex.append({"eid": eid, "term": tt, "type": g.type.iloc[0], "ref": m(tr, *REF), "peak": m(tr, 0, 2), "lasting": m(tr, 13, 36),
               "ctl_ref": m(ct, *REF), "ctl_peak": m(ct, 0, 2), "ctl_lasting": m(ct, 13, 36)})
pd.DataFrame(ex).to_csv(f"{SCR}/event_excess.csv", index=False)
jsave(R, f"{SCR}/r_events.json", indent=1)
pd.DataFrame(ROWS).to_csv(f"{SCR}/models_F.csv", index=False)
print(json.dumps(R["flow"]), json.dumps(R["subtypes"])[:1500])
for r in rob:
    print(r["label"], {k: (v["b"], v["lo"], v["hi"]) for k, v in r.items() if isinstance(v, dict)})
