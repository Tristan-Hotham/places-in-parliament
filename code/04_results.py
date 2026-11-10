"""Step 4: data/results.json (every number quoted anywhere) from the step 1 to 3 outputs, plus data/models.csv and a few
descriptive extras for the page, blog and collage. Asserts check the internal consistency of the headline numbers."""
import numpy as np, pandas as pd
from common import *

R = {"data": jload(f"{SCR}/r_data.json")}
R.update(jload(f"{SCR}/r_models.json"))
R["F"] = jload(f"{SCR}/r_events.json")
Z = np.load(f"{SCR}/mats.npz", allow_pickle=False)
A = Z["A"]; TERMS = list(Z["terms"]); YEARS = Z["years"]
AN = pd.read_csv(f"{DATA}/annual.csv")
c = R["conc"]
# headline shortcuts (rounded as quoted)
H = {}
H["london_1910s"] = round(c["1910"]["london"], 1); H["london_2010s"] = round(c["2010"]["london"], 1); H["london_2020s"] = round(c["2020"]["london"], 1)
H["london_1950s"] = round(c["1950"]["london"], 1)
H["gini_1910s"] = round(c["1910"]["gini"], 3); H["gini_2010s"] = round(c["2010"]["gini"], 3); H["gini_2020s"] = round(c["2020"]["gini"], 3)
H["top10_1910s"] = round(c["1910"]["top10"], 1); H["top10_2010s"] = round(c["2010"]["top10"], 1)
H["enp_1910s"] = round(c["1910"]["enp"], 1); H["enp_2010s"] = round(c["2010"]["enp"], 1); H["enp_2020s"] = round(c["2020"]["enp"], 1)
H["hoover_1910s"] = round(c["1910"]["hoover"], 1); H["hoover_2010s"] = round(c["2010"]["hoover"], 1)
H["places_1910s"] = c["1910"]["places_mentioned"]; H["places_2010s"] = c["2010"]["places_mentioned"]
H["gini_drop"] = round(-R["conc_diff_2010_1910"]["gini"]["b"], 3)
H["gini_drop_lo"] = round(-R["conc_diff_2010_1910"]["gini"]["hi"], 3); H["gini_drop_hi"] = round(-R["conc_diff_2010_1910"]["gini"]["lo"], 3)
sg = R["seg"]["gini"]
H["gini_slope_pre"] = round(-sg["pre"]["b"], 4); H["gini_slope_post"] = round(-sg["post"]["b"], 4)
H["gini_slope_ratio"] = round(sg["post"]["b"] / sg["pre"]["b"], 1)
H["places_slope_pre"] = round(R["seg"]["places_mentioned"]["pre"]["b"], 1); H["places_slope_post"] = round(R["seg"]["places_mentioned"]["post"]["b"], 1)
d = R["drivers"]["shapley"]
for k, nm in (("size", "size"), ("public interest", "views"), ("electoral map", "seat"), ("shocks", "shocks"), ("geography", "geo")):
    H[f"shap_{nm}"] = d[k]["share"]
H["pseudo_r2"] = round(R["drivers"]["total"]["b"], 3)
dc = R["decomp"]
for k in ("decade", "year", "place", "place_decade", "within", "shock"):
    H[f"dec_{k}"] = round(dc[k]["b"], 1) if k != "shock" else round(dc[k]["b"], 2)
