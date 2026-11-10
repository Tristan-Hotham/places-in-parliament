"""Reddit collage (r/dataisbeautiful style), light background, 2700 x 2025 px: the map of who gained and lost a share of
Commons town mentions, London's falling share since 1910, the effective number of places, and the variance split.
Run after code/05_figures.py:  python3 reddit/collage.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "code"))
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
from shapely.geometry import shape, Point
from shapely.ops import transform as stransform, unary_union
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
plt.rcParams.update({"font.family": "Source Serif 4", "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#6E604E", "xtick.color": "#6E604E", "ytick.color": "#6E604E"})
PAPER, INK, MUT, RED, BLUE, GREY, GOLD, SEA = "#FAF6EC", "#2B2119", "#6E604E", "#B4442E", "#2F6A9E", "#9C9384", "#C98A2B", "#EAF0F2"
CMAP = LinearSegmentedColormap.from_list("d", [BLUE, "#8FB0CF", "#C9C2B4", "#E3A58F", RED])
HALO = [pe.withStroke(linewidth=4, foreground=SEA)]
HALOP = [pe.withStroke(linewidth=4, foreground=PAPER)]
R = jload(f"{DATA}/results.json"); H = R["H"]; dc = R["decomp"]
AN = pd.read_csv(f"{DATA}/annual.csv"); CT = pd.read_csv(f"{DATA}/concentration.csv")
PL = pd.read_csv(f"{DATA}/places.csv"); PY = pd.read_csv(f"{DATA}/place_years.csv")
early = PL.term.map(PY[PY.year.between(1910, 1944)].groupby("term").in_mentions.sum()).fillna(0)
late = PL.term.map(PY[PY.year.between(1980, 2025)].groupby("term").in_mentions.sum()).fillna(0)
PL["lr"] = np.log2((late / late.sum() + 2e-5) / (early / early.sum() + 2e-5)); PL["tot"] = PL.in_1910_2025
tr = Transformer.from_crs(4326, 27700, always_xy=True)
xy = np.array([tr.transform(lo, la) for la, lo in zip(PL.lat, PL.lon)]); PL["x"], PL["y"] = xy[:, 0], xy[:, 1]
MP = PL[PL.tot >= 20].sort_values("tot", ascending=False)
assert len(MP) == R["map"]["n_map"]
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


fig = plt.figure(figsize=(13.5, 10.125), dpi=200)
fig.patch.set_facecolor(PAPER)
fig.text(0.03, 0.962, "Which places does Parliament talk about?", family=DISP, fontsize=31, fontweight="bold", color=INK, va="top")
fig.text(0.03, 0.905, f"House of Commons speeches saying \"in <place>\" for {R['data']['n_clean']:,} UK towns and cities, {Y0} to {Y1}", fontsize=14, color=MUT, va="top")
# map
ax = fig.add_axes([0.01, 0.125, 0.47, 0.695]); ax.set_facecolor(SEA)
patch(ax, irl, fc="#F2EEE6", ec="#BDB6A8", lw=0.4); patch(ax, ukp, fc="#FFFDF7", ec="#8E8576", lw=0.6)
ext = (-60000, 690000, -10000, 1000000)
ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.scatter(MP.x, MP.y, c=MP.lr.clip(-3, 3), cmap=CMAP, norm=TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3), s=5 + 2.6 * np.sqrt(MP.tot), lw=0.4, edgecolor="white", zorder=3)
LBL = {"London": (650000, 95000), "Glasgow": (40000, 760000), "Belfast": (250000, 560000), "Liverpool": (215000, 430000), "Jarrow": (560000, 640000)}
LBLA = []
from shapely.geometry import box as _box, LineString as _LS
fig.canvas.draw()
_rend = fig.canvas.get_renderer()
_inv = ax.transData.inverted()
def _ok(an, lines):
    bb = matplotlib.text.Text.get_window_extent(an, _rend); (x0, y0), (x1, y1) = _inv.transform([(bb.x0 - 4, bb.y0 - 4), (bb.x1 + 4, bb.y1 + 4)])
    B = _box(x0, y0, x1, y1)
    if B.intersects(ukp) or B.intersects(irl): return False
    if ((MP.x.between(x0, x1)) & (MP.y.between(y0, y1))).any(): return False
    if any(B.intersects(o) for o in lines): return False
    return True
placed = []  # (box-able annotation, leader line)
for t, (lx, ly) in LBL.items():
    r = PL[PL.term == t].iloc[0]
    cands = [(lx, ly)] + [(r.x + d * np.cos(a_), r.y + d * np.sin(a_)) for d in range(60000, 260000, 15000) for a_ in np.linspace(0, 2 * np.pi, 24, endpoint=False)]
    for cx, cy in cands:
        an = ax.annotate(t, (r.x, r.y), (cx, cy), fontsize=12, color=INK, path_effects=HALO, ha="center", va="center",
                         arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8, shrinkA=8, shrinkB=2), zorder=5)
        L = _LS([(r.x, r.y), (cx, cy)])
        if ext[0] < cx < ext[1] and ext[2] < cy < ext[3] and _ok(an, [l for _, l in placed]) and not any(L.crosses(l) for _, l in placed):
            placed.append((an, L)); print("label", t, int(cx), int(cy)); break
        an.remove()
    else:
        raise SystemExit(f"no sea spot for {t}")
fig.text(0.03, 0.855, "Who gained the Commons' attention?", fontsize=14, fontweight="bold", color=INK)
fig.text(0.03, 0.83, f"Share of all town mentions, 1980 to 2025 vs 1910 to 1944 ({R['map']['n_map']} places with 20+ mentions)", fontsize=10.5, color=MUT)
# colour legend on the sea (bottom left)
cax = fig.add_axes([0.035, 0.07, 0.17, 0.016])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3), cmap=CMAP), cax=cax, orientation="horizontal", ticks=[-3, -2, -1, 0, 1, 2, 3])
cb.outline.set_visible(False); cb.ax.set_xticklabels(["1/8", "1/4", "1/2", "same", "2x", "4x", "8x"], fontsize=9.5)
fig.text(0.035, 0.093, "Red: bigger share now. Blue: smaller share.", fontsize=10.5, color=INK)
fig.text(0.25, 0.093, "Dot size: all mentions, 1910 to 2025", fontsize=10.5, color=INK)
sax = fig.add_axes([0.25, 0.045, 0.22, 0.045]); sax.axis("off"); sax.set_xlim(0, 1); sax.set_ylim(0, 1)
for j, n in enumerate((100, 1000, 10000)):
    sax.scatter([0.08 + j * 0.33], [0.6], s=5 + 2.6 * np.sqrt(n), color="#C9C2B4", lw=0.4, edgecolor="white", clip_on=False)
    sax.text(0.08 + j * 0.33 + 0.07, 0.6, f"{n:,}", fontsize=9.5, color=MUT, va="center")
# right: London share
a1 = fig.add_axes([0.56, 0.56, 0.4, 0.27]); a1.set_facecolor(PAPER)
a1.plot(AN.year, AN.london, color=RED, lw=1.2, alpha=0.5)
mid = np.array([d + (4.5 if d < 2020 else 2.5) for d in DECADES])
a1.plot(mid, CT.london, "o-", color=RED, ms=5, lw=2)
a1.set_ylim(0, 65); a1.set_xlim(1908, 2027); a1.tick_params(labelsize=11)
a1.set_yticks([0, 20, 40, 60]); a1.set_yticklabels(["0%", "20%", "40%", "60%"])
fig.text(0.55, 0.855, "London's share of all Commons town mentions", fontsize=14, fontweight="bold", color=INK)
a1.text(1913, 57, f"1910s: {H['london_1910s']:.0f}%", fontsize=13, color=RED, fontweight="bold", path_effects=HALOP)
a1.text(2024, 34, f"2010s: {H['london_2010s']:.0f}%", fontsize=13, color=RED, fontweight="bold", ha="right", path_effects=HALOP)
a1.text(1960, 52, "line: each year; dots: decades", fontsize=10, color=MUT)
# right middle: effective number of places
fig.text(0.55, 0.47, "As if attention were shared equally by", fontsize=14, fontweight="bold", color=INK)
fig.text(0.55, 0.445, f"{H['enp_1910s']:.0f} places", family=DISP, fontsize=34, fontweight="bold", color=RED, va="top")
fig.text(0.55, 0.385, "in the 1910s", fontsize=12.5, color=INK, va="top")
fig.text(0.78, 0.445, f"{H['enp_2010s']:.0f} places", family=DISP, fontsize=34, fontweight="bold", color=BLUE, va="top")
fig.text(0.78, 0.385, "in the 2010s", fontsize=12.5, color=INK, va="top")
# right bottom: variance split
fig.text(0.55, 0.32, "But where a place stands is mostly about the place", fontsize=14, fontweight="bold", color=INK)
fig.text(0.55, 0.293, f"Variation in yearly mentions, {dc['n_places']:,} places x {dc['n_years']} years", fontsize=11, color=MUT)
a3 = fig.add_axes([0.55, 0.215, 0.41, 0.055]); a3.axis("off")
parts = [("place", "the place itself", INK), ("place_decade", "slow change", BLUE), ("decade", "decade", GREY), ("year", "", "#E3D7BC"), ("other", "yearly noise", "#E3D7BC"), ("shock", "", GOLD)]
left = 0
for k, lab, c in parts:
    v = dc[k]["b"]; a3.barh(0, v, left=left, color=c, edgecolor=PAPER, lw=1); left += v
a3.set_xlim(0, 100)
legend = [(f"{dc['place']['b']:.0f}%", "the place itself (permanent)", INK), (f"{dc['place_decade']['b']:.0f}%", "the place's slow rise or fall", BLUE),
          (f"{dc['decade']['b']:.0f}%", "the decade (every place)", GREY), (f"{dc['other']['b'] + dc['year']['b']:.0f}%", "year to year noise", "#E3D7BC"),
          (f"{dc['shock']['b']:.2f}%", "by-elections and disasters", GOLD)]
for j, (v, lab, c) in enumerate(legend):
    xx = 0.55 + (j % 3) * 0.145; yy = 0.185 - (j // 3) * 0.05
    fig.patches.append(matplotlib.patches.Rectangle((xx, yy - 0.012), 0.012, 0.016, transform=fig.transFigure, color=c))
    fig.text(xx + 0.017, yy, v, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(xx + 0.017, yy - 0.021, lab, fontsize=10, color=MUT, va="top")
fig.text(0.03, 0.022, f"Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); four earlier studies.  maps.tristanhotham.com/{SLUG}  Dr Tristan Hotham",
         fontsize=9.5, family="IBM Plex Mono", color=MUT)
out = os.path.join(HERE, "places_in_parliament_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER)
print(out, Image.open(out).size)
