# Which places get Parliament's attention?

A century of the House of Commons and the map of the United Kingdom, 1910 to 2025. A consolidation study that puts four earlier studies of Commons place mentions (Mentioned in the House, Who gets talked about?, Do by-elections make Parliament listen? and the disasters study) on one monthly panel of Hansard counts for 1,596 UK towns and cities, and adds new analyses: concentration over a century, a decomposition of the variance of attention, persistence, seat names since 1910, and one harmonised event study of by-elections and disasters. The analysis plan was written before any outcome model was run (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/places-in-parliament/
Paper: https://doi.org/10.5281/zenodo.24103127
Blog post: https://blog.tristanhotham.com/2026/10/31/places-in-parliament/
Code and data: https://github.com/Tristan-Hotham/places-in-parliament

## Headline results

- Concentration fell: London took 49.1% of Commons "in <place>" mentions in the 1910s and 18.3% in the 2010s (11.2% in the partial 2020s). The Gini coefficient over places fell from 0.977 to 0.86 (difference -0.116 (95% CI -0.120 to -0.112)); the effective number of places rose from 3.9 to 25.7; places mentioned in a decade from 360 to 1,318.
- Faster after 1945: the Gini fell 0.0037 a decade before 1945 and 0.0127 after (difference CI excludes zero), mainly because many more towns entered debate; London's own share fell at a similar pace in both periods.
- Drivers, 2005 to 2025 (1,425 places): Shapley shares of explained variation: size 39.3%, public interest (Wikipedia views) 37.7%, electoral map 15.0%, geography 4.8%, shocks 3.2%. A seat-name place gets 110 (95% CI 80 to 144)% more mentions.
- Variance of yearly mentions, 185,136 place-years: the place itself 52.9 (95% CI 46.2 to 58.7)%, the place's slow change 18.253%, the decade 7.333%, year-to-year 21.172%, by-elections and disasters 0.05 (95% CI 0.03 to 0.08)% (placebo mean 0.0005%).
- Persistence: adjacent-decade rank correlations from 0.326 to 0.694; none reaches the planned 0.7.
- Seat names over a century: places named in a seat were mentioned 188%, 137% and 105% more than same-size places in 1910 to 1949, 1950 to 1979 and 1980 to 2025 (the premium did not grow); the size elasticity fell from 1.534 to 1.178. Within places, the change after 1945 is not robust.
- Shocks in one design (366 by-elections, 72 disasters): peak 289 (95% CI 191 to 419)% and 246 (95% CI 115 to 457)%; months 13 to 36 39 (95% CI 9 to 78)% and 10 (95% CI -24 to 60)%; the lasting contrast -21 (95% CI -49 to 24)% includes zero, and the disaster estimate depends on how disasters are tied to towns.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; every place sized by mentions in a chosen decade (slider and play), coloured by share change, seat name or nation; by-election rings and disaster triangles; layers panel, search, full screen, popups; a place explorer charting any place month by month since 1909 with by-elections and disasters marked. |
| `header.png` | Social card, 1200 x 630. |
| `data/places.csv` | One row per clean place (1,596): point, nation, modern population, precision factor, mentions 1910 to 2025 and by decade, seat-name years, shock flags. |
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

Hotham, T. (2026) Which places get Parliament's attention? A century of the House of Commons and the map of the United Kingdom, 1910 to 2025. Zenodo. https://doi.org/10.5281/zenodo.24103127

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
