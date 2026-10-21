#!/usr/bin/env python3
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://dblp.org/search/publ/api"
QUERY = "author:Engin_Erzin:"
SOURCE = "https://dblp.org/pid/15/2739"
OUT = Path("assets/publications.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; enginerzin.github.io/1.0; +https://enginerzin.github.io/)",
    "Accept": "application/json",
}

def fetch_json():
    params = urllib.parse.urlencode({"q": QUERY, "h": 1000, "format": "json"})
    url = API + "?" + params
    last_error = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                ctype = r.headers.get("Content-Type", "")
                if r.status != 200:
                    raise RuntimeError(f"DBLP returned HTTP {r.status}")
                try:
                    data = json.loads(body.decode("utf-8-sig"))
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    preview = body[:200].decode("utf-8", errors="replace")
                    raise RuntimeError(
                        f"DBLP did not return valid JSON (Content-Type: {ctype!r}). "
                        f"Response starts with: {preview!r}"
                    ) from e
                return data, url
        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Unable to fetch bibliography from DBLP after 3 attempts: {last_error}")

def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def author_name(a):
    return a.get("text", "") if isinstance(a, dict) else str(a)

def category(info):
    t = info.get("type", "")
    if t == "Journal Articles":
        return "Journal Articles"
    if "Conference" in t:
        return "Conference and Workshop Papers"
    if "Informal" in t:
        return "Informal and Other Publications"
    if "Books" in t or "Theses" in t:
        return "Books and Theses"
    return t or "Other"

data, request_url = fetch_json()
hits = data.get("result", {}).get("hits", {}).get("hit", [])
if not hits:
    raise RuntimeError("DBLP returned zero publications; refusing to overwrite the local bibliography.")

pubs = []
for hit in hits:
    info = hit.get("info", {})
    title = str(info.get("title", "")).rstrip(".")
    if not title:
        continue
    authors = [author_name(a) for a in as_list(info.get("authors", {}).get("author"))]
    dblp_url = info.get("url", "")
    key = dblp_url.split("/rec/")[-1] if "/rec/" in dblp_url else ""
    ee = info.get("ee", "")
    if isinstance(ee, list):
        ee = ee[0] if ee else ""
    pubs.append({
        "title": title,
        "authors": authors,
        "venue": info.get("venue", ""),
        "year": str(info.get("year", "")),
        "volume": str(info.get("volume", "")),
        "number": str(info.get("number", "")),
        "pages": str(info.get("pages", "")),
        "category": category(info),
        "url": ee or dblp_url or SOURCE,
        "dblp_key": key,
    })

pubs.sort(
    key=lambda x: (int(x["year"]) if x["year"].isdigit() else 0, x["title"]),
    reverse=True,
)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps(
        {"source": SOURCE, "api_request": request_url, "publications": pubs},
        ensure_ascii=False,
        indent=2,
    ) + "\n",
    encoding="utf-8",
)
print(f"Wrote {len(pubs)} publications to {OUT}")
