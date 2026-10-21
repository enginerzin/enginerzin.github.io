#!/usr/bin/env python3
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

APIS = [\n    "https://dblp.org/search/publ/api",\n    "https://dblp.dagstuhl.de/search/publ/api",\n    "https://dblp.uni-trier.de/search/publ/api",\n]
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

