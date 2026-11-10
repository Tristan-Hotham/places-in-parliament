"""Shared paths, constants and helpers for the places-in-parliament study ("Which places get Parliament's attention?").

Inputs (read in place, never modified):
  RAW/hansard_monthly.json   UK Parliament Hansard API timeline statistics, House of Commons, contribution type Spoken,
                             by month 1909-01 to 2026-10, retrieved 2026 (Open Parliament Licence v3.0). "inp":
                             contributions containing "in <place>" for the 1,661 place terms of Mentioned in the House.
  HP/places.csv              Mentioned in the House (Hotham 2026a, doi:10.5281/zenodo.23761431): place terms, points,
                             nation, modern population, ambiguity flags and precision factors.
  ELEC/contests.csv          Who Won Here? (doi:10.5281/zenodo.23761425): every general election contest 1832 to 2024
                             with date, seat name, point and nation.
  WVH/index.csv              Who gets talked about (Hotham 2026b, doi:10.5281/zenodo.24092583): main sample of 1,425
                             places with 2024 English Wikipedia pageviews, seat-name share 2005 to 2025, local authority.
  BA/event_places.csv        Do by-elections make Parliament listen? (Hotham 2026c, doi:10.5281/zenodo.24094210):
  BA/byelections.csv         by-election to town links with exclusion flags; by-election list (Wikipedia, CC BY-SA 4.0).
  BA/overrides.csv           seat-name aliases and hand decisions used for the links.
  DA/events.csv              Disasters (Hotham 2026d, doi:10.5281/zenodo.24094466): disasters 1909 to 2021 with date,
                             point, type, deaths, search term and inclusion flags.
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PP_RAW", "/home/claude/newdata/raw_new12")
HP = os.environ.get("PP_HP", "/home/claude/src6/hansard-places/data")
ELEC = os.environ.get("PP_ELEC", "/home/claude/src6/elections-since-1832/data")
WVH = os.environ.get("PP_WVH", "/home/claude/studies/wiki-vs-hansard/data")
BA = os.environ.get("PP_BA", "/home/claude/studies/byelection-attention")
DA = os.environ.get("PP_DA", "/home/claude/studies/disaster-attention/data")
GEO = os.environ.get("PP_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("PP_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("PP_SCRATCH", "/home/claude/scratch/places-in-parliament")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "places-in-parliament"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
DOIS = {"hansard-places": "10.5281/zenodo.23761431", "wiki-vs-hansard": "10.5281/zenodo.24092583",
        "byelection-attention": "10.5281/zenodo.24094210", "disaster-attention": "10.5281/zenodo.24094466",
        "who-won-here": "10.5281/zenodo.23761425"}

M0 = 1909                      # month index 0 = January 1909
LAST_MONTH = "2026-10"         # last month in the file
EV_LAST = "2026-09"            # last month used by the event designs (as in byelection-attention)
Y0, Y1 = 1910, 2025            # complete years used for annual and decade analyses
DECADES = list(range(1910, 2030, 10))   # 1910 ... 2020 (2020 = 2020 to 2025, partial)
ERAS = [(1910, 1944, "1910 to 1944"), (1945, 1979, "1945 to 1979"), (1980, 2025, "1980 to 2025")]
PRE, POST = 24, 36
REF = (-24, -13)
BINS = [(-12, -4), (-3, -1), (0, 2), (3, 12), (13, 24), (25, 36)]
BIN_NAMES = ["pre", "runup", "peak", "year1", "year2", "year3"]
K_CONTROLS = 5
NEAR_KM = 25.0
CITY_REF = 30.0                # reference-month mean at or above which a disaster town is too big to register
DIS_KM = 10.0                  # disaster point to nearest Hansard town
CHARING = (51.5074, -0.1278)


def mi(ym):
    y, m = (int(x) for x in ym.split("-")[:2])
    return (y - M0) * 12 + m - 1


def ym(i):
    return f"{M0 + i // 12}-{i % 12 + 1:02d}"


NT = mi(LAST_MONTH) + 1
EVLAST = mi(EV_LAST)


def era_of(y):
    for a, b, n in ERAS:
        if a <= y <= b:
            return n
    return None


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\bsaint\b", "st", s)
    return s


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "x1": return f"{float(v):.1f} times"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    raise ValueError(f)


def pc(b, se):
    from scipy.stats import norm as _n
    return {"b": round(100 * (math.exp(b) - 1), 1), "lo": round(100 * (math.exp(b - 1.96 * se) - 1), 1),
            "hi": round(100 * (math.exp(b + 1.96 * se) - 1), 1), "coef": round(float(b), 4), "se": round(float(se), 4),
            "p": round(float(2 * (1 - _n.cdf(abs(b / se)))), 4) if se > 0 else None}


def est(b, se, digits=3):
    from scipy.stats import norm as _n
    return {"b": round(float(b), digits), "lo": round(float(b - 1.96 * se), digits), "hi": round(float(b + 1.96 * se), digits),
            "se": round(float(se), digits + 1), "p": round(float(2 * (1 - _n.cdf(abs(b / se)))), 4) if se > 0 else None}
