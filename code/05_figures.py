"""Step 5: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf,
vector) and header.png (1200 x 630). Light paper background; red = London and big cities / more attention, blue = towns
and the shock comparison, gold = disasters."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import numpy as np, pandas as pd
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as stransform, unary_union
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
RED, BLUE, GREY, GOLD, GREEN = "#B4442E", "#2F6A9E", "#9C9384", "#C98A2B", "#5E7F4F"
CMAP = LinearSegmentedColormap.from_list("d", [BLUE, "#8FB0CF", "#C9C2B4", "#E3A58F", RED])
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json"); H = R["H"]
AN = pd.read_csv(f"{DATA}/annual.csv")
CT = pd.read_csv(f"{DATA}/concentration.csv")
ES = pd.read_csv(f"{DATA}/event_study.csv")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD):
    os.makedirs(d_, exist_ok=True)
SRC = f"Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0), \"in <place>\" contributions, House of Commons\nmaps.tristanhotham.com/{SLUG}"
DLAB = [f"{d}s" if d < 2020 else "2020 to 25" for d in DECADES]


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.058, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=SRC):
    fig.text(0.04, 0.012, s, fontsize=8.3, family=MONO, color=MUT, va="bottom", linespacing=1.4)


def panel(ax, lab):
    ax.text(-0.01, 1.04, lab, transform=ax.transAxes, fontsize=13, fontweight="bold", color=INK, ha="left", va="bottom")


# ---------- 1. concentration over time
fig = plt.figure(figsize=(12, 9.6))
title(fig, "A century of the Commons: attention spread out from London",
      f"Commons contributions containing \"in <place>\" for {R['data']['n_clean']:,} UK towns and cities, {Y0} to {Y1}; dots are decades with 95% intervals")
axs = [fig.add_axes([0.08, 0.53, 0.38, 0.30]), fig.add_axes([0.58, 0.53, 0.38, 0.30]),
       fig.add_axes([0.08, 0.10, 0.38, 0.30]), fig.add_axes([0.58, 0.10, 0.38, 0.30])]
mid = np.array([d + (4.5 if d < 2020 else 2.5) for d in DECADES])
ax = axs[0]; panel(ax, "A  London's share of all town mentions (%)")
ax.plot(AN.year, AN.london, color=RED, lw=1.0, alpha=0.45)
ax.errorbar(mid, CT.london, yerr=[CT.london - CT.london_lo, CT.london_hi - CT.london], fmt="o", color=RED, ms=5, lw=1.2, capsize=0)
ax.set_ylim(0, 70); ax.axvline(1945, color=MUT, lw=0.8, ls=(0, (3, 2)))
ax.text(1946, 64, "1945", fontsize=9.5, color=MUT)
ax = axs[1]; panel(ax, "B  Gini coefficient over places (1 = all on one place)")
ax.plot(AN.year, AN.gini, color=INK, lw=1.0, alpha=0.4, label="single years (higher: fewer mentions a year)")
ax.errorbar(mid, CT.gini, yerr=[CT.gini - CT.gini_lo, CT.gini_hi - CT.gini], fmt="o", color=INK, ms=5, lw=1.2, capsize=0, label="all places")
ax.errorbar(mid, CT.gini_xl, yerr=[CT.gini_xl - CT.gini_xl_lo, CT.gini_xl_hi - CT.gini_xl], fmt="s", color=GREY, ms=4.5, lw=1.0, capsize=0, label="without London")
ax.legend(frameon=False, fontsize=10, loc="lower left"); ax.set_ylim(0.78, 1.0); ax.axvline(1945, color=MUT, lw=0.8, ls=(0, (3, 2)))
ax = axs[2]; panel(ax, "C  Effective number of places (log scale)")
ax.plot(AN.year, AN.enp, color=BLUE, lw=1.0, alpha=0.45)
ax.errorbar(mid, CT.enp, yerr=[CT.enp - CT.enp_lo, CT.enp_hi - CT.enp], fmt="o", color=BLUE, ms=5, lw=1.2, capsize=0)
ax.set_yscale("log"); ax.set_yticks([2, 5, 10, 20, 50, 100]); ax.set_yticklabels(["2", "5", "10", "20", "50", "100"]); ax.minorticks_off()
ax.axvline(1945, color=MUT, lw=0.8, ls=(0, (3, 2)))
ax.text(1912, 60, "as if attention were shared\nequally by this many places", fontsize=9.5, color=MUT, va="top")
ax = axs[3]; panel(ax, "D  Places mentioned at least once in the year")
ax.plot(AN.year, AN.places_mentioned, color=GREEN, lw=1.6)
ax.set_ylim(0, AN.places_mentioned.max() * 1.1); ax.axvline(1945, color=MUT, lw=0.8, ls=(0, (3, 2)))
for a in axs:
    a.set_xlim(1908, 2027); a.tick_params(labelsize=10)
foot(fig); out(fig, "conc")

# ---------- 2. Lorenz curves
fig = plt.figure(figsize=(8.5, 8))
title(fig, "Fewer places take the lion's share", "Lorenz curves: share of all town mentions held by the least mentioned places", y=0.965)
ax = fig.add_axes([0.13, 0.12, 0.8, 0.7])
q = np.linspace(0, 1, 201)
for d, c, lab in (("1910", RED, "1910s"), ("1950", GOLD, "1950s"), ("2010", BLUE, "2010s")):
    ax.plot(100 * q, 100 * np.array(R["lorenz"][d]), color=c, lw=2.2, label=f"{lab}  (Gini {R['conc'][d]['gini']:.3f})")
ax.plot([0, 100], [0, 100], color=RULE, lw=1); ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.set_xlabel(f"share of the {R['data']['n_clean']:,} places, least mentioned first (%)"); ax.set_ylabel("share of mentions (%)")
ax.legend(frameon=False, loc="upper left", fontsize=11)
foot(fig); out(fig, "lorenz", blog=False)

# ---------- 3. drivers (Shapley)
d = R["drivers"]; BN = ["size", "public interest", "electoral map", "geography", "shocks"]
LAB = {"size": "Size\n(population)", "public interest": "Public interest\n(Wikipedia views)", "electoral map": "Electoral map\n(seat named after it)",
       "geography": "Geography\n(nation, distance\nfrom London)", "shocks": "Shocks\n(by-elections,\ndisasters)"}
fig = plt.figure(figsize=(11, 7.4))
title(fig, "What explains which places the Commons talks about, 2005 to 2025",
      f"Share of the explained variation (Shapley decomposition of a Poisson model), {d['n']:,} places; 95% bootstrap intervals")
ax = fig.add_axes([0.24, 0.12, 0.70, 0.66])
y = np.arange(len(BN))[::-1]
vals = [100 * d["shapley"][b]["b"] / d["total"]["b"] for b in BN]
lo = [100 * d["shapley"][b]["lo"] / d["total"]["b"] for b in BN]; hi = [100 * d["shapley"][b]["hi"] / d["total"]["b"] for b in BN]
cols = [INK, BLUE, RED, GREY, GOLD]
ax.barh(y, vals, color=cols, height=0.6)
ax.errorbar(vals, y, xerr=[np.array(vals) - lo, np.array(hi) - vals], fmt="none", ecolor=MUT, lw=1.2)
for yy, v, h in zip(y, vals, hi):
    ax.text(h + 1.2, yy, f"{v:.0f}%", va="center", fontsize=12, color=INK)
ax.set_yticks(y); ax.set_yticklabels([LAB[b] for b in BN], fontsize=11); ax.set_xlim(0, 55)
ax.set_xlabel(f"% of the explained variation (deviance pseudo R² = {d['total']['b']:.2f})")
foot(fig); out(fig, "drivers")

# ---------- 4. variance decomposition
dc = R["decomp"]
parts = [("place", "The place itself\n(permanent)", INK), ("place_decade", "The place's decade\n(slow rises and falls)", BLUE),
         ("decade", "The decade\n(for every place)", GREY), ("year", "The year", "#C9C2B4"),
         ("other", "Year to year noise\nwithin a decade", "#E3D7BC"), ("shock", "By-elections and\ndisasters", GOLD)]
fig = plt.figure(figsize=(12, 6.6))
title(fig, "Where a place stands is mostly about the place",
      f"Variance of log(1 + yearly mentions), {dc['n_places']:,} places x {dc['n_years']} years ({Y0} to {Y1}), split into parts; 95% bootstrap intervals")
ax = fig.add_axes([0.04, 0.42, 0.92, 0.2])
left = 0
for k, lab, c in parts:
    v = dc[k]["b"]
    ax.barh(0, v, left=left, color=c, height=0.8, edgecolor=PAPER, lw=1.2)
    left += v
ax.set_xlim(0, 100); ax.set_ylim(-0.5, 0.5); ax.axis("off")
xs = [0.04, 0.215, 0.39, 0.53, 0.66, 0.82]
left = 0
for (k, lab, c), xt in zip(parts, xs):
    v = dc[k]["b"]
    val = f"{v:.1f}%" if k not in ("shock",) else f"{v:.2f}%"
    ci = f"[{dc[k]['lo']:.1f} to {dc[k]['hi']:.1f}]" if k != "shock" else f"[{dc[k]['lo']:.2f} to {dc[k]['hi']:.2f}]"
    fig.text(xt + 0.024, 0.405, val, fontsize=17, fontweight="bold", color=c if c not in ("#E3D7BC", "#C9C2B4") else MUT, va="top")
    fig.text(xt, 0.29, lab, fontsize=10.5, color=INK, va="top")
    fig.text(xt, 0.17, ci, fontsize=9, color=MUT, va="top", family=MONO)
    fig.patches.append(matplotlib.patches.Rectangle((xt, 0.375), 0.018, 0.03, transform=fig.transFigure, color=c, ec=MUT, lw=0.4))
    left += v
foot(fig); out(fig, "decomp")

# ---------- 5. persistence
sp = R["spearman"]
fig = plt.figure(figsize=(11, 6.8))
title(fig, "The pecking order hardened after 1945", "Rank correlation (Spearman) of places' mentions between one decade and the next; 95% bootstrap intervals")
ax = fig.add_axes([0.1, 0.14, 0.86, 0.62])
keys = [k for k in sp if int(k.split("_")[1]) - int(k.split("_")[0]) == 10]
xs = np.arange(len(keys))
b = [sp[k]["b"] for k in keys]; lo = [sp[k]["lo"] for k in keys]; hi = [sp[k]["hi"] for k in keys]
ax.errorbar(xs, b, yerr=[np.array(b) - lo, np.array(hi) - b], fmt="o", color=INK, ms=7, lw=1.4)
ax.axhline(0.7, color=RED, lw=0.9, ls=(0, (3, 2))); ax.text(len(keys) - 0.6, 0.71, "0.7: the planned test", color=RED, fontsize=10, ha="right", va="bottom")
ax.set_xticks(xs); ax.set_xticklabels([f"{k.split('_')[0]}s to\n{DLAB[DECADES.index(int(k.split('_')[1]))]}" for k in keys], fontsize=9)
ax.set_ylim(0, 1); ax.set_ylabel("Spearman rank correlation")
ax.text(0, 0.9, f"1910s to 2010s: {sp['1910_2010']['b']:.2f}", fontsize=11.5, color=MUT)
foot(fig); out(fig, "persist")

# ---------- 6. size and seat names by era
e1 = R["E1"]; e2 = R["E2"]
fig = plt.figure(figsize=(12, 6.8))
title(fig, "Size matters less than it did; a seat name matters throughout",
      f"Poisson models of decade mentions, {e1['places']:,} places with a population, 1910s to 2020s; 95% intervals")
ax1 = fig.add_axes([0.08, 0.19, 0.38, 0.55]); ax2 = fig.add_axes([0.58, 0.19, 0.38, 0.55])
EN = ["1910s to\n1940s", "1950s to\n1970s", "1980s to\n2020s"]
b = [e1[f"lpop_{j}"]["b"] for j in range(3)]; lo = [e1[f"lpop_{j}"]["lo"] for j in range(3)]; hi = [e1[f"lpop_{j}"]["hi"] for j in range(3)]
ax1.errorbar(range(3), b, yerr=[np.array(b) - lo, np.array(hi) - b], fmt="o", color=INK, ms=8, lw=1.6)
ax1.axhline(1, color=RULE, lw=1); ax1.set_xticks(range(3)); ax1.set_xticklabels(EN); ax1.set_xlim(-0.5, 2.5); ax1.set_ylim(0.8, 1.8)
panel(ax1, "A  Mentions per 1% more people (elasticity)")
ax1.text(2.45, 1.01, "1 = in proportion to size", fontsize=9.5, color=MUT, ha="right", va="bottom")
b = [e1[f"seat_{j}"]["b"] for j in range(3)]; lo = [e1[f"seat_{j}"]["lo"] for j in range(3)]; hi = [e1[f"seat_{j}"]["hi"] for j in range(3)]
ax2.errorbar(np.arange(3) - 0.1, b, yerr=[np.array(b) - lo, np.array(hi) - b], fmt="o", color=RED, ms=8, lw=1.6, label="between places (same size)")
w = [e2["seat_pre"], e2["seat_post"]]
ax2.errorbar([0.1, 1.6], [x["b"] for x in w], yerr=[[x["b"] - x["lo"] for x in w], [x["hi"] - x["b"] for x in w]], fmt="s", color=BLUE, ms=7, lw=1.4,
             label="within a place (gaining or losing\na seat name; before / after 1945)")
ax2.axhline(0, color=RULE, lw=1); ax2.set_xticks(range(3)); ax2.set_xticklabels(EN); ax2.set_xlim(-0.5, 2.5)
ax2.set_ylabel("% more mentions"); panel(ax2, "B  Premium for a place named in a seat")
ax2.legend(frameon=False, fontsize=9.5, loc="upper right")
foot(fig); out(fig, "seat")

# ---------- 7. shocks: harmonised event study
F1 = R["F"]["F1"]
fig = plt.figure(figsize=(12, 8.4))
title(fig, "By-elections and disasters: one design, two kinds of shock",
      f"Monthly \"in <town>\" mentions against 5 matched towns each (Poisson, town and stack-by-month fixed effects);\n{F1['n']['events_B']} by-elections ({F1['towns_B']} towns) and {F1['n']['events_D']} disasters; month 0 = polling day or the disaster")
ax = fig.add_axes([0.1, 0.14, 0.86, 0.6])
for ty, c, lab in (("by-election", BLUE, "by-elections"), ("disaster", GOLD, "disasters")):
    g = ES[ES.type == ty].sort_values("k")
    ax.fill_between(g.k, 1 + g.lo / 100, 1 + g.hi / 100, color=c, alpha=0.16, lw=0)
    ax.plot(g.k, 1 + g.b / 100, color=c, lw=2, marker="o", ms=3, label=lab)
ax.axvspan(REF[0], REF[1], color=RULE, alpha=0.35, lw=0); ax.text(-18.5, 0.13, "reference\nmonths", ha="center", fontsize=9.5, color=MUT)
ax.axvline(0, color=INK, lw=0.8, ls=(0, (3, 2))); ax.axhline(1, color=MUT, lw=0.8)
ax.set_yscale("log"); ax.set_yticks([0.125, 0.25, 0.5, 1, 2, 4, 8]); ax.set_yticklabels(["1/8", "1/4", "1/2", "no change", "2x", "4x", "8x"]); ax.minorticks_off()
ax.set_ylim(0.1, 16); ax.set_xlim(-24.5, 36.5); ax.set_xticks(range(-24, 37, 6)); ax.set_xlabel("months from the event")
ax.legend(frameon=False, fontsize=12, loc="upper right")
tx = (f"Months 13 to 36: by-elections {F1['lasting__B']['b']:+.0f}% [{F1['lasting__B']['lo']:.0f} to {F1['lasting__B']['hi']:.0f}],\n"
      f"disasters {F1['lasting__D']['b']:+.0f}% [{F1['lasting__D']['lo']:.0f} to {F1['lasting__D']['hi']:.0f}]")
ax.text(35.5, 0.13, tx, ha="right", fontsize=10.5, color=INK)
foot(fig); out(fig, "shocks")

# ---------- 8. map: who gained and lost attention, 1910 to 1944 vs 1980 to 2025
tr = Transformer.from_crs(4326, 27700, always_xy=True)
Cf = jload(f"{GEO}/counties_uk.geojson")["features"]
uk = unary_union([shape(f["geometry"]).buffer(0.002) for f in Cf]).buffer(-0.002).simplify(0.003)
ukp = stransform(lambda a, b, z=None: tr.transform(a, b), uk)
NE = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]
irl = stransform(lambda a, b, z=None: tr.transform(a, b), next(shape(f["geometry"]) for f in NE if f["properties"]["ADM0_A3"] == "IRL"))


def patch(ax, g, **kw):
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.geom_type != "Polygon": continue
        v, c = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = np.asarray(ring.coords); v += cs.tolist(); c += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(v, c), **kw))


def basemap(ax, ext=(-30000, 690000, -10000, 1080000)):
    ax.set_facecolor("#EAF0F2")
    patch(ax, irl, fc="#F2EEE6", ec="#BDB6A8", lw=0.4)
    patch(ax, ukp, fc="#FBF7EE", ec="#8E8576", lw=0.6)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)


PL = pd.read_csv(f"{DATA}/places.csv")
PY = pd.read_csv(f"{DATA}/place_years.csv")
early = PL.term.map(PY[PY.year.between(1910, 1944)].groupby("term").in_mentions.sum()).fillna(0)
late = PL.term.map(PY[PY.year.between(1980, 2025)].groupby("term").in_mentions.sum()).fillna(0)
PL["sh_early"] = early / early.sum(); PL["sh_late"] = late / late.sum()
PL["lr"] = np.log2((PL.sh_late + 2e-5) / (PL.sh_early + 2e-5))
PL["tot"] = PL.in_1910_2025
xy = np.array([tr.transform(lo, la) for la, lo in zip(PL.lat, PL.lon)]); PL["x"], PL["y"] = xy[:, 0], xy[:, 1]
MP = PL[PL.tot >= 20].sort_values("tot", ascending=False)
R_map = {"n_map": int(len(MP)), "n_gain": int((MP.lr > 0).sum()), "n_loss": int((MP.lr < 0).sum())}
fig = plt.figure(figsize=(11, 12.4))
title(fig, "Who gained the Commons' attention, and who lost it",
      f"Share of all town mentions, 1980 to 2025 against 1910 to 1944; {len(MP):,} places with 20 or more mentions", y=0.975)
ax = fig.add_axes([0.02, 0.05, 0.68, 0.82]); basemap(ax)
sc = ax.scatter(MP.x, MP.y, c=MP.lr.clip(-3, 3), cmap=CMAP, norm=TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3), s=6 + 3.2 * np.sqrt(MP.tot),
                lw=0.5, edgecolor="white", zorder=3, alpha=0.95)
cax = fig.add_axes([0.76, 0.52, 0.025, 0.26])
cb = fig.colorbar(sc, cax=cax, ticks=[-3, -2, -1, 0, 1, 2, 3]); cb.outline.set_visible(False)
cb.ax.set_yticklabels(["1/8", "1/4", "1/2", "same", "2x", "4x", "8x"], fontsize=9.5)
fig.text(0.745, 0.80, "Share of mentions,\n1980 to 2025 against\n1910 to 1944", fontsize=10.5, color=INK, va="bottom")
fig.text(0.745, 0.47, f"Dot size: all mentions,\n{Y0} to {Y1}\n\nRed: a bigger share of\nthe Commons' town talk\nthan before 1945.\nBlue: a smaller share.\n\nLondon's share fell from\n{H['london_1910s']:.0f}% (1910s) to {H['london_2010s']:.0f}%\n(2010s)", fontsize=9.8, color=MUT, va="top")
from shapely.geometry import Point
LBL = {"London": (655000, 262000), "Belfast": (150000, 482000), "Glasgow": (60000, 720000), "Cardiff": (205000, 120000), "Liverpool": (262000, 402000)}
for t, (lx, ly) in LBL.items():
    r = PL[PL.term == t].iloc[0]
    assert not ukp.contains(Point(lx, ly)) and not irl.contains(Point(lx, ly)), t      # label anchored on sea
    ax.annotate(t, (r.x, r.y), (lx, ly), fontsize=11, color=INK, path_effects=HALO, ha="center", va="center",
                arrowprops=dict(arrowstyle="-", color=MUT, lw=0.7, shrinkA=6, shrinkB=2), zorder=5)
foot(fig); out(fig, "map")
R2 = jload(f"{DATA}/results.json"); R2["map"] = R_map; jsave(R2, f"{DATA}/results.json", indent=1)

# ---------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.text(0.05, 0.86, "Which places get", fontsize=40, fontweight="bold", family=DISP, color=INK, va="top")
fig.text(0.05, 0.73, "Parliament's attention?", fontsize=40, fontweight="bold", family=DISP, color=INK, va="top")
fig.text(0.05, 0.56, f"A century of the House of Commons\nand the map of the UK, {Y0} to {Y1}", fontsize=17, color=MUT, va="top", linespacing=1.4)
fig.text(0.05, 0.33, f"London's share of town mentions\n{H['london_1910s']:.0f}% in the 1910s, {H['london_2010s']:.0f}% in the 2010s", fontsize=15, color=RED, va="top", linespacing=1.4)
fig.text(0.05, 0.07, "Dr Tristan Hotham · maps.tristanhotham.com", fontsize=12, family=MONO, color=MUT)
ax = fig.add_axes([0.62, 0.03, 0.36, 0.94]); basemap(ax); ax.set_facecolor(PAPER)
ax.scatter(MP.x, MP.y, c=MP.lr.clip(-3, 3), cmap=CMAP, norm=TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3), s=2 + 1.6 * np.sqrt(MP.tot), lw=0.3, edgecolor="white", zorder=3)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER)
plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done", R_map)
