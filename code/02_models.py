"""Step 2: the pre-specified analyses A to E of NOTES.md (concentration, drivers, variance decomposition, persistence,
seat names over a century) with their robustness checks. Outputs: SCR/r_models.json, data/concentration.csv,
data/drivers_shapley.csv, data/models.csv (appended by step 3)."""
import itertools, warnings
import numpy as np, pandas as pd, pyfixest as pf, statsmodels.api as sm
from scipy.stats import spearmanr
from common import *

warnings.filterwarnings("ignore")
Z = np.load(f"{SCR}/mats.npz", allow_pickle=False)
YM, A = Z["YM"], Z["A"]
TERMS = list(Z["terms"]); NATION = Z["nation"]; POP = Z["pop"]; DLON = Z["dlon"]; YEARS = Z["years"]
SEAT, SH_BY, SH_DI = Z["SEAT"], Z["SH_BY"], Z["SH_DI"]
IDX = {t: i for i, t in enumerate(TERMS)}
LON = IDX["London"]
NP_, NY = A.shape
rng = np.random.default_rng(20261110)
R = {}; ROWS = []


def dec_months(d):
    a = mi(f"{d}-01"); b = mi(f"{min(d + 9, Y1)}-12")
    return np.arange(a, b + 1)


def gini(x):
    x = np.sort(x); n = len(x); s = x.sum()
    if s <= 0: return np.nan
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * s))


def measures(tot, pop_mask, popshare, sub=None):
    """tot: totals per place (clean places)."""
    s = tot.sum()
    out = {"gini": gini(tot), "london": 100 * tot[LON] / s, "top10": 100 * np.sort(tot)[-10:].sum() / s,
           "enp": float(s ** 2 / (tot ** 2).sum()), "gini_xl": gini(np.delete(tot, LON))}
    m = tot[pop_mask] / tot[pop_mask].sum()
    out["hoover"] = 100 * 0.5 * np.abs(m - popshare).sum()
    return out


popmask = np.isfinite(POP) & (POP > 0)
popshare = POP[popmask] / POP[popmask].sum()
glon = np.array([km(CHARING[0], CHARING[1], la, lo) <= NEAR_KM for la, lo in zip(Z["lat"], Z["lon"])])


def conc_table(M, nboot=1000, label="main", keep=None):
    """concentration measures per decade with bootstrap over months; M is places x months."""
    rows, boots = [], {}
    for d in DECADES:
        ms = dec_months(d)
        X = M[:, ms]
        tot = X.sum(1)
        pt = measures(tot, popmask, popshare)
        B = []
        for _ in range(nboot):
            b = X[:, rng.integers(0, len(ms), len(ms))].sum(1)
            B.append(measures(b, popmask, popshare))
        B = pd.DataFrame(B); boots[d] = B
        r = {"decade": d, "label": label, "total": float(tot.sum()), "places_mentioned": int((tot > 0).sum())}
        for k in pt:
            # bias-corrected percentile interval: the bootstrap of a Gini over resampled months is biased upward (repeated
            # months leave rarely mentioned places at zero), so the percentiles are shifted by the bootstrap bias
            # (mean of draws minus the estimate). Changed after the first run, when plain percentile intervals missed the estimate.
            bias = float(B[k].mean() - pt[k])
            r[k] = pt[k]; r[k + "_lo"] = float(B[k].quantile(.025) - bias); r[k + "_hi"] = float(B[k].quantile(.975) - bias)
            r[k + "_bias"] = bias
        rows.append(r)
    return pd.DataFrame(rows), boots


CT, CB = conc_table(YM)
R["conc"] = {int(r["decade"]): {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != "label"} for r in CT.to_dict("records")}
diff = {}
for k in ("gini", "london", "top10", "hoover", "gini_xl", "enp"):
    dd = CB[2010][k].values - CB[1910][k].values
    pt_ = float(CT.loc[CT.decade == 2010, k].iloc[0] - CT.loc[CT.decade == 1910, k].iloc[0])
    bi = float(dd.mean() - pt_)
    diff[k] = {"b": round(pt_, 4), "lo": round(float(np.quantile(dd, .025)) - bi, 4), "hi": round(float(np.quantile(dd, .975)) - bi, 4)}
