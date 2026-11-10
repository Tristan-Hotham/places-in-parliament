# places-in-parliament: working notes

Brief: /home/claude/work/new13/BRIEFS.md section B (+ new12 top, new11 top, new8/new9/new10 shared rules, house brief
/home/claude/newdata/BRIEF.md, GIF brief /home/claude/gifs/BRIEF.md). Format refs: fame-half-life, byelection-attention.
Scratch: /home/claude/scratch/places-in-parliament (delete by exact path at the end).

Title: "Which places get Parliament's attention? A century of the Commons and the map of the UK".
A consolidation paper uniting four published preprints (cite as Hotham 2026a to d):
- hansard-places (Mentioned in the House), doi 10.5281/zenodo.23761431
- wiki-vs-hansard (Who gets talked about), doi 10.5281/zenodo.24092583
- byelection-attention (Do by-elections make Parliament listen?), doi 10.5281/zenodo.24094210
- disaster-attention (disasters: spikes and fades), doi 10.5281/zenodo.24094466

## Inputs (read in place, never modified)
- /home/claude/newdata/raw_new12/hansard_monthly.json: "inp" monthly counts of Commons spoken contributions containing
  "in <place>" for the 1,661 place terms, 1909-01 to 2026-10 (retrieved 2026-11-09). Open Parliament Licence v3.0.
- /home/claude/src6/hansard-places/data/places.csv: place points, nation, population (modern: Census 2021 BUA or
  GeoNames), ambiguity flags (shared, namesake, word) and precision factors.
- /home/claude/src6/elections-since-1832/data/contests.csv: constituency names at every general election (Who Won Here?).
- /home/claude/studies/wiki-vs-hansard/data/index.csv: 1,425 places matched to Wikipedia with 2024 pageviews, seat-name
  share 2005 to 2025, region, deprivation.
- /home/claude/studies/byelection-attention/data/event_places.csv (+ byelections.csv): every by-election to town link
  with the published exclusion flags; main sample (main == 1).
- /home/claude/studies/disaster-attention/data/events.csv: disaster list with dates, points, type, deaths; main == 1.

## Data construction rules (set before any outcome model)
- Monthly series per place exactly as in byelection-attention: spelling variants added to the main term, longer names
  starting with the same words subtracted (prefix subtraction), then multiplied by the precision factor of
  Mentioned in the House for scaled ordinary-word names. Places flagged shared, namesake or word (below 60% precision)
  are left out: 1,597 clean places (number to be confirmed by the code).
- Years: complete calendar years 1910 to 2025 for annual and decade analyses (1909 starts in March). Decades
  1910s to 2010s (complete) plus "2020 to 2025" (six years, reported but flagged as partial). Eras: 1910 to 1944,
  1945 to 1979, 1980 to 2025. Event windows use months up to 2026-09 (as in byelection-attention).
- London = the term "London" (as in Mentioned in the House). Greater London (all clean places within 25 km of
  Charing Cross) used as a sensitivity.
- Seat names at a time: a place is "named in a seat" in a year if it appears (whole-word, same rule as
  byelection-attention, variants included) in a constituency name at the most recent general election on or
  before 1 July of that year (Who Won Here? contests).
- Shocks per place-year: a by-election naming the place (any linked by-election, links with far == 0) in that year
  or the next (years 0 and 1 after polling); a disaster from the disaster-attention list mapped to the place
  (event term if it is a clean Hansard place, else the nearest clean Hansard place within 10 km of the event point)
  in that year or the next.

## Analysis plan (written before running any outcome model)

Overall question: what drives a place's share of parliamentary attention, how concentrated is it, how has it
changed since 1909, and which shocks leave lasting traces? Design: observational and descriptive throughout; no
causal language beyond the event designs, which estimate the change in attention that comes with the whole
episode.

### A. Concentration over time (new)
Unit: decade (and year). Outcome: the distribution of "in" mentions over the clean places.
Measures: London's share; share of the top 10 places; Gini coefficient over all clean places (zeros included);
Hoover (dissimilarity) index between mention shares and population shares (places with a population, modern
figures); Lorenz curves for 1910s, 1950s, 2010s. 95% CIs by bootstrap of months within the decade (1,000 draws).
- H1 concentration falls: Gini, top-10 share and London share lower in the 2010s than in the 1910s (bootstrap CI of
  the difference excludes 0). Against: CI includes 0 or the change is positive.
- H1b not only London: the Gini over places excluding London also falls (same test).
- H2 timing: on annual Gini, a segmented trend with a break at 1945 (OLS, Newey-West SE, 5 lags): pre-1945 slope,
  post-1945 slope, difference. Expect a steeper fall after 1945 ("rise of constituency talk"). Against: slope
  difference CI includes 0.

