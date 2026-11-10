"""Step 9: README.md and reddit/post.md from data/results.json. 10.5281/zenodo.24103127, https://doi.org/10.5281/zenodo.24103127 and https://blog.tristanhotham.com/2026/10/31/places-in-parliament/ are left for the
publisher to fill."""
from common import *

R = jload(f"{DATA}/results.json"); H = R["H"]; F1 = R["F"]["F1"]; dc = R["decomp"]; d = R["drivers"]
ci = lambda x, n=0: f"{x['b']:.{n}f} (95% CI {x['lo']:.{n}f} to {x['hi']:.{n}f})"
readme = f"""# Which places get Parliament's attention?

A century of the House of Commons and the map of the United Kingdom, 1910 to 2025. A consolidation study that puts four earlier studies of Commons place mentions (Mentioned in the House, Who gets talked about?, Do by-elections make Parliament listen? and the disasters study) on one monthly panel of Hansard counts for {R['data']['n_clean']:,} UK towns and cities, and adds new analyses: concentration over a century, a decomposition of the variance of attention, persistence, seat names since 1910, and one harmonised event study of by-elections and disasters. The analysis plan was written before any outcome model was run (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/{SLUG}/
Paper: {{https://doi.org/10.5281/zenodo.24103127}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/places-in-parliament/}}
Code and data: {REPO}

## Headline results

- Concentration fell: London took {H['london_1910s']}% of Commons "in <place>" mentions in the 1910s and {H['london_2010s']}% in the 2010s ({H['london_2020s']}% in the partial 2020s). The Gini coefficient over places fell from {H['gini_1910s']} to {H['gini_2010s']} (difference {ci(R['conc_diff_2010_1910']['gini'], 3)}); the effective number of places rose from {H['enp_1910s']} to {H['enp_2010s']}; places mentioned in a decade from {H['places_1910s']:,} to {H['places_2010s']:,}.
- Faster after 1945: the Gini fell {H['gini_slope_pre']} a decade before 1945 and {H['gini_slope_post']} after (difference CI excludes zero), mainly because many more towns entered debate; London's own share fell at a similar pace in both periods.
- Drivers, 2005 to 2025 ({d['n']:,} places): Shapley shares of explained variation: size {H['shap_size']}%, public interest (Wikipedia views) {H['shap_views']}%, electoral map {H['shap_seat']}%, geography {H['shap_geo']}%, shocks {H['shap_shocks']}%. A seat-name place gets {ci(d['seat_pc'])}% more mentions.
- Variance of yearly mentions, {dc['n_rows']:,} place-years: the place itself {ci(dc['place'], 1)}%, the place's slow change {dc['place_decade']['b']}%, the decade {dc['decade']['b']}%, year-to-year {dc['within']['b']}%, by-elections and disasters {ci(dc['shock'], 2)}% (placebo mean {dc['placebo_shock']['mean']}%).
- Persistence: adjacent-decade rank correlations from {H['sp_1910_1920']} to {H['sp_2010_2020']}; none reaches the planned 0.7.
- Seat names over a century: places named in a seat were mentioned {R['E1']['seat_0']['b']:.0f}%, {R['E1']['seat_1']['b']:.0f}% and {R['E1']['seat_2']['b']:.0f}% more than same-size places in 1910 to 1949, 1950 to 1979 and 1980 to 2025 (the premium did not grow); the size elasticity fell from {R['E1']['lpop_0']['b']} to {R['E1']['lpop_2']['b']}. Within places, the change after 1945 is not robust.
- Shocks in one design ({F1['n']['events_B']} by-elections, {F1['n']['events_D']} disasters): peak {ci(F1['peak__B'])}% and {ci(F1['peak__D'])}%; months 13 to 36 {ci(F1['lasting__B'])}% and {ci(F1['lasting__D'])}%; the lasting contrast {ci(F1['contrast']['lasting'])}% includes zero, and the disaster estimate depends on how disasters are tied to towns.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; every place sized by mentions in a chosen decade (slider and play), coloured by share change, seat name or nation; by-election rings and disaster triangles; layers panel, search, full screen, popups; a place explorer charting any place month by month since 1909 with by-elections and disasters marked. |
| `header.png` | Social card, 1200 x 630. |
| `data/places.csv` | One row per clean place ({R['data']['n_clean']:,}): point, nation, modern population, precision factor, mentions 1910 to 2025 and by decade, seat-name years, shock flags. |
| `data/place_years.csv` | Place-years with any mention, seat name or shock: mentions, seats named, shock indicators. |
| `data/hansard_monthly_clean.csv.gz` | Monthly "in <place>" counts for every clean place after variants, prefix subtraction and precision scaling (non-zero months). |
| `data/annual.csv`, `data/concentration.csv` | Annual and decade concentration measures (decades with bias-corrected bootstrap intervals). |
| `data/drivers_shapley.csv` | Shapley decomposition of the 2005 to 2025 model. |
| `data/byelection_links.csv`, `data/disaster_towns.csv`, `data/shock_events.csv` | By-election to town links; every disaster with its town and distance; disaster exclusion flags for the harmonised design. |
| `data/event_study.csv`, `data/models.csv` | Monthly event-study estimates by shock type; every coefficient of every model. |
| `data/results.json`, `data/site.json`, `data/monthly.json` | Every number quoted anywhere; page data. |
| `code/` | Scripts in order, templates, `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the post text and a GIF. |

## Method in brief

- Counts: House of Commons spoken contributions per month containing "in" plus the place name (UK Parliament Hansard API timeline statistics), built as in the by-election study (variants, prefix subtraction) with the precision factors of Mentioned in the House; ambiguous names excluded, plus "Erskine" ("in Erskine May").
- Concentration: London share, top ten share, Gini, effective number of places and the dissimilarity with population by decade, bias-corrected bootstrap over months; segmented annual trends with a 1945 break (Newey and West errors).
- Drivers: PPML of 2005 to 2025 mentions on size, public interest, electoral map, shocks and geography, Shapley split of the deviance pseudo-R2, bootstrap over places.
- Variance decomposition: exact orthogonal split of log(1 + yearly mentions) on the balanced place-year panel; shock share from by-election and disaster indicators; permutation placebo.
- Seat names: whole-word matches of place names in constituency names at every general election (Who Won Here?); PPML of decade mentions between and within places.
- Shocks: one stacked PPML design for by-elections and disasters (five matched towns each, town and stack-by-month fixed effects, errors clustered by event).
- Limits: "in <place>" is a sample of mentions; today's place list and modern populations; the 2020s are partial with a sharp 2024 to 2025 rise in places mentioned; observational design; disasters tied to the nearest Hansard town.

## Sources and licences

- Hansard, House of Commons, via the UK Parliament Hansard API. Contains Parliamentary information licensed under the Open Parliament Licence v3.0.
- Hotham (2026) Mentioned in the House, doi:10.5281/zenodo.23761431; Who gets talked about?, doi:10.5281/zenodo.24092583; Do by-elections make Parliament listen?, doi:10.5281/zenodo.24094210; disasters study, doi:10.5281/zenodo.24094466; Who Won Here?, doi:10.5281/zenodo.23761425.
- English Wikipedia lists of UK by-elections and disasters (CC BY-SA 4.0); Wikipedia pageviews and Wikidata (CC0).
- Base map: OpenFreeMap Positron (OpenStreetMap contributors, ODbL); Natural Earth and ONS outlines in the figures.

Licence: text, figures and data CC BY 4.0 (Wikipedia-derived fields CC BY-SA 4.0); code MIT (see LICENSE).

## How to rerun

```
python3 code/01_data.py        # monthly series, seat names, shocks
python3 code/02_models.py      # A to E: concentration, drivers, decomposition, persistence, seat names
python3 code/03_events.py      # F: harmonised event study
python3 code/04_results.py     # data/results.json, data/models.csv
python3 code/05_figures.py     # figures and header.png
python3 code/06_build_site.py  # page data and index.html
DOI=10.5281/zenodo.N python3 code/07_paper.py   # paper (DOI optional)
python3 reddit/collage.py
python3 code/09_readme.py      # README.md and reddit/post.md
python3 code/08_release.py     # blog post and Zenodo files
node code/qa.js                # screenshots (needs Playwright)
```

Input paths are set in `code/common.py`. Python 3 with numpy, pandas, statsmodels, pyfixest, shapely, pyproj and matplotlib; xelatex for the paper.

## Citation

Hotham, T. (2026) Which places get Parliament's attention? A century of the House of Commons and the map of the United Kingdom, 1910 to 2025. Zenodo. {{https://doi.org/10.5281/zenodo.24103127}}

{AI}
"""
post = f"""**Title:** [OC] London took {H['london_1910s']:.0f}% of the House of Commons' mentions of UK towns in the 1910s and {H['london_2010s']:.0f}% in the 2010s. A century of Hansard, {R['data']['n_clean']:,} places.

**Body:**

I counted every House of Commons speech since 1909 that says "in" plus the name of one of {R['data']['n_clean']:,} UK towns and cities, month by month, and brought together four earlier studies of the same counts.

- In the 1910s London alone took {H['london_1910s']:.0f}% of these mentions; in the 2010s, {H['london_2010s']:.0f}%. The pattern went from being like talking about {H['enp_1910s']:.0f} places to about {H['enp_2010s']:.0f}.
- The spread sped up after 1945, mostly because far more towns came into debate.
- But a place's standing is mostly about the place: {H['dec_place']:.0f}% of the variation in yearly mentions is a fixed feature of the place, and by-elections and disasters together just {H['dec_shock']:.2f}%.
- Today, size and public interest (Wikipedia views) explain about the same share of who gets mentioned; a place with a seat named after it gets about {d['seat_pc']['b']:.0f}% more mentions than a similar place without one.
- By-elections and disasters both make a town's name jump ({H['F_x_peak_B']:.1f}x and {H['F_x_peak_D']:.1f}x matched towns around the event).

Interactive map, with a search to chart any place month by month since 1909: https://maps.tristanhotham.com/{SLUG}/

**Source comment:**

Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); by-election and disaster lists from Wikipedia (CC BY-SA 4.0); Wikipedia pageviews and Wikidata (CC0). Method: shares and Gini by decade with bootstrap intervals, an exact variance decomposition of the place-year panel, Poisson models, and a matched event study; plan written before the analysis. Tools: Python (pandas, statsmodels, pyfixest, matplotlib), MapLibre. Paper and code: {REPO}
"""
for s in (readme, post):
    for bad in ("—", "–", "DSIT", "DCMS", "pre-registered"):
        assert bad not in s, bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words; post", len(post.split()))