R["conc_diff_2010_1910"] = diff
# post-1945 vs 1910 to 1944 within-era change, and 1950s vs 1930s
for a_, b_ in ((1930, 1950), (1950, 2010)):
    dd = CB[b_]["gini"].values - CB[a_]["gini"].values
    pt_ = float(CT.loc[CT.decade == b_, "gini"].iloc[0] - CT.loc[CT.decade == a_, "gini"].iloc[0])
    bi = float(dd.mean() - pt_)
    R[f"gini_diff_{b_}_{a_}"] = {"b": round(pt_, 4), "lo": round(float(np.quantile(dd, .025)) - bi, 4), "hi": round(float(np.quantile(dd, .975)) - bi, 4)}
# Lorenz curves (for the figure) and annual series
lor = {}
for d in (1910, 1950, 2010):
    tot = np.sort(YM[:, dec_months(d)].sum(1)); c = np.concatenate([[0], np.cumsum(tot) / tot.sum()])
    q = np.linspace(0, 1, 201); lor[d] = np.interp(q, np.linspace(0, 1, len(c)), c).round(5).tolist()
R["lorenz"] = lor
ann = []
for j, y in enumerate(YEARS):
    tot = A[:, j]
    m = measures(tot, popmask, popshare)
    ann.append({"year": int(y), "total": float(tot.sum()), "places_mentioned": int((tot > 0).sum()), **m,
                "seat_share_att": 100 * tot[SEAT[:, j] > 0].sum() / tot.sum()})
AN = pd.DataFrame(ann)
AN.to_csv(f"{DATA}/annual.csv", index=False, float_format="%.4f")
# H2: segmented trend, break at 1945, Newey-West (5 lags)
for k in ("gini", "london", "top10", "places_mentioned"):
    t = AN.year - 1945; post = (AN.year >= 1945).astype(float)
    X = sm.add_constant(np.column_stack([t, t * post, post]))
    f = sm.OLS(AN[k].values, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    pre_s, dif = f.params[1], f.params[2]
    V = f.cov_params()
    post_se = math.sqrt(V[1, 1] + V[2, 2] + 2 * V[1, 2])
    R.setdefault("seg", {})[k] = {"pre": est(10 * pre_s, 10 * f.bse[1], 4), "post": est(10 * (pre_s + dif), 10 * post_se, 4),
                                   "diff": est(10 * dif, 10 * f.bse[2], 4), "jump": est(f.params[3], f.bse[3], 4), "n": int(len(AN))}
# robustness for A
rob = []
alt = {"no prefix subtraction": Z["YM_noprefix"], "no precision scaling": Z["YM_noscale"]}
for lab, M in alt.items():
    T_, B_ = conc_table(M, nboot=200, label=lab)
    rob.append((lab, T_, B_))
for nat in ("England", "Scotland", "Wales", "Northern Ireland"):
    keep = NATION != nat
    M = YM[keep]
    s10 = M[:, dec_months(1910)].sum(1); s20 = M[:, dec_months(2010)].sum(1)
    rob.append((f"without {nat}", pd.DataFrame([{"decade": 1910, "gini": gini(s10)}, {"decade": 2010, "gini": gini(s20)}]), None))
big = popmask & (POP >= 50000)
M = YM[big]
rob.append(("places of 50,000 or more", pd.DataFrame([{"decade": d, "gini": gini(M[:, dec_months(d)].sum(1))} for d in (1910, 2010)]), None))
# Greater London as one unit
Mg = np.vstack([YM[~glon], YM[glon].sum(0, keepdims=True)])
gl = []
for d in DECADES:
    tot = Mg[:, dec_months(d)].sum(1)
    gl.append({"decade": d, "gini": gini(tot), "glondon_share": 100 * tot[-1] / tot.sum()})
GL = pd.DataFrame(gl)
rob.append(("Greater London as one unit", GL, None))
R["glondon"] = {int(r.decade): {"share": round(r.glondon_share, 2), "gini": round(r.gini, 4)} for r in GL.itertuples()}
R["n_glondon_places"] = int(glon.sum())
R["conc_robust"] = [{"label": lab, "gini_1910": round(float(T_.loc[T_.decade == 1910, "gini"].iloc[0]), 4),
                     "gini_2010": round(float(T_.loc[T_.decade == 2010, "gini"].iloc[0]), 4)} for lab, T_, _ in rob]
CT.to_csv(f"{DATA}/concentration.csv", index=False, float_format="%.4f")
print("A done", diff["gini"], R["seg"]["gini"])

# ------------------------------------------------------------------ B. drivers, 2005 to 2025 cross-section
W = pd.read_csv(f"{WVH}/index.csv")
BL = pd.read_csv(f"{DATA}/byelection_links.csv")
DT = pd.read_csv(f"{DATA}/disaster_towns.csv").fillna({"town": ""})
nby = BL[(BL.year >= 2005) & (BL.year <= 2023)].groupby("term").size()
W["byel"] = W.term.map(nby).fillna(0)
W["disaster"] = W.term.isin(set(DT[(DT.year >= 2005) & (DT.town != "")].town)).astype(int)
W["lpop"] = np.log(W.pop_main); W["lviews"] = np.log(W.views)
W["ldist"] = [math.log(1 + km(CHARING[0], CHARING[1], a, b)) for a, b in zip(W.lat, W.lon)]
for n_ in ("Scotland", "Wales", "Northern Ireland"):
    W["nat_" + n_[:2]] = (W.nation == n_).astype(int)
W["lad"] = W.lad_name.fillna(W.term)
BLOCKS = {"size": ["lpop"], "public interest": ["lviews"], "electoral map": ["seat_share"], "shocks": ["byel", "disaster"],
          "geography": ["nat_Sc", "nat_Wa", "nat_No", "ldist"]}
BN = list(BLOCKS)


def dev_r2(df, cols, y="in_05_25"):
    yv = df[y].values
    X = np.ones((len(df), 1)) if not cols else sm.add_constant(df[cols].values.astype(float))
    f = sm.GLM(yv, X, family=sm.families.Poisson()).fit()
    return 1 - f.deviance / f.null_deviance


def shapley(df, y="in_05_25", blocks=BLOCKS):
    names = list(blocks); v = {}
    for r_ in range(len(names) + 1):
        for S in itertools.combinations(names, r_):
            v[frozenset(S)] = dev_r2(df, sum((blocks[b] for b in S), []), y) if S else 0.0
    n = len(names); out = {}
    for b in names:
        s = 0.0
        for r_ in range(n):
            for S in itertools.combinations([x for x in names if x != b], r_):
                w = math.factorial(r_) * math.factorial(n - r_ - 1) / math.factorial(n)
                s += w * (v[frozenset(S) | {b}] - v[frozenset(S)])
        out[b] = s
    out["total"] = v[frozenset(names)]
    out["alone"] = {b: v[frozenset([b])] for b in names}
    return out


def ppml_full(df, cl="lad", y="in_05_25"):
    cols = sum(BLOCKS.values(), [])
    X = sm.add_constant(df[cols].astype(float))
    f = sm.GLM(df[y].values, X, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df[cl])[0]})
    return {c: est(f.params[c], f.bse[c], 4) for c in cols}, f