### B. What drives a place's share (2005 to 2025 cross-section, extends wiki-vs-hansard)
Unit: place (wiki-vs-hansard main sample, N about 1,425). Outcome: "in" mentions 2005 to 2025 (in_05_25).
Model M-B: PPML on blocks: size (log population), public interest (log 2024 pageviews), electoral map (seat-name
share 2005 to 2025), shocks (number of by-elections naming the place polled 2005 to 2023; any main-list disaster
at the place 2005 to 2021), geography (nation indicators, log distance from London). SEs clustered by local
authority. Decomposition: Shapley values of the deviance pseudo-R2 over the five blocks (all 32 subsets); 95% CIs
by bootstrap of places (300 draws).
- H3 size is the largest block; public interest and electoral map each add explanatory power beyond size (Shapley
  share CI above 0); shocks add little in a 21-year cross-section. Against: size not largest; CIs at 0.

### C. Variance decomposition of the century panel (new)
Unit: place-year, clean places, 1910 to 2025 (balanced). Outcome y = log(1 + mentions). Because the panel is
balanced the variance splits exactly into orthogonal parts: common decade, year within decade, place (permanent),
place by decade (slow reshuffling), and the within place-decade remainder; the remainder is then split into a
shock part (by-election and disaster indicators, partialled on place-decade and year effects) and the rest.
Shares of total variance with 95% CIs by bootstrap of places (500 draws).
- H4 the place component is the largest single part (a stable hierarchy); the shock component is small for the
  panel as a whole. Against: decade or place-by-decade larger than place.
- Placebo: shock years moved to random years for the same place (200 permutations): the shock share should fall to
  about 0.

### D. Persistence (new)
- Spearman rank correlation of place mention rates between adjacent decades and between the 1910s and the 2010s
  (places with at least one mention in either decade; bootstrap CI over places).
- Annual AR(1) of the place's log share (log((y+0.5)/total)) with place and year fixed effects, SE clustered by place;
  half-life of a deviation = ln 2 / -ln(rho). By era.
- H5 attention is persistent: adjacent-decade Spearman above 0.7 in every decade; positive AR(1). Against: below 0.7.

### E. Seat names over a century (new: extends the 2005 to 2025 seat premium to 1910 to 2025)
Unit: place-decade (clean places with population), PPML of decade mentions with decade fixed effects:
- E1 cross-section by era: log population, named-in-a-seat share of the decade's years, nation; era-specific
  coefficients; SE clustered by place.
- E2 within place: place and decade fixed effects, seat-name share (identifies gaining and losing a seat name in
  redistributions), with an interaction for post-1945 decades. Lead placebo: next decade's seat-name share added;
  it should be about 0.
- H6 the seat-name premium is positive in every era and larger after 1945; the size elasticity falls after 1945.
  Against: interaction CI includes 0.

### F. Which shocks leave lasting traces (harmonised event study, new)
One common design for both shock types: stacked PPML, months -24 to +36, bins pre (-12 to -4), run-up (-3 to -1),
peak (0 to 2), year 1 (3 to 12), year 2 (13 to 24), year 3 (25 to 36), reference months -24 to -13, unit and
stack-by-month fixed effects, 5 matched controls per treated place (same nation, more than 25 km away, no by-election
or disaster within the window plus 12 months, nearest on log reference-month mentions and log population), SEs
clustered by event. Outcome: "in <town>" for both.
- By-elections: the main sample of byelection-attention (387 town links), re-stacked with the harmonised control
  rule (controls also free of disasters).
- Disasters: disaster-attention main list (86 events) mapped to a town (event term if a clean Hansard place, else
  nearest clean Hansard place within 10 km); excluded if the window falls outside the data, if a by-election names
  the town within the window, or if the town's reference-month mean is 30 or more (a city too big to register a
  local event, as in disaster-attention).
- One joint model with type-specific bins; contrasts disaster minus by-election for peak, year 1 and "lasting"
  (months 13 to 36 pooled). Sub-types (exploratory, small N): by-elections where the seat changed hands vs held;
  disasters with 50 or more deaths vs fewer.
- H7 both shocks raise attention at the peak; the by-election rise lasts longer (months 13 to 36) than the disaster
  rise relative to their peaks. Two-sided contrast. Against: contrast CI includes 0.

### Robustness (pre-specified)
- R1 measurement: no prefix subtraction; no precision scaling; outcome as share of the year's total (A, C, D).
- R2 leave-one-out: without London; without each nation (A, B, C); Greater London as one unit (A).
- R3 sample: places with 50,000 or more people only (A, B, C, E); drop the partial 2020s (A, C, E).
- R4 placebo/falsification: permuted shock years (C); lead seat-name (E); events moved 24 months earlier (F).
- R5 alternative inference: SE clustered by place instead of local authority (B); two-way (event and town) or
  by town (F); 10 controls (F).
- R6 alternative estimators: OLS on log(1 + y) for B, E and F.

What would count against the synthesis: a concentration that did not fall, a seat premium that predates 1945 as much
as it follows it, place effects that explain little of the panel (attention mostly shocks), or shocks whose traces
do not differ.

