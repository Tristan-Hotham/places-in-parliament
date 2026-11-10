"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, adds the tables and compiles with xelatex.
Output: release/paper/Hotham_Places_in_Parliament.pdf and .tex beside the f_*.pdf figures. The DOI is printed as the
placeholder https://doi.org/10.5281/zenodo.24103127 unless the env var DOI is set: DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Places_in_Parliament"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
M = lambda s: s.replace("-", "$-$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    for k in ("f0", "f1", "f2", "f3", "f4"):
        if f == k: return M(nz(float(v), int(k[1])))
    return tex(str(v))


def nz(x, d):
    """Format x to d decimals, adding a decimal when a negative value would print as -0."""
    s = f"{x:.{d}f}"
    while s.startswith("-") and float(s) == 0 and d < 3:
        d += 1; s = f"{x:.{d}f}"
    return s


def pc(v, d=0):
    return M(f"{nz(v['b'], d)} [{nz(v['lo'], d)}, {nz(v['hi'], d)}]") if v else ""


def ci(v, d=0):
    return M(f"[{nz(v['lo'], d)}, {nz(v['hi'], d)}]") if v else ""


def tab(caption, label, spec, head, rows, size="\\small", sep=None, fit=False):
    s = f"\\begin{{table}}[tbp]\\centering{size}\\caption{{{caption}}}\\label{{{label}}}"
    if sep: s += f"\\setlength{{\\tabcolsep}}{{{sep}}}"
    body = f"\\begin{{tabular}}{{{spec}}}\\toprule {head}\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}"
    if fit: body = "\\resizebox{\\textwidth}{!}{" + body + "}"
    return s + body + "\\end{table}"


S = R["sources"]
rows = (f"Mentioned in the House \\citep{{hotham2026a}} & Which places does the Commons mention? & 1,661 place terms, 1909 to 2025 & Mentions grow faster than population (elasticity {S['hansard_places']['elasticity_pop']}); London's share falling\\\\\n"
        f"Who gets talked about \\citep{{hotham2026b}} & Public vs Commons attention & {S['wiki_vs_hansard']['n']:,} places, 2005 to 2025 & Pageview elasticity {S['wiki_vs_hansard']['views_elasticity']} [{S['wiki_vs_hansard']['views_lo']}, {S['wiki_vs_hansard']['views_hi']}]; seat-name places +{S['wiki_vs_hansard']['seat_pc']}\\% [{S['wiki_vs_hansard']['seat_lo']}, {S['wiki_vs_hansard']['seat_hi']}]\\\\\n"
        f"Do by-elections make Parliament listen? \\citep{{hotham2026c}} & Attention after a by-election & {S['byelection_attention']['byelections']} by-elections, {S['byelection_attention']['towns']} towns & +{S['byelection_attention']['result']}\\% at the result, +{S['byelection_attention']['year1']}\\% months 3 to 12, +{S['byelection_attention']['year2']}\\% months 13 to 24\\\\\n"
        f"Does Parliament notice disasters, and whose? \\citep{{hotham2026d}} & Attention after a disaster & {S['disaster_attention']['disasters']} disasters (main) & {S['disaster_attention']['month0']} times in the month; half the excess within {S['disaster_attention']['half_months']} months (median)\\\\\n"
        f"This paper & What decides a place's share, and how has it changed? & {R['data']['n_clean']:,} places, monthly, 1910 to 2025 & Concentration, drivers, variance decomposition, persistence, seat names over a century, harmonised shocks\\\\\n")
T_SRC = tab("The four earlier studies and this synthesis.", "tab:sources", "p{3.3cm}p{3.0cm}p{2.8cm}p{5.2cm}", "Study & Question & Data & Main result", rows, size="\\footnotesize")

CT = pd.read_csv(f"{DATA}/concentration.csv")
rows = ""
for r in CT.itertuples():
    lab = f"{r.decade}s" if r.decade < 2020 else "2020 to 2025"
    rows += (f"{lab} & {r.total:,.0f} & {r.places_mentioned:,} & {r.london:.1f} [{r.london_lo:.1f}, {r.london_hi:.1f}] & {r.top10:.1f} & "
             f"{r.gini:.3f} [{r.gini_lo:.3f}, {r.gini_hi:.3f}] & {r.gini_xl:.3f} & {r.enp:.1f} & {r.hoover:.1f}\\\\\n")
d = R["conc_diff_2010_1910"]
rows += (f"\\midrule 2010s minus 1910s & & & {pc(d['london'], 1)} & {pc(d['top10'], 1)} & {pc(d['gini'], 3)} & {pc(d['gini_xl'], 3)} & {pc(d['enp'], 1)} & {pc(d['hoover'], 1)}\\\\\n")
T_CONC = tab("Concentration of Commons place mentions by decade. Mentions: total ``in <place>'' contributions; places: places mentioned at least once; London and top ten: shares (\\%); Gini over all {:,} places (with and without London); ENP: effective number of places; Hoover: dissimilarity between mention and population shares (\\%). 95\\% bias-corrected bootstrap intervals (1,000 draws of months).".format(R["data"]["n_clean"]),
             "tab:conc", "lrrlrlrrr", "Decade & Mentions & Places & London (\\%) & Top 10 & Gini & Gini excl. & ENP & Hoover", rows, size="\\scriptsize", sep="3pt", fit=True)

rows = ""
for k, lab, dd in (("gini", "Gini", 4), ("london", "London share (points)", 2), ("top10", "Top ten share (points)", 2), ("places_mentioned", "Places mentioned in the year", 1)):
    x = R["seg"][k]
    rows += f"{lab} & {pc(x['pre'], dd)} & {pc(x['post'], dd)} & {pc(x['diff'], dd)} & {pc(x['jump'], dd)}\\\\\n"
T_SEG = tab(f"Segmented trends on the annual series, {Y0} to {Y1} ($N$ = {R['seg']['gini']['n']} years): change per decade before and after 1945, their difference, and the level shift at 1945; OLS with Newey and West errors (5 lags), 95\\% CI.",
            "tab:seg", "lllll", "Measure & Before 1945 & From 1945 & Difference & Shift at 1945", rows, size="\\footnotesize", sep="4pt", fit=True)

dr = R["drivers"]; co = dr["coef"]
lab = {"lpop": "log population", "lviews": "log pageviews (2024)", "seat_share": "seat-name share", "byel": "by-elections (count)", "disaster": "disaster (any)",
       "nat_Sc": "Scotland", "nat_Wa": "Wales", "nat_No": "Northern Ireland", "ldist": "log distance from London"}
rows = "\\multicolumn{5}{l}{\\textit{A. PPML coefficients (errors clustered by local authority)}}\\\\\n"
for k, v in co.items():
    rows += f"\\quad {lab[k]} & {M(f'{v['b']:.3f}')} & ({v['se']:.3f}) & {M(f'[{v['lo']:.3f}, {v['hi']:.3f}]')} & {v['p']:.3f}\\\\\n"
rows += f"\\midrule\\multicolumn{{5}}{{l}}{{\\textit{{B. Shapley shares of the deviance pseudo-$R^2$ ({dr['total']['b']:.3f}; 95\\% bootstrap interval {dr['total']['lo']:.3f} to {dr['total']['hi']:.3f})}}}}\\\\\n"
for b in ("size", "public interest", "electoral map", "geography", "shocks"):
    v = dr["shapley"][b]
    rr = [x for x in R["drivers_robust"] if "shapley" in x]
    rows += f"\\quad {b} & {v['b']:.3f} & & [{v['lo']:.3f}, {v['hi']:.3f}] & {v['share']:.1f}\\%\\\\\n"
rows += "\\midrule\\multicolumn{5}{l}{\\textit{C. Shapley values in checks: " + "; ".join(
    f"{x['label']} (N = {x.get('n', dr['n']):,}): " + ", ".join(f"{b} {x['shapley'][b]:.3f}" for b in ("size", "public interest", "electoral map", "geography", "shocks")) + f", total {x['total']:.3f}"
    for x in R["drivers_robust"] if "shapley" in x).replace("_", " ") + "}}\\\\\n"
T_DRV = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{" + f"What explains place mentions, 2005 to 2025: PPML of ``in'' mentions for {dr['n']:,} places ({dr['lads']} local authority clusters)." + "}\\label{tab:drivers}"
         "\\begin{tabular}{p{6.2cm}rrlr}\\toprule Term & $b$ & (SE) & 95\\% CI & $p$ or share\\\\\\midrule\n" + rows.replace("\\multicolumn{5}{l}{\\textit{C.", "\\multicolumn{5}{p{14cm}}{\\textit{C.") + "\\bottomrule\\end{tabular}\\end{table}")

