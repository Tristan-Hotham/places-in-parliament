"""Step 8: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo). 10.5281/zenodo.24103127, https://doi.org/10.5281/zenodo.24103127 and
https://blog.tristanhotham.com/2026/10/31/places-in-parliament/ are left for the publisher to fill."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json"); H = R["H"]
NAME = "Hotham_Places_in_Parliament"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Which places get Parliament's attention?",
        "slug": "places-in-parliament",
        "excerpt": f"A century of Hansard and {R['data']['n_clean']:,} UK towns. London took {H['london_1910s']:.0f}% of the Commons' town mentions in the 1910s and {H['london_2010s']:.0f}% in the 2010s, yet where a place stands is still mostly about the place itself.",
        "seo_description": f"A century of House of Commons mentions of {R['data']['n_clean']:,} UK towns: how attention spread out from London, and what decides a place's share.",
        "tags": ["maps", "data visualisation", "Parliament", "Hansard", "representation", "UK politics", "by-elections", "London"],
        "header_alt": "Title card on cream paper reading 'Which places get Parliament's attention?' beside a map of UK towns coloured red where their share of Commons mentions grew and blue where it shrank."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("places.csv", "place_years.csv", "annual.csv", "concentration.csv", "drivers_shapley.csv", "byelection_links.csv", "disaster_towns.csv",
               "shock_events.csv", "event_study.csv", "models.csv", "results.json", "hansard_monthly_clean.csv.gz"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\\end\{quote\}", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$-$", "-").replace("$", "").replace("``", "\"").replace("''", "\"")
zmeta = {"title": "Which Places Get Parliament's Attention? A Century of the House of Commons and the Map of the United Kingdom, 1910 to 2025",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/places-in-parliament/}}.</p><p>Sources: Hansard via the UK Parliament Hansard API (Open Parliament Licence v3.0); the author's earlier preprints Mentioned in the House (doi:10.5281/zenodo.23761431), Who gets talked about? (doi:10.5281/zenodo.24092583), Do by-elections make Parliament listen? (doi:10.5281/zenodo.24094210) and the disasters study (doi:10.5281/zenodo.24094466); Who Won Here? (doi:10.5281/zenodo.23761425); English Wikipedia lists (CC BY-SA 4.0); Wikipedia pageviews and Wikidata (CC0). Text, figures and data CC BY 4.0 (fields from Wikipedia lists CC BY-SA 4.0); code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["parliamentary attention", "geographic representation", "House of Commons", "Hansard", "concentration", "constituency representation", "by-elections", "disasters", "United Kingdom"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}]
         + [{"identifier": DOIS[k], "relation": "isDerivedFrom", "resource_type": "publication"} for k in ("hansard-places", "wiki-vs-hansard", "byelection-attention", "disaster-attention", "who-won-here")],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip; abstract words", len(ab.split()))