SH = shapley(W)
bs = []
for b in range(300):
    i = rng.integers(0, len(W), len(W))
    s = shapley(W.iloc[i].reset_index(drop=True))
    bs.append({k: s[k] for k in BN + ["total"]})
BS = pd.DataFrame(bs)
R["drivers"] = {"n": int(len(W)), "lads": int(W.lad.nunique()), "total": {"b": round(SH["total"], 4), "lo": round(BS.total.quantile(.025), 4), "hi": round(BS.total.quantile(.975), 4)},
                "shapley": {b: {"b": round(SH[b], 4), "lo": round(BS[b].quantile(.025), 4), "hi": round(BS[b].quantile(.975), 4),
                                "share": round(100 * SH[b] / SH["total"], 1)} for b in BN},
                "alone": {b: round(SH["alone"][b], 4) for b in BN},
                "byel_places": int((W.byel > 0).sum()), "disaster_places": int(W.disaster.sum())}
co, fB = ppml_full(W)
R["drivers"]["coef"] = co
for c, v in co.items():
    ROWS.append({"model": "B drivers PPML", "term": c, **v, "n": len(W)})
# exp effects for text
R["drivers"]["seat_pc"] = pc(co["seat_share"]["b"], co["seat_share"]["se"])
R["drivers"]["byel_pc"] = pc(co["byel"]["b"], co["byel"]["se"])
R["drivers"]["disaster_pc"] = pc(co["disaster"]["b"], co["disaster"]["se"])
# robustness for B
rb = []
co2, _ = ppml_full(W, cl="term"); rb.append({"label": "SE clustered by place", **{k: co2[k] for k in ("lpop", "lviews", "seat_share", "byel")}})
for lab, sub in (("without London", W[W.term != "London"]), ("places of 50,000 or more", W[W.pop_main >= 50000]),
                 ("England only", W[W.nation == "England"])):
    s = shapley(sub.reset_index(drop=True), blocks={k: [c for c in v if sub[c].std() > 0] for k, v in BLOCKS.items()})
    rb.append({"label": lab, "n": int(len(sub)), "shapley": {b: round(s[b], 4) for b in BN}, "total": round(s["total"], 4)})