dc = R["decomp"]
parts = [("place", "Place (permanent)"), ("place_decade", "Place by decade (slow change)"), ("decade", "Decade (common)"), ("year", "Year within decade (common)"),
         ("within", "Within place and decade"), ("shock", "\\quad of which by-elections and disasters")]
rows = "".join(f"{lab_} & {dc[k]['b']:.{2 if k == 'shock' else 1}f} & [{dc[k]['lo']:.{2 if k == 'shock' else 1}f}, {dc[k]['hi']:.{2 if k == 'shock' else 1}f}] & "
               + " & ".join(f"{x[k]:.{2 if k == 'shock' else 1}f}" for x in R["decomp_robust"]) + "\\\\\n" for k, lab_ in parts)
rows += "\\midrule Places & " + f"{dc['n_places']:,} & & " + " & ".join(f"{x['n_places']:,}" for x in R["decomp_robust"]) + "\\\\\n"
heads = ["Share", "Bootstrap", "Shares", "No prefix", "No scaling", "No London", "50,000+", "100+ ment.", "To 2019"]
T_DEC = tab(f"Variance decomposition of $\\log(1+\\text{{mentions}})$ on the balanced place-year panel ({dc['n_rows']:,} place-years), \\% of total; 95\\% intervals from 500 bootstrap draws of places. Checks: outcome as share of the year's total; no prefix subtraction; no precision scaling; without London; places of 50,000 or more; places with 100 or more mentions; 1910 to 2019. Shock effects: by-election years {dc['beta_by']['b']:.3f} log points [{dc['beta_by']['lo']:.3f}, {dc['beta_by']['hi']:.3f}], disaster years {dc['beta_di']['b']:.3f} [{dc['beta_di']['lo']:.3f}, {dc['beta_di']['hi']:.3f}]. Placebo (shock years moved at random, 200 draws): mean {dc['placebo_shock']['mean']:.4f}\\%.",
            "tab:decomp", "lrlrrrrrrr", "Part & " + " & ".join(heads[:2]) + " & " + " & ".join(heads[2:]), rows, size="\\scriptsize", sep="3pt", fit=True)