Design honesty: Hansard "in <place>" counts are a sample of place mentions; the place list is today's UK (Ireland
before 1922 absent; Northern Ireland only), with modern populations; counts are contributions not words; volume of
Hansard changes over time (shares and year effects absorb it); the 2020s are partial.

## Changes after the first run (labelled in the paper)
1. Seat-name link: "Cities of London and Westminster" was matched to the term London (whole-word rule); it names the City of
   London. Alias added. Found because the within-place seat model was driven by London switching to "named" in 1950.
2. Whole-list audit of the 200 most mentioned places: "in Erskine" is "in Erskine May" (the procedure manual), 869
   contributions, not flagged in Mentioned in the House. Excluded (1,596 clean places, not 1,597).
3. Concentration intervals: the bootstrap of months is biased upward for the Gini and Hoover index (repeated months leave
   rare places at zero), so plain percentile intervals missed the estimates. Now percentile intervals shifted by the
   bootstrap bias (bias about 0.003 to 0.006 in the Gini).
4. Placebo P1 in F: first coded over the full -24..+36 window around the false date, which includes the real event at
   +24; corrected to -24..+12 (as in byelection-attention). Only the corrected version is reported.

## Results (numbers from data/results.json)
- A: London 49.1% (1910s) to 18.3% (2010s), 11.2% (2020 to 2025, partial). Gini 0.977 to 0.860 (diff -0.116, CI -0.120 to
  -0.112); without London also falls. ENP 3.9 to 25.7. Places mentioned in a decade 360 to 1,318. Hoover 60.1 to 31.7.
  H1, H1b supported. H2: Gini slope -0.0037/decade before 1945, -0.0127 after (diff CI excludes 0): supported for Gini
  and places mentioned; London's own share fell at a similar pace before and after (diff n.s.).
  2024 and 2025: abrupt rise in places mentioned (about 650 a year to 930): flagged as needing confirmation.
- B (N 1,425): Shapley shares size 39.3%, public interest 37.7% (CIs overlap: "size largest" not clearly supported),
  electoral map 15.0%, geography 4.8%, shocks 3.2%; pseudo-R2 0.933. Seat-name share +110% [80, 144].
- C: place 52.9% [46.2, 58.7], place x decade 18.3%, decade 7.3%, year 0.3%, within 21.2%, shocks 0.05% [0.03, 0.08];
  placebo mean 0.0005%. H4 supported.
- D: adjacent-decade Spearman 0.33 (1910s-20s) to 0.69 (2010s-20s); none >= 0.7, so H5 NOT supported by its criterion.
  AR(1) 0.437, half-life 0.84 years.
- E: size elasticity 1.53 (1910-49), 1.36, 1.18 (falls, CI excl. 0). Between-place seat premium 188%, 137%, 105% (does
  not grow). Within place: 59% before 1945, 164% after, diff 66% [-8, 201]; lead placebo 21% [-0.5, 48]. H6 partly
  supported (size elasticity falls; premium positive throughout); larger premium after 1945 not supported. Within-place
  direction of change not robust (larger after 1945 for 50k+, England, OLS; reversed without London).
- F (366 by-elections, 72 disasters): peak B +289% [191, 419], D +246% [115, 457]; months 3-12 B +87%, D +31%,
  contrast -30% [-50, -3]; months 13-36 B +39% [9, 78], D +10% [-24, 60], contrast -21% [-49, 24] (n.s.). Retained share
  of peak B 14% [3, 26], D 4% [-16, 20]. H7 supported for peaks and year 1, not for the lasting contrast. Disaster
  placebo (dates -24 months) year1 +67% [3, 170]: not clean. Own-town disasters (20): lasting +140% [59, 263], so the
  ranking of lasting traces is not robust. Exploratory: changed-hands by-elections lasting +82%, disasters 50+ deaths +80%.

## References: verification
42 references. New ones checked online in this build (WebSearch/WebFetch, 2026): Israeli 2007 (RePEc record and
abstract: JEI 5(2) 199-212, doi 10.1007/s10888-006-9036-6), Davis and Weinstein 2002 (EconPapers record and abstract,
AER 92(5) 1269-1289), Nickell 1981 (Econometric Society page, 49(6) 1417), Lorenz 1905 (bibliographic record, 9(70)
209-219, doi 10.2307/2276207), Johnston and Pattie 2006 (OUP, library catalogues), Agnew 1987 (Allen and Unwin, catalogue),
Efron and Tibshirani 1993 (Chapman and Hall, catalogues), Bevan and Jennings 2014 and Zittel et al. 2019 (re-checked).
All others were verified in the source studies' builds and their independent reviews (wiki-vs-hansard,
byelection-attention, disaster-attention NOTES) and are cited only for what their titles and abstracts state.
Dropped: Hoover 1936 (record not reached; the index is described without a citation).
