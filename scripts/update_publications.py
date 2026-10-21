#!/usr/bin/env python3
import json, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

URL = "https://dblp.org/pid/15/2739.xml"
OUT = Path("assets/publications.json")
HEADERS = {"User-Agent": "enginerzin.github.io bibliography updater (academic homepage)"}

with urllib.request.urlopen(urllib.request.Request(URL, headers=HEADERS), timeout=60) as r:
    root = ET.fromstring(r.read())

category_map = {
    "article": "Journal Articles",
    "inproceedings": "Conference and Workshop Papers",
    "proceedings": "Conference and Workshop Papers",
    "incollection": "Conference and Workshop Papers",
    "book": "Books and Theses",
    "phdthesis": "Books and Theses",
    "mastersthesis": "Books and Theses",
    "www": "Informal and Other Publications",
}

def text(el, name):
    x = el.find(name)
    return "".join(x.itertext()).strip() if x is not None else ""

pubs = []
for r in root.findall("r"):
    if not len(r):
        continue
    e = r[0]
    title = text(e, "title").rstrip(".")
    if not title:
        continue
    key = e.attrib.get("key", "")
    authors = ["".join(a.itertext()).strip() for a in e.findall("author")]
    venue = text(e, "journal") or text(e, "booktitle") or text(e, "publisher") or text(e, "school")
    ee = text(e, "ee")
    url = ee or ("https://dblp.org/rec/" + key if key else "https://dblp.org/pid/15/2739")
    tag = e.tag
    category = category_map.get(tag, "Other")
    # DBLP uses <article publtype="informal"> for CoRR/preprints.
    if e.attrib.get("publtype") == "informal":
        category = "Informal and Other Publications"
    pubs.append({
        "title": title, "authors": authors, "venue": venue,
        "year": text(e, "year"), "volume": text(e, "volume"),
        "number": text(e, "number"), "pages": text(e, "pages"),
        "category": category, "url": url, "dblp_key": key
    })

pubs.sort(key=lambda x: (int(x["year"]) if x["year"].isdigit() else 0, x["title"]), reverse=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"source": URL, "publications": pubs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {len(pubs)} publications to {OUT}")