W["ly"] = np.log1p(W.in_05_25)
Xo = sm.add_constant(W[sum(BLOCKS.values(), [])].astype(float))
fo = sm.OLS(W.ly, Xo).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(W.lad)[0]})
r2 = {}
names = BN
vv = {}
for r_ in range(len(names) + 1):
    for S in itertools.combinations(names, r_):
        cols = sum((BLOCKS[b] for b in S), [])
        vv[frozenset(S)] = sm.OLS(W.ly, sm.add_constant(W[cols].astype(float))).fit().rsquared if cols else 0.0
for b in names:
    s = 0.0
    for r_ in range(len(names)):
        for S in itertools.combinations([x for x in names if x != b], r_):
            w = math.factorial(r_) * math.factorial(len(names) - r_ - 1) / math.factorial(len(names))
            s += w * (vv[frozenset(S) | {b}] - vv[frozenset(S)])
    r2[b] = round(s, 4)
rb.append({"label": "OLS on log(1 + mentions), R2 Shapley", "shapley": r2, "total": round(vv[frozenset(names)], 4)})
R["drivers_robust"] = rb
pd.DataFrame([{"block": b, **R["drivers"]["shapley"][b], "alone": R["drivers"]["alone"][b]} for b in BN]).to_csv(f"{DATA}/drivers_shapley.csv", index=False)
print("B done", R["drivers"]["shapley"], R["drivers"]["total"])

