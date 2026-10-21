#!/usr/bin/env python3
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

APIS = [
    "https://dblp.org/search/publ/api",
    "https://dblp.dagstuhl.de/search/publ/api",
    "https://dblp.uni-trier.de/search/publ/api",
]
QUERY = "author:Engin_Erzin:"
SOURCE = "https://dblp.org/pid/15/2739"
OUT = Path("assets/publications.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; enginerzin.github.io/1.0; +https://enginerzin.github.io/)",
    "Accept": "application/json",
}

def fetch_json():
    params = urllib.parse.urlencode({"q": QUERY, "h": 1000, "format": "json"})
    errors = []
    for api in APIS:
        url = api + "?" + params
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read()
                    status = r.status
                    ctype = r.headers.get("Content-Type", "")
                    # DBLP may answer 202 while still returning a usable API body.
                    if status not in (200, 202):
                        raise RuntimeError(f"HTTP {status}")
                    try:
                        data = json.loads(body.decode("utf-8-sig"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as e:
                        preview = body[:200].decode("utf-8", errors="replace")
                        raise RuntimeError(
                            f"HTTP {status}, invalid JSON (Content-Type: {ctype!r}); "
                            f"response starts with {preview!r}"
                        ) from e
                    hits = data.get("result", {}).get("hits", {}).get("hit", [])
                    if not hits:
                        raise RuntimeError(f"HTTP {status}, valid JSON but zero hits")
                    print(f"Fetched bibliography from {api} (HTTP {status})")
                    return data, url
            except Exception as e:
                errors.append(f"{api} attempt {attempt + 1}: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
    raise RuntimeError(
        "Unable to fetch bibliography from any official DBLP endpoint:\n  - "
        + "\n  - ".join(errors)
    )

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

if not pubs:
    raise RuntimeError("No usable DBLP publication records were produced.")

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
