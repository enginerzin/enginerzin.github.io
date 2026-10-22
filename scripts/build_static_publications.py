#!/usr/bin/env python3
import json, urllib.parse, urllib.request
from pathlib import Path
ORCID="0000-0002-2715-2368"
HEADERS={"User-Agent":"enginerzin.github.io static bibliography builder"}
def get(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
author=get("https://api.openalex.org/authors/orcid:"+ORCID)
aid=author["id"].rsplit("/",1)[-1]
params=urllib.parse.urlencode({"filter":f"author.id:{aid}","per-page":100})
base="https://api.openalex.org/works?"+params
page=1; works=[]
while True:
    data=get(base+"&page="+str(page)); works.extend(data["results"])
    if len(works)>=data["meta"]["count"]: break
    page+=1
def cat(t):
    if t in {"article","review"}: return "Journal Articles"
    if t in {"proceedings-article","proceedings"}: return "Conference and Workshop Papers"
    if t in {"book","book-chapter","dissertation","monograph"}: return "Books and Theses"
    return "Informal and Other Publications"
pubs=[]; seen=set()
for w in works:
    title=(w.get("title") or "").strip(); year=str(w.get("publication_year") or "")
    if not title or not year: continue
    key=((w.get("doi") or "").lower(),title.lower(),year)
    if key in seen: continue
    seen.add(key)
    authors=[a.get("author",{}).get("display_name","") for a in w.get("authorships",[]) if a.get("author",{}).get("display_name")]
    source=((w.get("primary_location") or {}).get("source") or {})
    b=w.get("biblio") or {}; doi=w.get("doi") or ""
    first=b.get("first_page") or ""; last=b.get("last_page") or ""
    pages=first if first==last else "-".join(x for x in [first,last] if x)
    pubs.append({"title":title,"authors":authors,"venue":source.get("display_name") or "","year":year,"volume":b.get("volume") or "","number":b.get("issue") or "","pages":pages,"category":cat(w.get("type") or ""),"url":doi or w.get("id") or "https://dblp.org/pid/15/2739","openalex_id":w.get("id") or ""})
pubs.sort(key=lambda x:(int(x["year"]),x["title"]),reverse=True)
out={"source":"Static bibliography; canonical DBLP: https://dblp.org/pid/15/2739; seeded from OpenAlex ORCID 0000-0002-2715-2368","publications":pubs}
Path("assets").mkdir(exist_ok=True)
Path("assets/publications.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Wrote {len(pubs)} publications for {author['display_name']} ({aid})")