# ------------------------------------------------------------------ C. variance decomposition of the place-year panel
DEC_OF = np.array([min(y // 10 * 10, 2020) for y in YEARS])
DLIST = sorted(set(DEC_OF))


def decompose(Y, S_list):
    """balanced nested ANOVA: decade, year within decade, place, place x decade, remainder; remainder split by shocks."""
    m = Y.mean()
    yt = Y.mean(0)                                   # year means
    yi = Y.mean(1)                                   # place means
    yd = np.array([yt[DEC_OF == d].mean() for d in DLIST])
    ydt = yd[np.searchsorted(DLIST, DEC_OF)]
    yid = np.column_stack([Y[:, DEC_OF == d].mean(1) for d in DLIST])
    yidt = yid[:, np.searchsorted(DLIST, DEC_OF)]
    N, T = Y.shape
    tot = ((Y - m) ** 2).sum()
    ss = {"decade": N * ((ydt - m) ** 2).sum(), "year": N * ((yt - ydt) ** 2).sum(), "place": T * ((yi - m) ** 2).sum(),
          "place_decade": ((yidt - yi[:, None] - ydt[None, :] + m) ** 2).sum()}
    r = Y - yidt - yt[None, :] + ydt[None, :]
    ss["within"] = (r ** 2).sum()
    Xs = []
    for S in S_list:
        S = S.astype(float)
        sd = np.column_stack([S[:, DEC_OF == d].mean(1) for d in DLIST])[:, np.searchsorted(DLIST, DEC_OF)]
        Xs.append((S - sd - S.mean(0)[None, :] + np.array([S.mean(0)[DEC_OF == d].mean() for d in DLIST])[np.searchsorted(DLIST, DEC_OF)][None, :]).ravel())
    X = np.column_stack(Xs); rv = r.ravel()
    beta, *_ = np.linalg.lstsq(X, rv, rcond=None)
    ss["shock"] = float(((X @ beta) ** 2).sum())
    ss["other"] = ss["within"] - ss["shock"]
    out = {k: 100 * v / tot for k, v in ss.items()}
    out["beta"] = beta.tolist()
    assert abs(sum(out[k] for k in ("decade", "year", "place", "place_decade", "within")) - 100) < 1e-6
    return out


Ylog = np.log1p(A)
DC = decompose(Ylog, [SH_BY, SH_DI])
DCb = decompose(Ylog, [SH_BY]); DCd = decompose(Ylog, [SH_DI])
bs = []
for b in range(500):
    i = rng.integers(0, NP_, NP_)
    d_ = decompose(Ylog[i], [SH_BY[i], SH_DI[i]])
    bs.append({k: d_[k] for k in ("decade", "year", "place", "place_decade", "within", "shock", "other")} | {"b_by": d_["beta"][0], "b_di": d_["beta"][1]})
BS = pd.DataFrame(bs)
R["decomp"] = {k: {"b": round(DC[k], 3), "lo": round(BS[k].quantile(.025), 3), "hi": round(BS[k].quantile(.975), 3)} for k in ("decade", "year", "place", "place_decade", "within", "shock", "other")}
R["decomp"]["shock_by_only"] = round(DCb["shock"], 3); R["decomp"]["shock_di_only"] = round(DCd["shock"], 3)
R["decomp"]["n_places"] = NP_; R["decomp"]["n_years"] = NY; R["decomp"]["n_rows"] = int(NP_ * NY)
# shock effects in log points (cluster bootstrap over places)
for j, k in enumerate(("by", "di")):
    b = DC["beta"][j]; lo, hi = BS[f"b_{k}"].quantile(.025), BS[f"b_{k}"].quantile(.975)
    R["decomp"][f"beta_{k}"] = {"b": round(b, 3), "lo": round(lo, 3), "hi": round(hi, 3)}
R["decomp"]["shock_place_years"] = {"byelection": int(SH_BY.sum()), "disaster": int(SH_DI.sum())}
# placebo: shocks moved to random years within place (circular shift), 200 permutations
pl = []
for b in range(200):
    sh = rng.integers(1, NY, NP_)
    Sb = np.vstack([np.roll(SH_BY[i], sh[i]) for i in range(NP_)]); Sd = np.vstack([np.roll(SH_DI[i], sh[i]) for i in range(NP_)])
    pl.append(decompose(Ylog, [Sb, Sd])["shock"])
R["decomp"]["placebo_shock"] = {"mean": round(float(np.mean(pl)), 4), "p95": round(float(np.quantile(pl, .95)), 4),
                                "p": round(float((np.array(pl) >= DC["shock"]).mean()), 4)}
# robustness for C
tot_t = A.sum(0)
cr = []
for lab, Yalt, sl in (("share of the year's total, log(1 + 10,000 x share)", np.log1p(1e4 * A / tot_t[None, :]), None),
                      ("no prefix subtraction", np.log1p(Z["A_np"]), None), ("no precision scaling", np.log1p(Z["A_ns"]), None),
                      ("without London", np.delete(Ylog, LON, 0), np.arange(NP_) != LON),
                      ("places of 50,000 or more", Ylog[big], big),
                      ("places with 100 or more mentions", Ylog[A.sum(1) >= 100], A.sum(1) >= 100)):
    m_ = sl if sl is not None else np.ones(NP_, bool)
    d_ = decompose(Yalt, [SH_BY[m_], SH_DI[m_]])
    cr.append({"label": lab, "n_places": int(m_.sum()), **{k: round(d_[k], 2) for k in ("decade", "year", "place", "place_decade", "within", "shock")}})
keepY = YEARS <= 2019
DEC_SAVE = DEC_OF.copy()
DEC_OF = DEC_OF[keepY]; DLIST = sorted(set(DEC_OF))
d_ = decompose(Ylog[:, keepY], [SH_BY[:, keepY], SH_DI[:, keepY]])
cr.append({"label": "1910 to 2019 (drop the partial 2020s)", "n_places": NP_, **{k: round(d_[k], 2) for k in ("decade", "year", "place", "place_decade", "within", "shock")}})
DEC_OF = DEC_SAVE; DLIST = sorted(set(DEC_OF))
R["decomp_robust"] = cr
print("C done", R["decomp"])

# ------------------------------------------------------------------ D. persistence
DT_ = np.column_stack([A[:, DEC_OF == d].sum(1) / (DEC_OF == d).sum() for d in DLIST])     # mean per year per decade
sp = {}
for a_, b_ in list(zip(DLIST[:-1], DLIST[1:])) + [(1910, 2010), (1950, 2010)]:
    ia, ib = DLIST.index(a_), DLIST.index(b_)
    m_ = (DT_[:, ia] > 0) | (DT_[:, ib] > 0)
    x, y = DT_[m_, ia], DT_[m_, ib]
    rho = spearmanr(x, y).correlation
    B = []
    for _ in range(500):
        i = rng.integers(0, m_.sum(), m_.sum()); B.append(spearmanr(x[i], y[i]).correlation)
    sp[f"{a_}_{b_}"] = {"b": round(rho, 3), "lo": round(float(np.quantile(B, .025)), 3), "hi": round(float(np.quantile(B, .975)), 3), "n": int(m_.sum())}
R["spearman"] = sp
zz = np.log((A + 0.5) / tot_t[None, :])
pan = pd.DataFrame({"place": np.repeat(np.arange(NP_), NY), "year": np.tile(YEARS, NP_), "z": zz.ravel()})
pan["zl"] = pan.groupby("place").z.shift(1)
pan["era"] = pan.year.map(era_of)
pan["tot"] = np.repeat(A.sum(1), NY)
pan = pan.dropna()
ar = {}
for lab, sub in (("all", pan), ("100 or more mentions", pan[pan.tot >= 100])):
    f = pf.feols("z ~ zl | place + year", data=sub, vcov={"CRV1": "place"})
    rho, se = f.coef()["zl"], f.se()["zl"]
    ar[lab] = {**est(rho, se, 4), "half_life": round(math.log(2) / -math.log(rho), 2), "n": int(f._N), "places": int(sub.place.nunique())}
for a_, b_, n_ in ERAS:
    sub = pan[pan.era == n_]
    f = pf.feols("z ~ zl | place + year", data=sub, vcov={"CRV1": "place"})
    rho, se = f.coef()["zl"], f.se()["zl"]
    ar[n_] = {**est(rho, se, 4), "half_life": round(math.log(2) / -math.log(rho), 2), "n": int(f._N)}
R["ar1"] = ar
print("D done", sp["1910_2010"], ar["all"])

# ------------------------------------------------------------------ E. seat names over a century
rows = []
for i in range(NP_):
    if not popmask[i]:
        continue
    for d in DLIST:
        m_ = DEC_OF == d
        rows.append({"place": TERMS[i], "decade": d, "y": A[i, m_].sum(), "seat": (SEAT[i, m_] > 0).mean(), "nation": NATION[i],
                     "lpop": math.log(POP[i]), "post45": int(d >= 1950), "era": era_of(d if d != 1940 else 1940)})
PD = pd.DataFrame(rows)
PD["era"] = np.where(PD.decade < 1950, "1910s to 1940s", np.where(PD.decade < 1980, "1950s to 1970s", "1980s to 2020s"))
EN = ["1910s to 1940s", "1950s to 1970s", "1980s to 2020s"]
PD = PD.sort_values(["place", "decade"])
PD["seat_lead"] = PD.groupby("place").seat.shift(-1)
for j, e in enumerate(EN):
    PD[f"lpop_{j}"] = PD.lpop * (PD.era == e); PD[f"seat_{j}"] = PD.seat * (PD.era == e)
PD["seat_post"] = PD.seat * PD.post45
PD["dec"] = PD.decade.astype(str)
E1 = pf.fepois("y ~ lpop_0 + lpop_1 + lpop_2 + seat_0 + seat_1 + seat_2 + C(nation) | dec", data=PD, vcov={"CRV1": "place"})
co, se = E1.coef(), E1.se()
R["E1"] = {"n": int(E1._N), "places": int(PD.place.nunique()),
           **{f"lpop_{j}": est(co[f"lpop_{j}"], se[f"lpop_{j}"], 3) for j in range(3)},
           **{f"seat_{j}": pc(co[f"seat_{j}"], se[f"seat_{j}"]) for j in range(3)}}
# contrast size elasticity post-1945 vs before
V = E1._vcov; nm = list(co.index)
for a_, b_ in ((0, 1), (0, 2)):
    ia, ib = nm.index(f"lpop_{a_}"), nm.index(f"lpop_{b_}")
    d_ = co.iloc[ib] - co.iloc[ia]; s_ = math.sqrt(V[ia, ia] + V[ib, ib] - 2 * V[ia, ib])
    R["E1"][f"lpop_diff_{b_}_{a_}"] = est(d_, s_, 3)
    ia, ib = nm.index(f"seat_{a_}"), nm.index(f"seat_{b_}")
    d_ = co.iloc[ib] - co.iloc[ia]; s_ = math.sqrt(V[ia, ia] + V[ib, ib] - 2 * V[ia, ib])
    R["E1"][f"seat_diff_{b_}_{a_}"] = pc(d_, s_)
for c in co.index:
    ROWS.append({"model": "E1 decades PPML", "term": c, **est(co[c], se[c], 4), "n": int(E1._N)})
E2 = pf.fepois("y ~ seat + seat_post | place + dec", data=PD, vcov={"CRV1": "place"})
co, se = E2.coef(), E2.se()
V = E2._vcov
R["E2"] = {"n": int(E2._N), "places": int(PD[PD.groupby("place").y.transform("sum") > 0].place.nunique()),
           "seat_pre": pc(co["seat"], se["seat"]), "seat_post_diff": pc(co["seat_post"], se["seat_post"]),
           "seat_post": pc(co["seat"] + co["seat_post"], math.sqrt(V[0, 0] + V[1, 1] + 2 * V[0, 1])),
           "switchers": int((PD.groupby("place").seat.agg(lambda s: s.max() > s.min())).sum())}
for c in co.index:
    ROWS.append({"model": "E2 within-place PPML", "term": c, **est(co[c], se[c], 4), "n": int(E2._N)})
sub = PD.dropna(subset=["seat_lead"])
E3 = pf.fepois("y ~ seat + seat_lead | place + dec", data=sub, vcov={"CRV1": "place"})
R["E2"]["lead"] = {"seat": pc(E3.coef()["seat"], E3.se()["seat"]), "lead": pc(E3.coef()["seat_lead"], E3.se()["seat_lead"]), "n": int(E3._N)}
# E pooled within-place premium, and robustness
E4 = pf.fepois("y ~ seat | place + dec", data=PD, vcov={"CRV1": "place"})
R["E2"]["pooled"] = pc(E4.coef()["seat"], E4.se()["seat"])
er = []
for lab, sub in (("1910s to 2010s (drop the partial 2020s)", PD[PD.decade < 2020]), ("places of 50,000 or more", PD[np.exp(PD.lpop) >= 50000]),
                 ("without London", PD[PD.place != "London"]), ("England only", PD[PD.nation == "England"])):
    f = pf.fepois("y ~ seat + seat_post | place + dec", data=sub, vcov={"CRV1": "place"})
    c_, s_ = f.coef(), f.se(); V_ = f._vcov
    er.append({"label": lab, "n": int(f._N), "seat_pre": pc(c_["seat"], s_["seat"]), "seat_post_diff": pc(c_["seat_post"], s_["seat_post"]),
               "seat_post": pc(c_["seat"] + c_["seat_post"], math.sqrt(V_[0, 0] + V_[1, 1] + 2 * V_[0, 1]))})
PD["ly"] = np.log1p(PD.y)
f = pf.feols("ly ~ seat + seat_post | place + dec", data=PD, vcov={"CRV1": "place"})
c_, s_ = f.coef(), f.se(); V_ = f._vcov
er.append({"label": "OLS on log(1 + mentions)", "n": int(f._N), "seat_pre": pc(c_["seat"], s_["seat"]), "seat_post_diff": pc(c_["seat_post"], s_["seat_post"]),
           "seat_post": pc(c_["seat"] + c_["seat_post"], math.sqrt(V_[0, 0] + V_[1, 1] + 2 * V_[0, 1]))})
R["E_robust"] = er
# descriptive: share of attention to places named in a seat, by decade
R["seat_share_att"] = {int(d): round(float(AN[(AN.year // 10 * 10).clip(upper=2020) == d].seat_share_att.mean()), 2) for d in DLIST}
R["seat_places_by_decade"] = {int(d): int((SEAT[:, DEC_OF == d].max(1) > 0).sum()) for d in DLIST}
print("E done", R["E1"], R["E2"])
jsave(R, f"{SCR}/r_models.json", indent=1)
pd.DataFrame(ROWS).to_csv(f"{SCR}/models_A_E.csv", index=False)