H["dec_slow"] = round(dc["place"]["b"] + dc["place_decade"]["b"], 1)
H["by_logpts_pc"] = round(100 * (math.exp(dc["beta_by"]["b"]) - 1), 1)
H["di_logpts_pc"] = round(100 * (math.exp(dc["beta_di"]["b"]) - 1), 1)
sp = R["spearman"]
H["sp_1910_1920"] = sp["1910_1920"]["b"]; H["sp_2010_2020"] = sp["2010_2020"]["b"]; H["sp_1910_2010"] = sp["1910_2010"]["b"]
H["sp_min_adjacent"] = min(v["b"] for k, v in sp.items() if int(k.split("_")[1]) - int(k.split("_")[0]) == 10)
H["sp_max_adjacent"] = max(v["b"] for k, v in sp.items() if int(k.split("_")[1]) - int(k.split("_")[0]) == 10)
H["sp_n_below_07"] = sum(1 for k, v in sp.items() if int(k.split("_")[1]) - int(k.split("_")[0]) == 10 and v["b"] < 0.7)
H["ar_rho"] = R["ar1"]["all"]["b"]; H["ar_half"] = R["ar1"]["all"]["half_life"]
F1 = R["F"]["F1"]
H["F_peak_B"] = F1["peak__B"]["b"]; H["F_peak_D"] = F1["peak__D"]["b"]
H["F_x_peak_B"] = round(1 + F1["peak__B"]["b"] / 100, 1); H["F_x_peak_D"] = round(1 + F1["peak__D"]["b"] / 100, 1)
H["F_last_B"] = F1["lasting__B"]["b"]; H["F_last_D"] = F1["lasting__D"]["b"]
R["H"] = H
# descriptive extras: top ten places per decade
top = {}
for dd in DECADES:
    j = (YEARS >= dd) & (YEARS <= min(dd + 9, Y1))
    tot = A[:, j].sum(1); o = np.argsort(-tot)[:10]
    top[dd] = [[TERMS[i], round(float(tot[i]))] for i in o]
R["top_by_decade"] = top
# London's share by year: max and min
R["london_year_max"] = AN.loc[AN.london.idxmax(), ["year", "london"]].round(1).tolist()
R["london_year_min"] = AN.loc[AN.london.idxmin(), ["year", "london"]].round(1).tolist()
R["places_mentioned_1910"] = int(AN.loc[AN.year == 1910, "places_mentioned"].iloc[0]); R["places_mentioned_2025"] = int(AN.loc[AN.year == 2025, "places_mentioned"].iloc[0])
# source study headlines cited (from their published results files, for the synthesis table)
R["sources"] = {
    "hansard_places": {"doi": DOIS["hansard-places"], "places": 1661, "clean": 1597, "elasticity_pop": 1.34},
    "wiki_vs_hansard": {"doi": DOIS["wiki-vs-hansard"], "n": 1425, "views_elasticity": 0.54, "views_lo": 0.46, "views_hi": 0.62, "seat_pc": 121, "seat_lo": 90, "seat_hi": 158},
    "byelection_attention": {"doi": DOIS["byelection-attention"], "byelections": 366, "towns": 387, "result": 296, "result_lo": 196, "result_hi": 429, "year1": 91, "year1_lo": 51, "year1_hi": 143,
                             "year2": 55, "year2_lo": 19, "year2_hi": 101},
    "disaster_attention": {"doi": DOIS["disaster-attention"], "disasters": 64, "month0": 10.4, "month0_lo": 2.4, "month0_hi": 44.9, "half_months": 8.5}}
# consistency checks
assert R["data"]["n_clean"] == R["decomp"]["n_places"] == 1596
assert abs(sum(R["decomp"][k]["b"] for k in ("decade", "year", "place", "place_decade", "within")) - 100) < 0.01
assert c["1910"]["gini"] > c["2010"]["gini"] and c["1910"]["london"] > c["2010"]["london"]
assert R["F"]["flow"]["main"] == F1["n"]["events_D"] and F1["n"]["events_B"] == R["F"]["flow"]["byelections"]
assert abs(sum(R["drivers"]["shapley"][k]["b"] for k in R["drivers"]["shapley"]) - R["drivers"]["total"]["b"]) < 1e-3
jsave(R, f"{DATA}/results.json", indent=1)
M = pd.concat([pd.read_csv(f"{SCR}/models_A_E.csv"), pd.read_csv(f"{SCR}/models_F.csv")], ignore_index=True)
M.to_csv(f"{DATA}/models.csv", index=False)
print(json.dumps(H, indent=0))
