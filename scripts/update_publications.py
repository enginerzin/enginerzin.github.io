#!/usr/bin/env python3
"""Import a manually downloaded canonical DBLP person XML export; never fetch."""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET

SOURCE = "https://dblp.org/pid/15/2739"
ROOT = Path(__file__).resolve().parents[1]


def convert(raw, retrieved):
    root = ET.fromstring(raw)
    if root.tag != "dblpperson" or root.get("pid") != "15/2739":
        raise ValueError("Expected the full dblpperson export for PID 15/2739")
    wrappers = root.findall("r")
    if not wrappers or int(root.attrib["n"]) != len(wrappers):
        raise ValueError("Export record count is missing, empty, or inconsistent")
    pubs = []
    seen = set()
    def text(node, tag):
        item = node.find(tag)
        return "" if item is None else "".join(item.itertext()).strip()
    for wrapper in wrappers:
        if len(wrapper) != 1:
            raise ValueError("Malformed publication wrapper")
        record = wrapper[0]
        key = record.get("key", "")
        title, year = text(record, "title"), text(record, "year")
        authors = ["".join(a.itertext()).strip() for a in record.findall("author")]
        if not key or key in seen or not title or not year.isdigit() or not authors:
            raise ValueError(f"Invalid or duplicate publication: {key}")
        seen.add(key)
        categories = {"article": "Journal Articles", "inproceedings": "Conference and Workshop Papers",
                      "book": "Books and Theses", "phdthesis": "Books and Theses", "mastersthesis": "Books and Theses"}
        category = categories.get(record.tag, "Other")
        if record.get("publtype") == "informal" or key.startswith("journals/corr/"):
            category = "Informal and Other Publications"
        pubs.append(dict(title=title, authors=authors, venue=text(record, "journal") or text(record, "booktitle"),
                         year=year, volume=text(record, "volume"), number=text(record, "number"),
                         pages=text(record, "pages"), category=category,
                         url=text(record, "ee") or "https://dblp.org/rec/" + key, dblp_key=key))
    pubs.sort(key=lambda p: (-int(p["year"]), p["title"]))
    return dict(source=SOURCE, retrieved_on=retrieved, status="verified-export", source_record_count=len(wrappers),
                source_sha256=hashlib.sha256(raw).hexdigest(), publications=pubs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", type=Path)
    parser.add_argument("--retrieved-on", required=True, type=lambda s: date.fromisoformat(s).isoformat())
    args = parser.parse_args()
    raw = args.xml.read_bytes()
    data = convert(raw, args.retrieved_on)
    # Retain the exact verified input for reproducibility and review.
    archive = ROOT / "data/dblp-15-2739.xml"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(raw)
    out = ROOT / "assets/publications.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(data['publications'])} publications to {out}")


if __name__ == "__main__":
    main()