sp = R["spearman"]
rows = ""
for k, v in sp.items():
    a, b = k.split("_")
    rows += f"{a}s to {b if b != '2020' else '2020 to 25'}{'s' if b != '2020' else ''} & {v['b']:.3f} & [{v['lo']:.3f}, {v['hi']:.3f}] & {v['n']:,}\\\\\n"
rows += "\\midrule \\multicolumn{4}{l}{\\textit{Annual AR(1) of log share, place and year fixed effects}}\\\\\n"
for k, v in R["ar1"].items():
    rows += f"\\quad {k} & {v['b']:.3f} & [{v['lo']:.3f}, {v['hi']:.3f}] & {v['n']:,} (half-life {v['half_life']:.2f} y)\\\\\n"
T_PER = tab("Persistence: Spearman rank correlations of places' mean yearly mentions between decades (places mentioned in either; 500 bootstrap draws of places), and annual AR(1) coefficients (errors clustered by place).",
            "tab:persist", "lrll", "Comparison & Estimate & 95\\% CI & $N$", rows, size="\\footnotesize")

e1, e2 = R["E1"], R["E2"]
EN = ["1910 to 1949", "1950 to 1979", "1980 to 2025"]
rows = "\\multicolumn{3}{l}{\\textit{E1: between places (decade and nation fixed effects)}}\\\\\n"
for j in range(3):
    rows += f"\\quad log population, {EN[j]} & {M(f'{e1[f'lpop_{j}']['b']:.3f}')} & {ci(e1[f'lpop_{j}'], 3)}\\\\\n"
for j in range(3):
    rows += f"\\quad seat name, {EN[j]} (\\%) & {e1[f'seat_{j}']['b']:.0f} & {ci(e1[f'seat_{j}'])}\\\\\n"
