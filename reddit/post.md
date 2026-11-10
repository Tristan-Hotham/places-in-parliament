**Title:** [OC] London took 49% of the House of Commons' mentions of UK towns in the 1910s and 18% in the 2010s. A century of Hansard, 1,596 places.

**Body:**

I counted every House of Commons speech since 1909 that says "in" plus the name of one of 1,596 UK towns and cities, month by month, and brought together four earlier studies of the same counts.

- In the 1910s London alone took 49% of these mentions; in the 2010s, 18%. The pattern went from being like talking about 4 places to about 26.
- The spread sped up after 1945, mostly because far more towns came into debate.
- But a place's standing is mostly about the place: 53% of the variation in yearly mentions is a fixed feature of the place, and by-elections and disasters together just 0.05%.
- Today, size and public interest (Wikipedia views) explain about the same share of who gets mentioned; a place with a seat named after it gets about 110% more mentions than a similar place without one.
- By-elections and disasters both make a town's name jump (3.9x and 3.5x matched towns around the event).

Interactive map, with a search to chart any place month by month since 1909: https://maps.tristanhotham.com/places-in-parliament/

**Source comment:**

Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); by-election and disaster lists from Wikipedia (CC BY-SA 4.0); Wikipedia pageviews and Wikidata (CC0). Method: shares and Gini by decade with bootstrap intervals, an exact variance decomposition of the place-year panel, Poisson models, and a matched event study; plan written before the analysis. Tools: Python (pandas, statsmodels, pyfixest, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/places-in-parliament