rows += f"\\quad size elasticity, 1980 to 2025 minus 1910 to 1949 & {M(f'{e1['lpop_diff_2_0']['b']:.3f}')} & {ci(e1['lpop_diff_2_0'], 3)}\\\\\n"
rows += f"\\quad seat premium, 1980 to 2025 relative to 1910 to 1949 (\\%) & {M(f'{e1['seat_diff_2_0']['b']:.0f}')} & {ci(e1['seat_diff_2_0'])}\\\\\n"
rows += f"\\quad $N$ (place-decades / places) & \\multicolumn{{2}}{{l}}{{{e1['n']:,} / {e1['places']:,}}}\\\\\n"
rows += "\\midrule\\multicolumn{3}{l}{\\textit{E2: within places (place and decade fixed effects)}}\\\\\n"
rows += f"\\quad seat name, before 1945 (\\%) & {M(f'{e2['seat_pre']['b']:.0f}')} & {ci(e2['seat_pre'])}\\\\\n"
rows += f"\\quad seat name, from 1945 (\\%) & {e2['seat_post']['b']:.0f} & {ci(e2['seat_post'])}\\\\\n"
rows += f"\\quad difference (\\%) & {e2['seat_post_diff']['b']:.0f} & {ci(e2['seat_post_diff'])}\\\\\n"
rows += f"\\quad pooled (\\%) & {e2['pooled']['b']:.0f} & {ci(e2['pooled'])}\\\\\n"
rows += f"\\quad lead placebo: seat name now / next decade (\\%) & {e2['lead']['seat']['b']:.0f} / {e2['lead']['lead']['b']:.0f} & {ci(e2['lead']['seat'])} / {ci(e2['lead']['lead'])}\\\\\n"
rows += f"\\quad $N$ (place-decades / places with mentions / switchers) & \\multicolumn{{2}}{{l}}{{{e2['n']:,} / {e2['places']:,} / {e2['switchers']}}}\\\\\n"
T_SEAT = tab("Seat names and size over a century: PPML of decade mentions, errors clustered by place. Seat name: share of the decade's years in which the place's name was part of a seat name; percentages are $100(e^b-1)$ for a whole decade named.",
             "tab:seat", "p{8.4cm}ll", "Term & Estimate & 95\\% CI", rows, size="\\footnotesize")

F1 = R["F"]["F1"]; fl = R["F"]["flow"]
lab = {"pre": "Months $-12$ to $-4$", "runup": "Months $-3$ to $-1$", "peak": "Months 0 to 2 (peak)", "year1": "Months 3 to 12", "lasting": "Months 13 to 36 (lasting)"}
rows = "".join(f"{lab[b]} & {pc(F1[b + '__B'])} & {pc(F1[b + '__D'])} & {pc(F1['contrast'][b])}\\\\\n" for b in ("pre", "runup", "peak", "year1", "lasting"))
rows += f"\\midrule Share of the peak left in months 13 to 36 (\\%) & {pc(F1['retained']['B'])} & {pc(F1['retained']['D'])} & \\\\\n"
rows += f"Events (clusters) & {F1['n']['events_B']} & {F1['n']['events_D']} & \\\\\n"
rows += f"Treated towns & {F1['towns_B']} & {F1['towns_D']} & \\\\\n"
rows += f"Mean mentions a month, treated: reference / peak / lasting & {F1['mean_ref_B']:.2f} / {F1['mean_peak_B']:.2f} / {F1['mean_lasting_B']:.2f} & {F1['mean_ref_D']:.2f} / {F1['mean_peak_D']:.2f} / {F1['mean_lasting_D']:.2f} & \\\\\n"
rows += f"Town-months used / in panel & \\multicolumn{{3}}{{l}}{{{F1['n']['rows']:,} / {F1['panel_rows']:,} ({F1['control_places']} distinct control towns)}}\\\\\n"
T_SH = tab(f"Harmonised event study (joint PPML with type-specific bins): percentage change against matched towns, 95\\% CI; contrast = disasters relative to by-elections. Disasters: {fl['disasters']} in the list, less {fl['no_town']} with no Hansard town within 10 km, {fl['outside_window']} outside the data window and {fl['byel_in_window']} with a by-election naming the town in the window.",
           "tab:shocks", "p{5.2cm}lll", "Period & By-elections & Disasters & Contrast", rows, size="\\footnotesize")

rows = "".join(f"{tex(x['label'])} & {x['gini_1910']:.3f} & {x['gini_2010']:.3f}\\\\\n" for x in R["conc_robust"])
T_CR = tab("Robustness of the fall in concentration: Gini coefficient over places in the 1910s and 2010s.", "tab:concrob", "lrr", "Check & 1910s & 2010s",
           f"Main & {R['conc']['1910']['gini']:.3f} & {R['conc']['2010']['gini']:.3f}\\\\\n" + rows, size="\\footnotesize")
rows = "".join(f"{tex(x['label'])} & {x['n']:,} & {pc(x['seat_pre'])} & {pc(x['seat_post'])} & {pc(x['seat_post_diff'])}\\\\\n" for x in R["E_robust"])
T_SR = tab("Robustness of the within-place seat-name premium (E2): \\% change, 95\\% CI.", "tab:seatrob", "lrlll", "Check & $N$ & Before 1945 & From 1945 & Difference",
           f"Main & {e2['n']:,} & {pc(e2['seat_pre'])} & {pc(e2['seat_post'])} & {pc(e2['seat_post_diff'])}\\\\\n" + rows, size="\\footnotesize", sep="4pt")
sub = R["F"]["subtypes"]
rows = "".join(f"{lab[b]} & " + " & ".join(pc(sub[t][b]) for t in ("B changed", "B held", "D 50+", "D under 50")) + "\\\\\n" for b in ("pre", "runup", "peak", "year1", "lasting"))
rows += "Events & " + " & ".join(str(sub[t]["events"]) for t in ("B changed", "B held", "D 50+", "D under 50")) + "\\\\\n"
T_SUB = tab("Exploratory sub-types in the harmonised design: \\% change against matched towns, 95\\% CI.", "tab:sub", "p{3.2cm}llll",
            "Period & By-el.: changed hands & By-el.: held & Disasters: 50+ deaths & Disasters: under 50", rows, size="\\scriptsize", sep="3pt")
rows = ""; grp = None
for x in R["F"]["robust"]:
    if x["group"] != grp:
        rows += f"\\multicolumn{{8}}{{l}}{{\\textit{{{tex(x['group'])}}}}}\\\\\n"; grp = x["group"]
    rows += f"\\quad {tex(x['label'])} & {x['rows']:,} & " + " & ".join(pc(x.get(f"{b}_{t}")) for t in ("B", "D") for b in ("peak", "year1", "lasting")) + "\\\\\n"
T_SR2 = tab("Robustness of the harmonised event study: \\% change against matched towns (95\\% CI) for by-elections (B) and disasters (D). The placebo is estimated over months $-24$ to $+12$ around the false date, so it has no months 13 to 36. The OLS row is on $\\log(1+y)$, a different scale.",
            "tab:shockrob", "p{4.4cm}rllllll", "Check & Rows & B 0 to 2 & B 3 to 12 & B 13 to 36 & D 0 to 2 & D 3 to 12 & D 13 to 36",
            f"Main (F1) & {F1['n']['rows']:,} & " + " & ".join(pc(F1[f"{b}__{t}"]) for t in ("B", "D") for b in ("peak", "year1", "lasting")) + "\\\\\n" + rows, size="\\scriptsize", sep="2pt", fit=True)
T_SR2 = T_SR2.replace("\\begin{table}[tbp]", "\\begin{table}[p]")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_SOURCES", T_SRC), ("TABLE_CONC", T_CONC), ("TABLE_SEG", T_SEG), ("TABLE_DRIVERS", T_DRV), ("TABLE_DECOMP", T_DEC), ("TABLE_PERSIST", T_PER),
             ("TABLE_SEAT", T_SEAT), ("TABLE_SHOCKS", T_SH), ("TABLE_CONCROB", T_CR), ("TABLE_SEATROB", T_SR), ("TABLE_SUB", T_SUB), ("TABLE_SHOCKROB", T_SR2)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("DOIURLTOKEN", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
for bad in ("DSIT", "DCMS", "pre-registered", "preregistered"):
    assert bad not in t, bad
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:20])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
ab = txt.split("Abstract")[1].split("Keywords")[0]
cites = set(re.findall(r"\\cite[pt]?\{([^}]+)\}", t)); cites = {c.strip() for x in cites for c in x.split(",")}
bibs = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", t))
print("uncited:", bibs - cites, "missing:", cites - bibs, "refs", len(bibs))
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;",
      [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))
